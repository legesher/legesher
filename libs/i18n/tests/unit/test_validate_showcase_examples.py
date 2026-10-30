"""Unit tests for the showcase example validator (CORE-1403).

Tests validate_showcase_examples.py: examples-root resolution, the
reverse-translate + ast.parse check against real shipped packs, coverage
warnings, and the strict-coverage / skip-if-missing exit-code contract.
"""

import sys
from pathlib import Path

import pytest

# Import from scripts directory
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
from validate_showcase_examples import (
    EXAMPLE_FILENAME,
    EXAMPLES_SUBDIR,
    discover_examples,
    main,
    resolve_examples_root,
)

# A valid Spanish showcase snippet: every localized token below is mapped
# by the real shipped `es` pack, so the reverse translation is canonical
# Python that parses.
VALID_ES_EXAMPLE = """\
definir saludar(nombre):
    mensaje = f"Hola, {nombre}"
    imprimir(mensaje)
    devolver mensaje


si __name__ == "__main__":
    saludar("Mundo")
"""

# A regressed snippet: `si_acaso` is not a token the `es` pack maps, so it
# survives reverse translation untouched and the result cannot ast.parse.
BROKEN_ES_EXAMPLE = """\
definir saludar(nombre):
    si_acaso nombre:
        imprimir(nombre)
"""


def make_examples_tree(root: Path, files: dict[str, str]) -> Path:
    """Create a fake preview checkout: <root>/languages/<lang>/hello_world.py."""
    for lang, content in files.items():
        lang_dir = root / EXAMPLES_SUBDIR / lang
        lang_dir.mkdir(parents=True)
        (lang_dir / EXAMPLE_FILENAME).write_text(content, encoding="utf-8")
    return root


@pytest.mark.unit
class TestResolveExamplesRoot:
    """Resolution order: CLI arg -> env var. Nothing else is searched."""

    def test_cli_arg_wins_over_env(self, tmp_path, monkeypatch):
        cli_root = tmp_path / "cli-root"
        env_root = tmp_path / "env-root"
        cli_root.mkdir()
        env_root.mkdir()
        monkeypatch.setenv("LEGESHER_PREVIEW_ROOT", str(env_root))

        resolved = resolve_examples_root(str(cli_root))

        assert resolved == cli_root

    def test_env_var_used_when_no_cli_arg(self, tmp_path, monkeypatch):
        env_root = tmp_path / "env-root"
        env_root.mkdir()
        monkeypatch.setenv("LEGESHER_PREVIEW_ROOT", str(env_root))

        resolved = resolve_examples_root(None)

        assert resolved == env_root

    def test_env_var_naming_a_missing_dir_resolves_to_none(self, tmp_path, monkeypatch):
        monkeypatch.setenv("LEGESHER_PREVIEW_ROOT", str(tmp_path / "absent"))

        resolved = resolve_examples_root(None)

        assert resolved is None

    def test_returns_none_when_neither_is_given(self, tmp_path, monkeypatch):
        monkeypatch.delenv("LEGESHER_PREVIEW_ROOT", raising=False)
        monkeypatch.chdir(tmp_path)

        resolved = resolve_examples_root(None)

        assert resolved is None


@pytest.mark.unit
class TestDiscoverExamples:
    def test_finds_examples_under_languages_subdir(self, tmp_path):
        root = make_examples_tree(tmp_path, {"es": "x = 1\n", "fr": "y = 2\n"})

        examples = discover_examples(root)

        assert set(examples) == {"es", "fr"}
        assert examples["es"] == root / EXAMPLES_SUBDIR / "es" / EXAMPLE_FILENAME

    def test_ignores_language_dirs_without_example_file(self, tmp_path):
        root = make_examples_tree(tmp_path, {"es": "x = 1\n"})
        (root / EXAMPLES_SUBDIR / "empty").mkdir()

        examples = discover_examples(root)

        assert set(examples) == {"es"}


