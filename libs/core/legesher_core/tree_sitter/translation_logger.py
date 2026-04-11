"""Translation data logger for future model training.

Logs structured translation data (identifier pairs, text pairs, validation
failures, backend metadata) in JSONL format for training/fine-tuning
code translation models.

All logging is append-mode and crash-safe — partial batch runs produce
usable output.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class TranslationLogger:
    """Logs translation data for future model training.

    Writes JSONL files organized by batch run timestamp:

        .legesher/translation_logs/
        ├── 2026-04-01T12-00-00/
        │   ├── metadata.json
        │   ├── identifier_pairs.jsonl
        │   ├── text_pairs.jsonl
        │   └── validation_failures.jsonl

    Example:
        >>> log = TranslationLogger(Path(".legesher/translation_logs"))
        >>> log.start_batch("anthropic", "claude-sonnet-4-5-20250514", "en", "es")
        >>> log.log_identifier_pair(
        ...     source="calculate_tax",
        ...     target="calcular_impuesto",
        ...     role="function_name",
        ...     context={"surrounding_code": "def calculate_tax(income):"},
        ...     naming_convention="snake_case",
        ... )
        >>> log.finish_batch()
    """

    def __init__(self, base_dir: Path):
        """Initialize the logger.

        Args:
            base_dir: Base directory for translation logs
                     (e.g., .legesher/translation_logs)
        """
        self.base_dir = base_dir
        self._batch_dir: Path | None = None
        self._batch_metadata: dict[str, Any] = {}
        self._identifier_file = None
        self._text_file = None
        self._failure_file = None
        self._counts = {
            "identifiers": 0,
            "comments": 0,
            "docstrings": 0,
            "strings": 0,
            "failures": 0,
            "files": 0,
        }

    def start_batch(
        self,
        backend: str,
        model: str,
        source_lang: str,
        target_lang: str,
    ) -> Path:
        """Start a new batch logging session.

        Creates a timestamped directory and opens log files.

        Args:
            backend: Backend name (e.g., "anthropic", "cohere-aya")
            model: Model identifier
            source_lang: Source language code
            target_lang: Target language code

        Returns:
            Path to the batch directory
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")
        self._batch_dir = self.base_dir / timestamp
        self._batch_dir.mkdir(parents=True, exist_ok=True)

        self._batch_metadata = {
            "backend": backend,
            "model": model,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "finished_at": None,
        }

        self._counts = {
            "identifiers": 0,
            "comments": 0,
            "docstrings": 0,
            "strings": 0,
            "failures": 0,
            "files": 0,
        }

        # Open files in append mode for crash safety
        # Wrap in try/except to close any handles on partial failure
        try:
            self._identifier_file = open(
                self._batch_dir / "identifier_pairs.jsonl", "a", encoding="utf-8"
            )
            self._text_file = open(
                self._batch_dir / "text_pairs.jsonl", "a", encoding="utf-8"
            )
            self._failure_file = open(
                self._batch_dir / "validation_failures.jsonl", "a", encoding="utf-8"
            )
        except Exception:
            for f in (self._identifier_file, self._text_file, self._failure_file):
                if f is not None:
                    f.close()
            self._identifier_file = None
            self._text_file = None
            self._failure_file = None
            raise

        logger.info("Started translation logging batch at %s", self._batch_dir)
        return self._batch_dir

    def log_identifier_pair(
        self,
        source: str,
        target: str,
        target_lang: str,
        role: str,
        naming_convention: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Log a translated identifier pair."""
        if self._identifier_file is None:
            return

        record = {
            "source": source,
            "target": target,
            "lang": target_lang,
            "role": role,
            "naming_convention": naming_convention,
            "context": context or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._identifier_file.write(json.dumps(record, ensure_ascii=False) + "\n")
        self._identifier_file.flush()
        self._counts["identifiers"] += 1

    def log_text_pair(
        self,
        source: str,
        target: str,
        target_lang: str,
        kind: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Log a translated text pair (comment, docstring, or string)."""
        if self._text_file is None:
            return

        record = {
            "source": source,
            "target": target,
            "lang": target_lang,
            "kind": kind,
            "context": context or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._text_file.write(json.dumps(record, ensure_ascii=False) + "\n")
        self._text_file.flush()
        self._counts[kind + "s"] = self._counts.get(kind + "s", 0) + 1

    def log_validation_failure(
        self,
        identifier: str,
        first_attempt: str,
        failure_reason: str,
        retry_result: str | None = None,
        retry_valid: bool | None = None,
    ) -> None:
        """Log a validation failure for training data."""
        if self._failure_file is None:
            return

        record = {
            "identifier": identifier,
            "first_attempt": first_attempt,
            "failure_reason": failure_reason,
            "retry_result": retry_result,
            "retry_valid": retry_valid,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._failure_file.write(json.dumps(record, ensure_ascii=False) + "\n")
        self._failure_file.flush()
        self._counts["failures"] += 1

    def log_file_completed(self, _file_path: str) -> None:
        """Record that a file has been translated."""
        self._counts["files"] += 1

    def finish_batch(self) -> dict[str, Any]:
        """Finish the batch and write metadata.

        Returns:
            Batch summary dict with counts and timing
        """
        self._batch_metadata["finished_at"] = datetime.now(timezone.utc).isoformat()
        self._batch_metadata["counts"] = self._counts.copy()

        # Close log files
        for f in (self._identifier_file, self._text_file, self._failure_file):
            if f is not None:
                f.close()
        self._identifier_file = None
        self._text_file = None
        self._failure_file = None

        # Write metadata
        if self._batch_dir is not None:
            metadata_path = self._batch_dir / "metadata.json"
            metadata_path.write_text(
                json.dumps(self._batch_metadata, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            logger.info(
                "Finished translation batch: %d identifiers, %d texts, %d failures",
                self._counts["identifiers"],
                sum(self._counts[k] for k in ("comments", "docstrings", "strings")),
                self._counts["failures"],
            )

        return self._batch_metadata

    def __enter__(self):
        return self

    def __exit__(self, _exc_type, _exc_val, _exc_tb):
        if self._identifier_file is not None:
            self.finish_batch()
        return False
