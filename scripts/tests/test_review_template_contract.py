"""The review template's consistency contract (CORE-1702).

``scripts/generate_reference_docs.py`` writes one REFERENCE.md per registry
language. That file is the markdown review template: a reviewer copies it,
fills the Suggested and Comments columns, and submits it. The contract below
is what makes a review interpretable later, across pack versions, Python
versions, languages and dialects:

* every version string comes from one source (the pack's ``pyproject.toml``,
  its version files, ``version-index.yml``); the hidden line, the heading and
  the language column agree;
* the Python axis is explicit: the template shows the newest Python view and
  every row states the versions its word applies to, with the earlier word
  where one exists (Sinhala ZWJ forms);
* every row carries a stable key, the key set equals English's for the same
  view, and a term a pack lacks is listed, never silently filled with English;
* values are byte-identical to the pack, RTL terms are single runs;
* nothing repo-wide is in a template, so regeneration is per pack;
* a dialect pack marks the rows it inherits from its base.
* the example program round-trips: with its pack words reversed to English it
  compiles, and none of its illustrative identifiers is a word of the pack.

Expected values are derived from the YAML and the registry in this module,
independently of the generator's own loader.
"""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import io
import json
import re
import shutil
import sqlite3
import sys
import tokenize
import unicodedata
from collections import Counter
from pathlib import Path

import pytest
import yaml

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10
    import tomli as tomllib  # type: ignore[import-not-found, no-redef]

from legesher_core.language_interface import create_translator_from_language_pack
from legesher_i18n.intake.review_template import parse_metadata_line
from legesher_i18n.script_policy import nfkc_delta_class

ROOT = Path(__file__).resolve().parents[2]
PACKS_DIR = ROOT / "libs" / "i18n" / "language-packs" / "python"
REGISTRY_PATH = ROOT / "libs" / "i18n" / "legesher_i18n" / "languages.json"
REGISTRY = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))["languages"]
CODES = sorted(REGISTRY)
RTL_CODES = [code for code in CODES if REGISTRY[code]["rtl"]]
VERSION_INDEX = yaml.safe_load(
    (PACKS_DIR / "version-index.yml").read_text(encoding="utf-8")
)["python_versions"]
SECTIONS = ("keywords", "builtins", "exceptions", "implicit_params")
INDEX_LISTS = {
    "keywords": "added_keywords",
    "builtins": "added_builtins",
    "exceptions": "added_exceptions",
}