@pytest.mark.unit
class TestValidation:
    def test_happy_path_valid_example_passes(self, tmp_path, capsys):
        root = make_examples_tree(tmp_path, {"es": VALID_ES_EXAMPLE})

        exit_code = main(["--examples-root", str(root)])

        captured = capsys.readouterr()
        assert exit_code == 0
        assert "es" in captured.out
        assert "1/1" in captured.out

    def test_regression_unmapped_token_fails(self, tmp_path, capsys):
        root = make_examples_tree(tmp_path, {"es": BROKEN_ES_EXAMPLE})

        exit_code = main(["--examples-root", str(root)])

        captured = capsys.readouterr()
        assert exit_code == 1
        assert "es" in captured.out
        assert "parse" in captured.out.lower()

    def test_failure_reported_even_in_quiet_mode(self, tmp_path, capsys):
        root = make_examples_tree(tmp_path, {"es": BROKEN_ES_EXAMPLE})

        exit_code = main(["--examples-root", str(root), "--quiet"])

        captured = capsys.readouterr()
        assert exit_code == 1
        assert "es" in captured.out

    def test_one_failure_does_not_mask_other_languages(self, tmp_path, capsys):
        root = make_examples_tree(
            tmp_path, {"es": BROKEN_ES_EXAMPLE, "fr": "défini f():\n    passer\n"}
        )

        exit_code = main(["--examples-root", str(root)])

        captured = capsys.readouterr()
        assert exit_code == 1
        # fr is valid French pack vocabulary and must still be validated/reported
        assert "fr" in captured.out


@pytest.mark.unit
class TestMissingExamplesRoot:
    def test_skip_if_missing_exits_zero_with_notice(self, tmp_path, capsys):
        missing = tmp_path / "does-not-exist"

        exit_code = main(["--examples-root", str(missing), "--skip-if-missing"])

        captured = capsys.readouterr()
        assert exit_code == 0
        assert "skip" in captured.out.lower()

    def test_missing_root_exits_two_without_skip_flag(self, tmp_path, capsys):
        missing = tmp_path / "does-not-exist"

        exit_code = main(["--examples-root", str(missing)])

        captured = capsys.readouterr()
        assert exit_code == 2
        assert str(missing) in captured.out

    def test_env_var_root_is_validated(self, tmp_path, monkeypatch, capsys):
        root = make_examples_tree(tmp_path / "env-root", {"es": VALID_ES_EXAMPLE})
        monkeypatch.setenv("LEGESHER_PREVIEW_ROOT", str(root))

        exit_code = main([])

        captured = capsys.readouterr()
        assert exit_code == 0
        assert "1/1" in captured.out
        assert str(root) in captured.out

    def test_env_var_naming_a_missing_dir_exits_two(
        self, tmp_path, monkeypatch, capsys
    ):
        missing = tmp_path / "does-not-exist"
        monkeypatch.setenv("LEGESHER_PREVIEW_ROOT", str(missing))

        exit_code = main([])

        captured = capsys.readouterr()
        assert exit_code == 2
        assert str(missing) in captured.out

    def test_nothing_given_with_skip_flag_exits_zero_with_notice(
        self, monkeypatch, capsys
    ):
        monkeypatch.delenv("LEGESHER_PREVIEW_ROOT", raising=False)

        exit_code = main(["--skip-if-missing", "--quiet"])

        captured = capsys.readouterr()
        assert exit_code == 0
        assert "NOTICE" in captured.out
        assert "LEGESHER_PREVIEW_ROOT" in captured.out
        assert "skip" in captured.out.lower()

    def test_nothing_given_without_skip_flag_exits_two_naming_env_var(
        self, monkeypatch, capsys
    ):
        monkeypatch.delenv("LEGESHER_PREVIEW_ROOT", raising=False)

        exit_code = main([])

        captured = capsys.readouterr()
        assert exit_code == 2
        assert "ERROR" in captured.out
        assert "LEGESHER_PREVIEW_ROOT" in captured.out


@pytest.mark.unit
class TestCoverage:
    def test_example_without_pack_is_warning_not_failure(self, tmp_path, capsys):
        # "xx" is not a shipped pack language
        root = make_examples_tree(tmp_path, {"es": VALID_ES_EXAMPLE, "xx": "x = 1\n"})

        exit_code = main(["--examples-root", str(root)])

        captured = capsys.readouterr()
        assert exit_code == 0
        assert "xx" in captured.out
        assert "warning" in captured.out.lower()

    def test_pack_without_example_is_warning_by_default(self, tmp_path, capsys):
        # Only an es example: every other shipped pack has no example
        root = make_examples_tree(tmp_path, {"es": VALID_ES_EXAMPLE})

        exit_code = main(["--examples-root", str(root)])

        captured = capsys.readouterr()
        assert exit_code == 0
        assert "warning" in captured.out.lower()

    def test_strict_coverage_makes_missing_example_a_failure(self, tmp_path, capsys):
        root = make_examples_tree(tmp_path, {"es": VALID_ES_EXAMPLE})

        exit_code = main(["--examples-root", str(root), "--strict-coverage"])

        captured = capsys.readouterr()
        assert exit_code == 1
        assert "missing" in captured.out.lower()
