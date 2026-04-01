"""Tests for TranslationLogger — structured logging for training data collection.

Tests batch lifecycle (start/finish), JSONL writing for identifier pairs,
text pairs, and validation failures, metadata output, context manager usage,
count tracking, and crash-safe flush behavior.
"""

import json

import pytest

from legesher_core.tree_sitter.translation_logger import TranslationLogger

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def logger(tmp_path):
    """TranslationLogger pointed at a temporary directory."""
    return TranslationLogger(base_dir=tmp_path / "logs")


@pytest.fixture
def started_logger(logger):
    """Logger with an active batch."""
    logger.start_batch(
        backend="mock",
        model="mock-v1",
        source_lang="en",
        target_lang="es",
    )
    return logger


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_jsonl(path):
    """Read all lines from a JSONL file."""
    lines = path.read_text(encoding="utf-8").strip().split("\n")
    return [json.loads(line) for line in lines if line.strip()]


# ===========================================================================
# start_batch
# ===========================================================================


class TestStartBatch:
    """Tests for batch initialization."""

    def test_creates_batch_directory(self, logger):
        batch_dir = logger.start_batch("mock", "mock-v1", "en", "es")
        assert batch_dir.exists()
        assert batch_dir.is_dir()

    def test_creates_log_files(self, logger):
        batch_dir = logger.start_batch("mock", "mock-v1", "en", "es")
        assert (batch_dir / "identifier_pairs.jsonl").exists()
        assert (batch_dir / "text_pairs.jsonl").exists()
        assert (batch_dir / "validation_failures.jsonl").exists()

    def test_returns_batch_directory_path(self, logger):
        batch_dir = logger.start_batch("mock", "mock-v1", "en", "es")
        assert "logs" in str(batch_dir)


# ===========================================================================
# log_identifier_pair
# ===========================================================================


class TestLogIdentifierPair:
    """Tests for identifier pair logging."""

    def test_writes_jsonl_record(self, started_logger):
        started_logger.log_identifier_pair(
            source="calculate_tax",
            target="calcular_impuesto",
            target_lang="es",
            role="function_name",
            naming_convention="snake_case",
            context={"surrounding_code": "def calculate_tax(income):"},
        )
        # Find the identifier_pairs.jsonl file
        batch_dir = started_logger._batch_dir
        records = _read_jsonl(batch_dir / "identifier_pairs.jsonl")
        assert len(records) == 1
        assert records[0]["source"] == "calculate_tax"
        assert records[0]["target"] == "calcular_impuesto"
        assert records[0]["lang"] == "es"
        assert records[0]["role"] == "function_name"
        assert records[0]["naming_convention"] == "snake_case"
        assert "timestamp" in records[0]

    def test_multiple_records(self, started_logger):
        for i in range(3):
            started_logger.log_identifier_pair(
                source=f"var_{i}",
                target=f"variable_{i}",
                target_lang="es",
                role="variable",
                naming_convention="snake_case",
            )
        batch_dir = started_logger._batch_dir
        records = _read_jsonl(batch_dir / "identifier_pairs.jsonl")
        assert len(records) == 3

    def test_no_op_before_start_batch(self, logger):
        # Should not raise, just silently no-op
        logger.log_identifier_pair(
            source="x",
            target="y",
            target_lang="es",
            role="variable",
            naming_convention="snake_case",
        )


# ===========================================================================
# log_text_pair
# ===========================================================================


class TestLogTextPair:
    """Tests for text pair (comment/docstring/string) logging."""

    def test_writes_jsonl_record(self, started_logger):
        started_logger.log_text_pair(
            source="This is a comment",
            target="Este es un comentario",
            target_lang="es",
            kind="comment",
            context={"line": 5},
        )
        batch_dir = started_logger._batch_dir
        records = _read_jsonl(batch_dir / "text_pairs.jsonl")
        assert len(records) == 1
        assert records[0]["source"] == "This is a comment"
        assert records[0]["target"] == "Este es un comentario"
        assert records[0]["kind"] == "comment"
        assert "timestamp" in records[0]

    def test_no_op_before_start_batch(self, logger):
        logger.log_text_pair(
            source="x",
            target="y",
            target_lang="es",
            kind="comment",
        )


# ===========================================================================
# log_validation_failure
# ===========================================================================


class TestLogValidationFailure:
    """Tests for validation failure logging."""

    def test_writes_jsonl_record(self, started_logger):
        started_logger.log_validation_failure(
            identifier="calculate_tax",
            first_attempt="calcular impuesto",
            failure_reason="contains spaces",
            retry_result="calcular_impuesto",
            retry_valid=True,
        )
        batch_dir = started_logger._batch_dir
        records = _read_jsonl(batch_dir / "validation_failures.jsonl")
        assert len(records) == 1
        assert records[0]["identifier"] == "calculate_tax"
        assert records[0]["first_attempt"] == "calcular impuesto"
        assert records[0]["failure_reason"] == "contains spaces"
        assert records[0]["retry_result"] == "calcular_impuesto"
        assert records[0]["retry_valid"] is True

    def test_no_op_before_start_batch(self, logger):
        logger.log_validation_failure(
            identifier="x",
            first_attempt="y",
            failure_reason="test",
        )