def _version_key(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


PY_VERSIONS = sorted(VERSION_INDEX, key=_version_key)
NEWEST = PY_VERSIONS[-1]


def _generator():
    spec = importlib.util.spec_from_file_location(
        "generate_reference_docs", ROOT / "scripts" / "generate_reference_docs.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # Registered before exec: the generator's dataclasses resolve their
    # string annotations through sys.modules[module.__name__].
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


G = _generator()


def _version_files(code: str, packs_root: Path = PACKS_DIR) -> list[Path]:
    (packs_dir,) = list((packs_root / code).glob("legesher_i18n_python_*/packs"))
    return sorted(packs_dir.glob("3.*.yml"), key=lambda p: _version_key(p.stem))


def _layers(code: str, packs_root: Path = PACKS_DIR) -> list[tuple[str, dict]]:
    """``(python version, raw YAML)`` per version file, oldest first."""
    return [
        (path.stem, yaml.safe_load(path.read_text(encoding="utf-8")) or {})
        for path in _version_files(code, packs_root)
    ]


def _merged(
    code: str, upto: str = NEWEST, packs_root: Path = PACKS_DIR
) -> dict[str, str]:
    """``section.term -> word`` as the files up to *upto* merge, later files winning."""
    words: dict[str, str] = {}
    for version, data in _layers(code, packs_root):
        if _version_key(version) > _version_key(upto):
            continue
        for section in SECTIONS:
            for term, word in (data.get(section) or {}).items():
                words[f"{section}.{term}"] = str(word)
    return words


def _pyproject(code: str, packs_root: Path = PACKS_DIR) -> dict:
    with (packs_root / code / "pyproject.toml").open("rb") as handle:
        return tomllib.load(handle)["project"]


def _rows(text: str) -> dict[str, list[str]]:
    """Key -> stripped cells of every six-cell term row in *text*."""
    rows: dict[str, list[str]] = {}
    in_fence = False
    for line in text.splitlines():
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or not line.startswith("| `"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) == 6:
            rows[cells[0].strip("`")] = cells
    return rows


@pytest.fixture(scope="module")
def english_view():
    return G.load_pack_view("en")


@pytest.fixture(scope="module")
def views(english_view):
    return {code: G.load_pack_view(code) for code in CODES}


@pytest.fixture(scope="module")
def templates(views, english_view):
    return {code: G.render_template(views[code], english_view) for code in CODES}


# --- versions -----------------------------------------------------------------


@pytest.mark.parametrize("code", CODES)
def test_view_takes_every_version_from_its_single_source(views, code: str) -> None:
    view = views[code]
    project = _pyproject(code)
    assert view.pack_name == project["name"]
    assert view.pack_version == project["version"]
    assert view.python == _version_files(code)[-1].stem == NEWEST
    assert view.python_versions == tuple(path.stem for path in _version_files(code))
    assert view.code == code
    assert view.bcp47 == REGISTRY[code]["bcp47"]


@pytest.mark.parametrize("code", CODES)
def test_hidden_line_heading_and_column_agree(templates, views, code: str) -> None:
    text = templates[code]
    view = views[code]
    meta = parse_metadata_line(text)
    assert (meta.pack, meta.pack_version, meta.python, meta.code, meta.bcp47) == (
        view.pack_name,
        view.pack_version,
        view.python,
        code,
        view.bcp47,
    )
    name, native = REGISTRY[code]["name"], REGISTRY[code]["native"]
    heading = f"# {name} ({native}) · {view.pack_name} {view.pack_version} · Python {view.python}"
    assert text.splitlines()[1] == heading
    column = f"| {name} · {view.pack_version} · Python {view.python} |"
    assert text.count(column) == len(SECTIONS)
    # One source: the only x.y.z in the file is the pack version, and the only
    # Python version literal outside the tables is the view's.
    assert set(re.findall(r"\b\d+\.\d+\.\d+\b", text)) == {view.pack_version}
    usage = text.split("## Usage", 1)[1].split("## ", 1)[0]
    assert f'"{view.python}"' in usage


@pytest.mark.parametrize("code", CODES)
def test_digest_fingerprints_this_packs_version_files(views, code: str) -> None:
    digest = hashlib.sha256()
    for path in _version_files(code):
        digest.update(path.name.encode())
        digest.update(path.read_bytes())
    assert views[code].digest == digest.hexdigest()[:12]


# --- the Python axis ------------------------------------------------------------


def test_index_additions_appear_in_the_english_file_for_that_version() -> None:
    layers = dict(_layers("en"))
    for version, info in VERSION_INDEX.items():
        for section, list_name in INDEX_LISTS.items():
            for term in info.get(list_name) or []:
                assert term in (layers[version].get(section) or {}), (
                    f"version-index says {section}.{term} arrives in {version}, "
                    f"but en/{version}.yml does not set it"
                )


def _index_additions() -> list[tuple[str, str]]:
    return [
        (f"{section}.{term}", version)
        for version, info in VERSION_INDEX.items()
        for section, list_name in INDEX_LISTS.items()
        for term in info.get(list_name) or []
    ]


@pytest.mark.parametrize(("key", "version"), _index_additions())
@pytest.mark.parametrize("code", CODES)
def test_added_terms_apply_from_the_version_that_added_them(
    views, code: str, key: str, version: str
) -> None:
    row = views[code].rows_by_key[key]
    assert _version_key(row.applies_from) >= _version_key(version)
    if not row.earlier:
        assert row.applies_from == version


def _histories(
    code: str, packs_root: Path = PACKS_DIR
) -> dict[str, list[tuple[str, str]]]:
    """``key -> [(version, word), ...]`` for every distinct consecutive word along the chain."""
    histories: dict[str, list[tuple[str, str]]] = {}
    for version, data in _layers(code, packs_root):
        for section in SECTIONS:
            for term, word in (data.get(section) or {}).items():
                history = histories.setdefault(f"{section}.{term}", [])
                if not history or history[-1][1] != str(word):
                    history.append((version, str(word)))
    return histories


def _expected_earlier(
    history: list[tuple[str, str]], versions: list[str]
) -> tuple[tuple[str, str, str], ...]:
    return tuple(
        (version, versions[versions.index(history[index + 1][0]) - 1], word)
        for index, (version, word) in enumerate(history[:-1])
    )


def _overrides() -> list[tuple[str, str, list[tuple[str, str]]]]:
    """Every (code, key, history) whose word changes along the chain."""
    return [
        (code, key, history)
        for code in CODES
        for key, history in _histories(code).items()
        if len(history) > 1
    ]


OVERRIDES = _overrides()


def test_the_shipped_overrides_are_the_ones_this_contract_is_built_on() -> None:
    # Sinhala's ZWJ rows and Japanese divmod; a new override is fine, but it
    # must be deliberate, so the set is pinned by language, not by count.
    assert {code for code, *_ in OVERRIDES} == {"si", "ja"}
    assert ("si", "keywords.True") in {(code, key) for code, key, *_ in OVERRIDES}


@pytest.mark.parametrize(("code", "key", "history"), OVERRIDES)
def test_an_overridden_word_states_every_range(
    views, templates, code, key, history
) -> None:
    row = views[code].rows_by_key[key]
    versions = list(views[code].python_versions)
    assert row.word == history[-1][1]
    assert row.applies_from == history[-1][0]
    assert row.earlier == _expected_earlier(history, versions)
    cells = _rows(templates[code])[key]
    assert cells[2] == f"`{row.word}`"
    ranges = "".join(f" ({start} to {end}: `{old}`)" for start, end, old in row.earlier)
    assert cells[3] == f"{row.applies_from}+{ranges}"


def test_sinhala_true_keeps_its_joiner_and_states_the_range(views) -> None:
    row = views["si"].rows_by_key["keywords.True"]
    assert "‍" in row.word
    assert "‍" not in row.earlier[0][2]
    assert row.earlier[0][0] == PY_VERSIONS[0]


@pytest.mark.parametrize("code", CODES)
def test_unoverridden_rows_state_a_single_open_range(
    templates, views, code: str
) -> None:
    cells = _rows(templates[code])
    for row in views[code].rows:
        if not row.earlier and row.inherited_from is None and row.word is not None:
            assert cells[row.key][3] == f"{row.applies_from}+"


def test_a_python_version_view_omits_later_terms_and_earlier_words() -> None:
    older = PY_VERSIONS[1]
    view = G.load_pack_view("si", python_version=older)
    assert view.python == older
    assert set(view.rows_by_key) == set(_merged("si", upto=older))
    assert "keywords.type" not in view.rows_by_key
    true_row = view.rows_by_key["keywords.True"]
    assert true_row.word == _merged("si", upto=older)["keywords.True"]
    assert true_row.earlier == ()
    text = G.render_template(view, G.load_pack_view("en", python_version=older))
    assert parse_metadata_line(text).python == older


# --- languages ---------------------------------------------------------------------


@pytest.mark.parametrize("code", CODES)
def test_key_set_equals_english_for_the_same_view(
    views, english_view, code: str
) -> None:
    keys = [row.key for row in views[code].rows]
    assert keys == [row.key for row in english_view.rows]
    assert all(key.split(".", 1)[0] in SECTIONS for key in keys)
    assert views[code].lacking == ()
    assert set(keys) == set(_merged(code))


@pytest.mark.parametrize("code", CODES)
def test_values_are_byte_identical_to_the_pack(templates, code: str) -> None:
    cells = _rows(templates[code])
    expected = _merged(code)
    assert set(cells) == set(expected)
    for key, word in expected.items():
        assert cells[key][2] == f"`{word}`"
        assert unicodedata.normalize("NFC", word) == word


@pytest.mark.parametrize(
    ("code", "key", "check"),
    [
        ("si", "keywords.True", lambda w: "‍" in w),
        (
            "hi",
            "keywords.class",
            lambda w: any(unicodedata.category(c) in {"Mn", "Mc"} for c in w),
        ),
        (
            "th",
            "keywords.while",
            lambda w: any(unicodedata.category(c) == "Mn" for c in w),
        ),
        ("ar", "keywords.except*", lambda w: w.endswith("*") and "؀" <= w[0] <= "ۿ"),
        (
            "he",
            "builtins.__import__",
            lambda w: w.startswith("__") and "א" <= w[2] <= "ת",
        ),
        ("zh", "keywords.class", lambda w: all("一" <= c <= "鿿" for c in w)),
    ],
)
def test_script_specific_values_survive_rendering(templates, code, key, check) -> None:
    word = _merged(code)[key]
    assert check(word), (
        f"the {code} pack no longer carries the script feature this test pins"
    )
    assert _rows(templates[code])[key][2] == f"`{word}`"


@pytest.mark.parametrize("code", RTL_CODES)
def test_rtl_term_cells_are_single_right_to_left_runs(templates, code: str) -> None:
    # A single strong-RTL run with neutrals only at the edges renders in the
    # same visual order inside a table cell as on a Python source line.
    for key, cells in _rows(templates[code]).items():
        words = [cells[2].strip("`")] + re.findall(r"`([^`]+)`", cells[3])
        for word in words:
            word = word.strip("_*")
            classes = {unicodedata.bidirectional(char) for char in word}
            assert classes <= {"R", "AL", "NSM", "ON", "BN"}, (key, word, classes)
            assert classes & {"R", "AL"}, (key, word)


def test_a_lacking_term_is_listed_not_filled_with_english(
    tmp_path: Path, english_view
) -> None:
    packs_root = tmp_path / "packs"
    shutil.copytree(PACKS_DIR / "si", packs_root / "si")
    shutil.copytree(PACKS_DIR / "en", packs_root / "en")
    base = packs_root / "si" / "legesher_i18n_python_si" / "packs" / "3.10.yml"
    data = yaml.safe_load(base.read_text(encoding="utf-8"))
    del data["keywords"]["while"]
    base.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    view = G.load_pack_view("si", packs_root=packs_root)
    assert view.lacking == ("keywords.while",)
    row = view.rows_by_key["keywords.while"]
    assert row.word is None
    cells = _rows(G.render_template(view, english_view))["keywords.while"]
    assert cells[2] == "(no word in this pack)"


@pytest.mark.parametrize("code", CODES)
def test_template_carries_nothing_repo_wide(templates, code: str) -> None:
    text = templates[code]
    assert not re.search(r"\b[0-9a-f]{40}\b", text)
    assert not re.search(r"\b\d{4}-\d{2}-\d{2}\b", text)
    assert str(len(REGISTRY)) + " languages" not in text


def test_a_template_is_a_function_of_its_own_pack_only(
    tmp_path: Path, english_view
) -> None:
    packs_root = tmp_path / "packs"
    shutil.copytree(PACKS_DIR, packs_root)
    other = packs_root / "de" / "legesher_i18n_python_de" / "packs" / "3.10.yml"
    other.write_text(
        other.read_text(encoding="utf-8").replace("wenn", "falls"), encoding="utf-8"
    )
    before = G.render_template(G.load_pack_view("si"), english_view)
    after = G.render_template(
        G.load_pack_view("si", packs_root=packs_root),
        G.load_pack_view("en", packs_root=packs_root),
    )
    assert before == after


# --- dialects --------------------------------------------------------------------


def test_a_dialect_pack_marks_the_rows_it_inherits(tmp_path: Path) -> None:
    packs_root = tmp_path / "packs"
    shutil.copytree(PACKS_DIR / "es", packs_root / "es")
    shutil.copytree(PACKS_DIR / "en", packs_root / "en")
    dialect = packs_root / "es-MX" / "legesher_i18n_python_es_mx" / "packs"
    dialect.mkdir(parents=True)
    (packs_root / "es-MX" / "pyproject.toml").write_text(
        '[project]\nname = "legesher-i18n-python-es-mx"\nversion = "0.0.1"\n',
        encoding="utf-8",
    )
    (dialect / "3.10.yml").write_text(
        "language: es-MX\ntarget: python\nversion: '3.10'\nkeywords:\n  if: si_mx\n"
        "builtins:\n  print: imprimir_mx\n",
        encoding="utf-8",
    )
    registry = {
        **REGISTRY,
        "es-MX": {**REGISTRY["es"], "name": "Spanish (Mexico)", "bcp47": "es-MX"},
    }
    view = G.load_pack_view("es-MX", packs_root=packs_root, registry=registry)
    assert view.base == "es"
    assert view.pack_version == "0.0.1"
    assert view.python == "3.10"
    own = {row.key for row in view.rows if row.inherited_from is None}
    assert own == {"keywords.if", "builtins.print"}
    base_words = _merged("es", upto="3.10")
    for row in view.rows:
        if row.inherited_from is not None:
            assert row.inherited_from == "es"
            assert row.word == base_words[row.key]
    assert view.lacking == ()
    english = G.load_pack_view("en", packs_root=packs_root, python_version="3.10")
    text = G.render_template(view, english)
    cells = _rows(text)
    assert cells["keywords.while"][3] == "3.10+ · inherited from es"
    assert cells["keywords.if"][3] == "3.10+"
    # Rendering reads the injected registry, not the global one.
    assert f"| **ISO 639-2** | `{REGISTRY['es']['iso639_2']}` |" in text
    assert "| **BCP 47 Tag** | `es-MX` |" in text


@pytest.mark.parametrize("code", CODES)
def test_shipped_packs_inherit_nothing(views, code: str) -> None:
    assert views[code].base is None
    assert all(row.inherited_from is None for row in views[code].rows)


# --- the template as a whole -----------------------------------------------------------


REQUIRED_CONSENT_LINES = [
    "- [ ] These suggestions and comments are my own work. AI help with formatting is fine; the",
    "      linguistic judgment is mine.",
    "- [ ] I sign off under the Developer Certificate of Origin.",
    "- [ ] I license my suggestions and comments under Apache-2.0.",
    "- [ ] I agree to the Code of Conduct.",
    '- [ ] I have read "Your contributions and your data" (CONTRIBUTOR_PRIVACY.md, version 1.0) and agree.',
    "- [ ] My contribution data may appear in research datasets and publications (never my identity).",
    "Credit me as (keep one): anonymous · my GitHub handle · this name: `<name>`",
]


@pytest.mark.parametrize("code", CODES)
def test_consent_block_matches_the_decision_record(templates, code: str) -> None:
    text = templates[code]
    for line in REQUIRED_CONSENT_LINES:
        assert line in text, line
    assert "- [x]" not in text


@pytest.mark.parametrize("code", CODES)
def test_sections_are_the_same_in_every_language(templates, code: str) -> None:
    headings = [line for line in templates[code].splitlines() if line.startswith("## ")]
    assert headings == [
        "## About you",
        "## Before you submit",
        "## Language Details",
        "## Keywords",
        "## Built-in Functions",
        "## Exceptions",
        "## Reserved Words",
        "## Example Code",
        "## Usage",
        "## Notes for Future Updates",
        "## How to submit this review",
    ]


@pytest.mark.parametrize("code", CODES)
def test_footer_points_at_language_packs_not_the_yaml(templates, code: str) -> None:
    text = templates[code]
    assert "Edit `legesher_i18n_python_" not in text
    assert "https://github.com/legesher/language-packs/blob/main/REVIEWING.md" in text
    bcp47 = REGISTRY[code]["bcp47"]
    assert f"`reviews/{bcp47}/{bcp47}-<your-github-username>.md`" in text
    assert "leave the first line of the file and" in text
    assert "—" not in text


def test_generator_writes_exactly_the_registry(tmp_path: Path) -> None:
    out = tmp_path / "out"
    G.main(["--out", str(out)])
    written = {path.parent.name for path in out.glob("*/REFERENCE.md")}
    assert written == set(REGISTRY)
    assert {path.name for path in out.iterdir()} == set(REGISTRY)


def test_generator_can_write_one_language(tmp_path: Path) -> None:
    out = tmp_path / "out"
    G.main(["--out", str(out), "--languages", "si,ja"])
    assert {path.parent.name for path in out.glob("*/REFERENCE.md")} == {"si", "ja"}


def test_a_word_overridden_twice_states_two_ranges(tmp_path: Path) -> None:
    packs_root = tmp_path / "packs"
    shutil.copytree(PACKS_DIR / "si", packs_root / "si")
    shutil.copytree(PACKS_DIR / "en", packs_root / "en")
    middle = packs_root / "si" / "legesher_i18n_python_si" / "packs" / "3.11.yml"
    data = yaml.safe_load(middle.read_text(encoding="utf-8"))
    data.setdefault("keywords", {})["True"] = "සත්යය"
    middle.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    view = G.load_pack_view("si", packs_root=packs_root)
    history = _histories("si", packs_root)["keywords.True"]
    assert len(history) == 3
    row = view.rows_by_key["keywords.True"]
    assert row.earlier == _expected_earlier(history, list(view.python_versions))
    assert [end for _, end, _ in row.earlier] == ["3.10", "3.12"]


def test_a_word_set_before_its_term_arrives_is_refused(tmp_path: Path) -> None:
    packs_root = tmp_path / "packs"
    shutil.copytree(PACKS_DIR / "si", packs_root / "si")
    shutil.copytree(PACKS_DIR / "en", packs_root / "en")
    base = packs_root / "si" / "legesher_i18n_python_si" / "packs" / "3.10.yml"
    data = yaml.safe_load(base.read_text(encoding="utf-8"))
    data["keywords"]["type"] = (
        "වර්ගය"  # the keyword arrives in 3.12 per version-index.yml
    )
    base.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    with pytest.raises(ValueError, match=r"keywords\.type"):
        G.load_pack_view("si", packs_root=packs_root)


@pytest.mark.parametrize(
    ("tag", "expected"),
    [
        ("es-MX", "es"),  # a region variant inherits from its base language
        (
            "pa-Arab",
            None,
        ),  # a script variant does not: the base is written in another script
        ("zh-Hans", None),  # no registry language has the bare tag
        ("fil", None),
    ],
)
def test_only_region_dialects_acquire_a_base(tag: str, expected: str | None) -> None:
    registry = {**REGISTRY, "pa": {**REGISTRY["hi"], "name": "Punjabi", "bcp47": "pa"}}
    assert G._base_code(tag, registry) == expected


# --- the example program -------------------------------------------------------------

#: True where ``tokenize`` spells NAME as ``\w+`` (CPython < 3.12), which
#: excludes marks and format characters (libs/core/tests/interpreter_gaps.py,
#: gap 1). The engine's return hop cannot match a pack word that fragments.
PURE_PYTHON_TOKENIZER = sys.version_info < (3, 12)


def _example_source(text: str) -> str:
    """The Python program inside the first ```python fence of *text*.

    *text* is a rendered template (the fence under its Example Code heading is
    taken) or the fenced block ``generate_example_code`` returns.
    """
    if "\n## Example Code\n" in text:
        text = text.split("\n## Example Code\n", 1)[1].split("\n## ", 1)[0]
    match = re.search(r"```python\n(.*?)\n```", text, re.DOTALL)
    assert match is not None, "no ```python fence in the example"
    return match.group(1)


def _example_identifier_keys() -> list[str]:
    """The EXAMPLE_TEXT keys whose values the example program uses as names.

    Read off the English program: every name it binds or reads that is an
    English EXAMPLE_TEXT value is an identifier key. The other keys are the
    docstring, the comments and the message strings, which no pack word can
    break.
    """
    english = G.load_pack_view("en")
    tree = ast.parse(_example_source(G.render_template(english, english)))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.arg):
            names.add(node.arg)
        elif isinstance(node, ast.ExceptHandler) and node.name:
            names.add(node.name)
    keys = [key for key, value in G.EXAMPLE_TEXT["en"].items() if value in names]
    assert keys, "the English example binds none of its EXAMPLE_TEXT values"
    return keys


EXAMPLE_IDENTIFIER_KEYS = _example_identifier_keys()


def _reverse_translate(source: str, code: str, python: str) -> str:
    """*source*, written in *code*'s words, back in canonical English.

    The same construction ``libs/i18n/scripts/validate_showcase_examples.py``
    uses for the preview showcase: the pack's English-to-local translator,
    reversed. The view's Python version is passed so the words reversed are
    the ones the template shows, not the running interpreter's.
    """
    en_to_local = create_translator_from_language_pack(
        "python", code, programming_language_version=python
    )
    return en_to_local.reverse().translate_code(source, code, "en")


#: True where ZWNJ, ZWJ and U+30FB are identifier characters (Unicode 15.1,
#: CPython 3.13+); libs/core/tests/interpreter_gaps.py, gap 2.
IDENTIFIER_RULES_ARE_UNICODE_15_1 = tuple(
    int(part) for part in unicodedata.unidata_version.split(".")
) >= (15, 1)

#: The characters Unicode 15.1 added to XID_Continue that the packs use.
UNICODE_15_1_CONTINUE_ADDITIONS = "\u200c\u200d\u30fb"


def _identifier_under_unicode_15_1(word: str) -> bool:
    """Whether *word* is an identifier once ZWNJ, ZWJ and U+30FB may continue one."""
    if not word or word[0] in UNICODE_15_1_CONTINUE_ADDITIONS:
        return False
    stand_in = {ord(ch): "_" for ch in UNICODE_15_1_CONTINUE_ADDITIONS}
    return word.translate(stand_in).isidentifier()


def _not_identifiers_here(code: str) -> list[str]:
    """Gap-2 words of *code*'s newest view and example identifiers, on this interpreter.

    Empty when this interpreter's Unicode tables are 15.1 or later (CPython
    3.13+). Before 15.1 it mirrors the strict ledger in
    libs/core/tests/interpreter_gaps.py (gap 2): it lists the words and example
    identifiers that ``str.isidentifier()`` refuses here but that become
    identifiers once ZWNJ, ZWJ and U+30FB are identifier characters (the
    Sinhala conjuncts spelled with ZWJ, the Japanese ``divmod`` with the
    katakana middle dot). If anything else is not an identifier, it returns
    an empty list, so the test fails instead of expecting a failure. English
    terms that are not identifiers themselves (``except*``) are left out.
    """
    if IDENTIFIER_RULES_ARE_UNICODE_15_1:
        return []
    english = _merged("en")
    words = [word for key, word in _merged(code).items() if english[key].isidentifier()]
    names = [G.EXAMPLE_TEXT[code][key] for key in EXAMPLE_IDENTIFIER_KEYS]
    refused = [word for word in words + names if not word.isidentifier()]
    if not all(_identifier_under_unicode_15_1(word) for word in refused):
        return []
    return refused


def _error_tokens(source: str) -> Counter[str]:
    """Multiset of ERRORTOKEN strings the running ``tokenize`` emits."""
    try:
        return Counter(
            token.string
            for token in tokenize.generate_tokens(io.StringIO(source).readline)
            if token.type == tokenize.ERRORTOKEN
        )
    except tokenize.TokenError:
        return Counter()


def _fragmenting_pack_words(code: str, native: str) -> list[str]:
    """Fragments of the pack words in *native* the running tokenizer cannot read whole.

    The same program rendered with English keywords, builtins and exceptions
    but the same identifiers is the baseline, so an identifier that fragments
    appears in both renderings and cancels out; what remains came from a pack
    word. Empty with the C tokenizer (CPython 3.12+).
    """
    if not PURE_PYTHON_TOKENIZER:
        return []
    english_words = _example_source(G.generate_example_code(code, {}, {}, {}))
    return sorted((_error_tokens(native) - _error_tokens(english_words)).elements())


@pytest.mark.parametrize("code", CODES)
def test_example_code_round_trips_and_compiles(
    request: pytest.FixtureRequest, templates, views, code: str
) -> None:
    source = _example_source(templates[code])
    unspellable = _not_identifiers_here(code)
    if unspellable:
        request.applymarker(
            pytest.mark.xfail(
                strict=True,
                reason=(
                    f"{code}: {unspellable} are identifiers only from Unicode 15.1 "
                    f"(CPython 3.13) and this interpreter's tables "
                    f"({unicodedata.unidata_version}) reject them, so the view "
                    "neither loads nor compiles here "
                    "(libs/core/tests/interpreter_gaps.py, gap 2)"
                ),
            )
        )
    else:
        fragments = _fragmenting_pack_words(code, source)
        if fragments:
            shown = ", ".join(f"U+{ord(ch):04X}" for ch in dict.fromkeys(fragments))
            pytest.skip(
                f"pure-Python tokenize (CPython {sys.version_info.major}."
                f"{sys.version_info.minor}) spells NAME as \\w+ and reads {shown} as "
                "ERRORTOKEN fragments, so the return hop never matches the pack "
                "words they belong to and whether the example compiles is not "
                "predicted; pinned strictly by libs/core/tests "
                "(interpreter_gaps.py, gap 1; CORE-2192)"
            )
    canonical = _reverse_translate(source, code, views[code].python)
    try:
        compile(canonical, f"<{code} REFERENCE.md example>", "exec")
    except SyntaxError as exc:
        line = canonical.splitlines()[exc.lineno - 1] if exc.lineno else ""
        pytest.fail(
            f"{code}: the example does not compile once its pack words are "
            f"English again: line {exc.lineno}: {exc.msg}\n    {line.strip()}"
        )


@pytest.mark.parametrize("code", CODES)
def test_example_identifiers_never_collide_with_pack_words(code: str) -> None:
    # Python compares names after NFKC (PEP 3131), so a spelling that is
    # NFKC-equal to a pack word shadows it as surely as the same bytes do.
    owners: dict[str, list[str]] = {}
    for key, history in _histories(code).items():
        for _version, word in history:
            owners.setdefault(unicodedata.normalize("NFKC", word), []).append(key)
    text = G.EXAMPLE_TEXT[code]
    problems = [
        f"EXAMPLE_TEXT[{code!r}][{key!r}] = {text[key]!r} is this pack's word for "
        + ", ".join(owners[unicodedata.normalize("NFKC", text[key])])
        for key in EXAMPLE_IDENTIFIER_KEYS
        if unicodedata.normalize("NFKC", text[key]) in owners
    ]
    assert not problems, "\n".join(problems)


def test_example_identifiers_are_nfkc_fixed_points() -> None:
    # The hi and bn style guides (and python.yml) require identifiers to be
    # NFKC fixed points, so the name in the template is the name Python binds.
    # The one allowance is the pack gate's own: Thai SARA AM (U+0E33), whose
    # decomposition CPython folds to the same identifier ("sara-am-only" in
    # legesher_i18n.script_policy). Any other instability is a failure.
    unstable = []
    for code in CODES:
        for key in EXAMPLE_IDENTIFIER_KEYS:
            word = G.EXAMPLE_TEXT[code][key]
            delta = nfkc_delta_class(word)
            if delta is not None and delta != "sara-am-only":
                unstable.append(
                    f"EXAMPLE_TEXT[{code!r}][{key!r}] = {word!r} is NFKC-unstable "
                    f"({delta})"
                )
    assert not unstable, "\n".join(unstable)


HOOK_PATHS = [
    "libs/i18n/language-packs/python/si/legesher_i18n_python_si/packs/3.13.yml",
    "libs/i18n/language-packs/python/si/pyproject.toml",
    "libs/i18n/language-packs/python/version-index.yml",
    "libs/i18n/legesher_i18n/languages.json",
    "libs/i18n/legesher_i18n/intake/review_template.py",
    "scripts/generate_reference_docs.py",
]


@pytest.mark.parametrize("path", HOOK_PATHS)
def test_regenerate_hook_fires_on_every_template_input(path: str) -> None:
    config = yaml.safe_load(
        (ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8")
    )
    hooks = [
        hook
        for repo in config["repos"]
        for hook in repo["hooks"]
        if hook.get("id") == "regenerate-reference-docs"
    ]
    assert len(hooks) == 1
    assert re.search(hooks[0]["files"], path), (
        f"{path} does not trigger the regenerate hook"
    )


# --- the template read back by the review parser (CORE-2508) ------------------------
#
# The parser keys on what the generator writes: the hidden line, the six boxes,
# the six columns and the row keys. These tests render templates the shipped
# packs cannot produce today (a dialect, a lacking term) and read them back, so
# the parser's decisions on those rows are pinned to the generator's real output.

from legesher_i18n.db.schema_v2 import apply_schema_v2  # noqa: E402
from legesher_i18n.intake.review_parser import (  # noqa: E402
    PullRequest,
    ReviewFileRefused,
    parse_review_file,
    read_review_file,
)


def _filled(template: str, rows: dict[str, tuple[str, str]], user: str = "reviewer") -> str:
    """Tick every box, name *user*, fill *rows* (key -> Suggested, Comments)."""
    text = template.replace("`<your-github-username>`", f"`{user}`", 1).replace("- [ ]", "- [x]")
    lines = text.split("\n")
    for index, line in enumerate(lines):
        for key, (suggested, comments) in rows.items():
            if line.startswith(f"| `{key}` |"):
                lines[index] = f"{line[: -len('| | |')]}| {suggested} | {comments} |"
    return "\n".join(lines)


def _concept_db(tmp_path: Path, tag: str, terms: dict[str, str]) -> sqlite3.Connection:
    conn = sqlite3.connect(tmp_path / "contract.db")
    apply_schema_v2(conn)
    conn.execute(
        "INSERT INTO programming_languages(code, name, status) VALUES ('python', 'Python', 'shipping')"
    )
    language, _, region = tag.partition("-")
    conn.execute(
        "INSERT INTO locales(tag, language_subtag, region_subtag, name, native_name,"
        " direction, in_registry) VALUES (?, ?, ?, ?, ?, 'ltr', 1)",
        (tag, language, region or None, tag, tag),
    )
    for term, category in terms.items():
        cursor = conn.execute(
            "INSERT INTO concepts(slug, definition_en, category) VALUES (?, ?, ?)",
            (term, term, category),
        )
        conn.execute(
            "INSERT INTO terms(concept_id, programming_language, name, category)"
            " VALUES (?, 'python', ?, ?)",
            (cursor.lastrowid, term, category),
        )
    return conn


def _dialect_template(tmp_path: Path) -> str:
    packs_root = tmp_path / "packs"
    shutil.copytree(PACKS_DIR / "es", packs_root / "es")
    shutil.copytree(PACKS_DIR / "en", packs_root / "en")
    dialect = packs_root / "es-MX" / "legesher_i18n_python_es_mx" / "packs"
    dialect.mkdir(parents=True)
    (packs_root / "es-MX" / "pyproject.toml").write_text(
        '[project]\nname = "legesher-i18n-python-es-mx"\nversion = "0.0.1"\n', encoding="utf-8"
    )
    (dialect / "3.10.yml").write_text(
        "language: es-MX\ntarget: python\nversion: '3.10'\nkeywords:\n  if: si_mx\n",
        encoding="utf-8",
    )
    registry = {**REGISTRY, "es-MX": {**REGISTRY["es"], "name": "Spanish (Mexico)", "bcp47": "es-MX"}}
    view = G.load_pack_view("es-MX", packs_root=packs_root, registry=registry)
    english = G.load_pack_view("en", packs_root=packs_root, python_version="3.10")
    return G.render_template(view, english)


def test_a_verdict_on_an_inherited_dialect_row_is_evidence_for_the_dialect(
    tmp_path: Path,
) -> None:
    template = _dialect_template(tmp_path)
    base_word = _merged("es", upto="3.10")["keywords.while"]
    text = _filled(template, {"keywords.while": ("", "✓"), "keywords.for": ("`pa_cada`", "regional")})
    review = read_review_file(text, template)
    inherited = {row.key: row.inherited_from for row in review.answered}
    assert inherited == {"keywords.while": "es", "keywords.for": "es"}
    assert any("inherited from es" in note and "es-MX" in note for note in review.notes)

    conn = _concept_db(tmp_path, "es-MX", {"while": "keyword", "for": "keyword"})
    bundle = parse_review_file(
        text,
        template_text=template,
        path="reviews/es-MX/es-MX-reviewer.md",
        pull_request=PullRequest("https://github.com/legesher/language-packs/pull/9", 9, "reviewer"),
        conn=conn,
    ).bundle
    assert bundle["locale"] == "es-MX"
    surfaces = {r["concept"]: [e["surface_form"] for e in r["endorsements"]] for r in bundle["responses"]}
    assert surfaces == {"while": [base_word], "for": ["pa_cada"]}


def _lacking_template(tmp_path: Path, english_view) -> str:
    packs_root = tmp_path / "packs"
    shutil.copytree(PACKS_DIR / "si", packs_root / "si")
    shutil.copytree(PACKS_DIR / "en", packs_root / "en")
    base = packs_root / "si" / "legesher_i18n_python_si" / "packs" / "3.10.yml"
    data = yaml.safe_load(base.read_text(encoding="utf-8"))
    del data["keywords"]["while"]
    base.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return G.render_template(G.load_pack_view("si", packs_root=packs_root), english_view)


@pytest.mark.parametrize("comments", ["✓", "Keep: fine as it is"])
def test_a_tick_or_keep_on_a_no_word_row_is_refused_by_key(
    tmp_path: Path, english_view, comments: str
) -> None:
    template = _lacking_template(tmp_path, english_view)
    with pytest.raises(ReviewFileRefused) as caught:
        read_review_file(_filled(template, {"keywords.while": ("", comments)}), template)
    problems = "\n".join(caught.value.problems)
    assert "keywords.while" in problems and "nothing to endorse" in problems


def test_a_suggestion_on_a_no_word_row_proposes_the_first_word(
    tmp_path: Path, english_view
) -> None:
    template = _lacking_template(tmp_path, english_view)
    text = _filled(template, {"keywords.while": ("`අතරතුර`", "the usual word for while")})
    (row,) = read_review_file(text, template).answered
    assert (row.key, row.current, row.verdict, row.suggested) == (
        "keywords.while", None, "suggest", "අතරතුර",
    )