# ===========================================================================
# finish_batch
# ===========================================================================


class TestFinishBatch:
    """Tests for batch completion and metadata writing."""

    def test_writes_metadata_json(self, started_logger):
        started_logger.log_identifier_pair(
            source="x",
            target="y",
            target_lang="es",
            role="variable",
            naming_convention="snake_case",
        )
        started_logger.finish_batch()

        batch_dir = started_logger._batch_dir
        metadata_path = batch_dir / "metadata.json"
        assert metadata_path.exists()

        data = json.loads(metadata_path.read_text(encoding="utf-8"))
        assert data["backend"] == "mock"
        assert data["model"] == "mock-v1"
        assert data["source_lang"] == "en"
        assert data["target_lang"] == "es"
        assert data["started_at"] is not None
        assert data["finished_at"] is not None
        assert "counts" in data

    def test_returns_metadata_dict(self, started_logger):
        result = started_logger.finish_batch()
        assert isinstance(result, dict)
        assert "backend" in result
        assert "counts" in result

    def test_closes_files(self, started_logger):
        started_logger.finish_batch()
        # After finish, the file handles should be None
        assert started_logger._identifier_file is None
        assert started_logger._text_file is None
        assert started_logger._failure_file is None


# ===========================================================================
# Count tracking
# ===========================================================================


class TestCounts:
    """Tests that counts are tracked correctly."""

    def test_identifier_count(self, started_logger):
        for _ in range(5):
            started_logger.log_identifier_pair(
                source="x",
                target="y",
                target_lang="es",
                role="variable",
                naming_convention="snake_case",
            )
        result = started_logger.finish_batch()
        assert result["counts"]["identifiers"] == 5

    def test_failure_count(self, started_logger):
        for _ in range(3):
            started_logger.log_validation_failure(
                identifier="x",
                first_attempt="y",
                failure_reason="test",
            )
        result = started_logger.finish_batch()
        assert result["counts"]["failures"] == 3

    def test_text_counts_by_kind(self, started_logger):
        started_logger.log_text_pair(
            source="a",
            target="b",
            target_lang="es",
            kind="comment",
        )
        started_logger.log_text_pair(
            source="c",
            target="d",
            target_lang="es",
            kind="comment",
        )
        started_logger.log_text_pair(
            source="e",
            target="f",
            target_lang="es",
            kind="docstring",
        )
        result = started_logger.finish_batch()
        assert result["counts"]["comments"] == 2
        assert result["counts"]["docstrings"] == 1

    def test_file_count(self, started_logger):
        started_logger.log_file_completed("file1.py")
        started_logger.log_file_completed("file2.py")
        result = started_logger.finish_batch()
        assert result["counts"]["files"] == 2


# ===========================================================================
# Context manager
# ===========================================================================


class TestContextManager:
    """Tests for __enter__ / __exit__ usage."""

    def test_context_manager_auto_finishes(self, tmp_path):
        log_dir = tmp_path / "ctx_logs"
        with TranslationLogger(base_dir=log_dir) as tl:
            tl.start_batch("mock", "mock-v1", "en", "es")
            tl.log_identifier_pair(
                source="x",
                target="y",
                target_lang="es",
                role="variable",
                naming_convention="snake_case",
            )
        # After context manager exit, metadata should be written
        assert tl._identifier_file is None  # files closed

    def test_context_manager_returns_self(self, tmp_path):
        log_dir = tmp_path / "ctx_logs"
        with TranslationLogger(base_dir=log_dir) as tl:
            assert isinstance(tl, TranslationLogger)

    def test_context_manager_without_start_batch(self, tmp_path):
        """Exiting without starting a batch should not raise."""
        log_dir = tmp_path / "ctx_logs"
        with TranslationLogger(base_dir=log_dir):
            pass  # No start_batch, no error


# ===========================================================================
# Crash safety: flush behavior
# ===========================================================================


class TestFlushBehavior:
    """Test that files are flushed after each write for crash safety."""

    def test_identifier_file_flushed(self, started_logger):
        started_logger.log_identifier_pair(
            source="x",
            target="y",
            target_lang="es",
            role="variable",
            naming_convention="snake_case",
        )
        # File should be readable even before finish_batch
        batch_dir = started_logger._batch_dir
        content = (batch_dir / "identifier_pairs.jsonl").read_text(encoding="utf-8")
        assert "x" in content

    def test_text_file_flushed(self, started_logger):
        started_logger.log_text_pair(
            source="comment text",
            target="texto",
            target_lang="es",
            kind="comment",
        )
        batch_dir = started_logger._batch_dir
        content = (batch_dir / "text_pairs.jsonl").read_text(encoding="utf-8")
        assert "comment text" in content

    def test_failure_file_flushed(self, started_logger):
        started_logger.log_validation_failure(
            identifier="x",
            first_attempt="bad value",
            failure_reason="invalid",
        )
        batch_dir = started_logger._batch_dir
        content = (batch_dir / "validation_failures.jsonl").read_text(encoding="utf-8")
        assert "bad value" in content
