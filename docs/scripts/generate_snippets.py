"""Generate localized snippet artifacts for the docs site.

Reads English Python snippets from docs/snippets/*.py, translates each into
all shipped pack languages, and categorizes every token so the site can emit
highlighted HTML without any grammar. Mirrors the engine's context-free
substitution: NAME tokens only, priority except*-compound > keyword >
builtin (incl. exceptions) > implicit param > identifier glossary; everything
else passes through.

Outputs under --out: snippet-langs.json and legesher-snippets.css (language
picker + display CSS), snippets/<slug>.json (localized variants with spans
plus the per-snippet identifier glossaries applied from
docs/snippets/identifiers/<lang>.yml), and highlight-terms/<lang>.json
(per-language token sets driving the playground's localized syntax
highlighting).
"""

from __future__ import annotations

import io
import sys
import tokenize
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "libs" / "i18n"))

from legesher_i18n.language_registry import (  # noqa: E402
    LANGUAGE_METADATA,
    get_active_language_codes,
)
from legesher_i18n.pack_loader import LanguagePackLoader  # noqa: E402

PACK_VERSION_DEFAULT = "3.12"

# FSTRING_START/MIDDLE/END exist only on Python 3.12+ (PEP 701); on older
# interpreters f-strings tokenize as a single STRING, so those members are
# simply absent. Build the map with getattr so the module imports on 3.10+
# (the docs build machine's python3 may lag the workspace's 3.13).
_TOKEN_CATEGORIES = {
    tok_type: category
    for tok_type, category in (
        (tokenize.STRING, "string"),
        (getattr(tokenize, "FSTRING_START", None), "string"),
        (getattr(tokenize, "FSTRING_MIDDLE", None), "string"),
        (getattr(tokenize, "FSTRING_END", None), "string"),
        (tokenize.COMMENT, "comment"),
        (tokenize.NUMBER, "number"),
    )
    if tok_type is not None
}


def _pascal_case_exceptions(exceptions: dict[str, str]) -> dict[str, str]:
    """Map lowercase exception keys to their real Python spellings.

    The loader stores exception keys lowercase; real source spells them like
    ValueError. Resolve the canonical spelling from builtins so lookups match
    NAME tokens exactly. Identity entries (value == lowercase key, e.g. the en
    pack's ``typeerror: typeerror``) mean "untranslated", so the display value
    is canonicalized too — variants must render real Python spellings.
    """
    import builtins as py_builtins

    canonical = {name.lower(): name for name in dir(py_builtins)}
    return {
        canonical.get(k, k): (canonical.get(v, v) if v == k else v)
        for k, v in exceptions.items()
    }


def load_packs(version: str = PACK_VERSION_DEFAULT) -> dict[str, dict]:
    loader = LanguagePackLoader()
    bundles: dict[str, dict] = {}
    for code in get_active_language_codes():
        pack = loader.load(code, "python", version)
        meta = LANGUAGE_METADATA[code]
        bundles[code] = {
            "keywords": dict(pack.keywords),
            "builtins": dict(pack.builtins),
            "exceptions_pascal": _pascal_case_exceptions(dict(pack.exceptions)),
            "reserved": dict(pack.implicit_params),
            "rtl": meta["rtl"],
            "native": meta["native"],
            "name": meta["name"],
        }
    return bundles


def categorize_tokens(
    source: str, bundle: dict, identifiers: dict[str, str] | None = None
) -> list[tuple[str, str]]:
    spans: list[tuple[str, str]] = []
    lines = source.splitlines(keepends=True)

    def slice_between(start: tuple[int, int], end: tuple[int, int]) -> str:
        (srow, scol), (erow, ecol) = start, end
        if srow == erow:
            return lines[srow - 1][scol:ecol] if srow - 1 < len(lines) else ""
        text = lines[srow - 1][scol:]
        for row in range(srow, erow - 1):
            text += lines[row]
        if erow - 1 < len(lines):
            text += lines[erow - 1][:ecol]
        return text

    tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    cursor = (1, 0)
    skip_next_op_star = False
    for i, tok in enumerate(tokens):
        if tok.type in (tokenize.ENCODING, tokenize.ENDMARKER):
            continue
        gap = slice_between(cursor, tok.start)
        if gap:
            spans.append((gap, "plain"))
        cursor = tok.end

        if skip_next_op_star and tok.type == tokenize.OP and tok.string == "*":
            skip_next_op_star = False
            continue  # consumed by the except* compound span

        if tok.type == tokenize.NAME:
            name = tok.string
            nxt = tokens[i + 1] if i + 1 < len(tokens) else None
            compound = name + "*"
            if (
                compound in bundle["keywords"]
                and nxt is not None
                and nxt.type == tokenize.OP
                and nxt.string == "*"
                and nxt.start == tok.end
            ):
                spans.append((bundle["keywords"][compound], "keyword"))
                skip_next_op_star = True
            elif name in bundle["keywords"]:
                spans.append((bundle["keywords"][name], "keyword"))
            elif name in bundle["exceptions_pascal"]:
                spans.append((bundle["exceptions_pascal"][name], "exception"))
            elif name in bundle["builtins"]:
                spans.append((bundle["builtins"][name], "builtin"))
            elif name in bundle["reserved"]:
                spans.append((bundle["reserved"][name], "reserved"))
            elif identifiers and name in identifiers:
                # Per-snippet identifier glossary (CORE-1696): display-layer
                # localization of sample identifiers; canonical stays English.
                spans.append((identifiers[name], "plain"))
            else:
                spans.append((tok.string, "plain"))
        else:
            spans.append((tok.string, _TOKEN_CATEGORIES.get(tok.type, "plain")))
    return spans


import argparse  # noqa: E402
import ast  # noqa: E402
import json  # noqa: E402
import unicodedata  # noqa: E402


def _nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def _highlight_terms(bundles: dict[str, dict]) -> dict:
    """Per-language token sets for the playground's localized highlighter.

    'k' colors like English keywords, 'a' like English True/False (bool tag),
    'b' like English builtin/exception call names. None is omitted on purpose:
    the default English style leaves it unstyled, so parity means no
    decoration. 's' names the language's def/class keywords so the client can
    mirror lezer-python's structural inference (definition-name coloring).
    Values are NFC so the client can match normalized words.
    """
    terms = {}
    for code, bundle in bundles.items():
        keywords = bundle["keywords"]
        atoms = {_nfc(keywords[k]) for k in ("True", "False") if k in keywords}
        skip = set(atoms)
        if "None" in keywords:
            skip.add(_nfc(keywords["None"]))
        kws = set()
        for value in keywords.values():
            word = _nfc(value)
            if word.endswith("*"):  # except* compound: match the word part
                word = word[:-1]
            if word not in skip:
                kws.add(word)
        builtins = {_nfc(v) for v in bundle["builtins"].values()} | {
            _nfc(v) for v in bundle["exceptions_pascal"].values()
        }
        structure = {
            key: _nfc(keywords[key]) for key in ("def", "class") if key in keywords
        }
        terms[code] = {
            "k": sorted(kws),
            "a": sorted(atoms),
            "b": sorted(builtins - kws),
            "s": structure,
        }
    return terms


def _css(langs: list[str]) -> str:
    rules = [
        ".lg-code pre[data-lang]{display:none}",
        '.lg-code pre[data-lang="en"]{display:block}',
    ]
    for code in langs:
        if code == "en":
            continue
        rules.append(
            f'html[data-snippet-lang="{code}"] .lg-code pre[data-lang]{{display:none}}\n'
            f'html[data-snippet-lang="{code}"] .lg-code pre[data-lang="{code}"]{{display:block}}'
        )
    return "\n".join(rules) + "\n"


def load_identifier_glossaries(
    snippets_dir: Path,
) -> dict[str, dict[str, dict[str, str]]]:
    """Read identifiers/<lang>.yml → {lang: {snippet: {english: localized}}}.

    A display/generation layer for sample identifiers (CORE-1696): canonical
    sources stay English; languages without a glossary (or entry) fall back
    to English identifiers. Everything is NFC-normalized on the way in.
    """
    import yaml

    glossaries: dict[str, dict[str, dict[str, str]]] = {}
    glossary_dir = snippets_dir / "identifiers"
    if not glossary_dir.is_dir():
        return glossaries
    for path in sorted(glossary_dir.glob("*.yml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        glossaries[path.stem] = {
            slug: {_nfc(str(k)): _nfc(str(v)) for k, v in (entries or {}).items()}
            for slug, entries in data.items()
        }
    return glossaries


def _validate_glossary(
    lang: str, slug: str, mapping: dict[str, str], bundle: dict
) -> None:
    """Refuse glossary words that collide with the language's pack tokens.

    A localized identifier equal to a localized keyword/builtin would be
    mis-translated by the engine's lang→en pass (and mis-highlighted), so it
    is a data error, caught at generation time.
    """
    taken: dict[str, str] = {}
    for category in ("keywords", "builtins", "exceptions_pascal", "reserved"):
        for value in bundle[category].values():
            taken.setdefault(_nfc(value), category)
    for english, localized in mapping.items():
        if localized in taken:
            print(
                f"error: identifiers/{lang}.yml {slug}.{english}: '{localized}' collides "
                f"with a pack {taken[localized]} token",
                file=sys.stderr,
            )
            raise SystemExit(1)
        if not localized.isidentifier():
            print(
                f"error: identifiers/{lang}.yml {slug}.{english}: '{localized}' is not a "
                "valid Python identifier",
                file=sys.stderr,
            )
            raise SystemExit(1)
    if len(set(mapping.values())) != len(mapping):
        print(
            f"error: identifiers/{lang}.yml {slug}: duplicate localized identifiers break "
            "the bidirectional swap",
            file=sys.stderr,
        )
        raise SystemExit(1)


def emit_artifacts(
    snippets_dir: Path, out_dir: Path, version: str = PACK_VERSION_DEFAULT
) -> None:
    bundles = load_packs(version)
    glossaries = load_identifier_glossaries(snippets_dir)
    (out_dir / "snippets").mkdir(parents=True, exist_ok=True)

    ordered = ["en"] + sorted(c for c in bundles if c != "en")
    langs_meta = [
        {
            "code": c,
            "native": bundles[c]["native"],
            "name": bundles[c]["name"],
            "rtl": bundles[c]["rtl"],
        }
        for c in ordered
    ]
    (out_dir / "snippet-langs.json").write_text(
        json.dumps(langs_meta, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    (out_dir / "legesher-snippets.css").write_text(_css(ordered), encoding="utf-8")
    # One file per language so the playground can lazy-load the selected
    # language's terms as a small chunk instead of bundling all packs.
    hl_dir = out_dir / "highlight-terms"
    hl_dir.mkdir(parents=True, exist_ok=True)
    for code, payload in _highlight_terms(bundles).items():
        (hl_dir / f"{code}.json").write_text(
            json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8"
        )

    for src_file in sorted(snippets_dir.glob("*.py")):
        source = src_file.read_text(encoding="utf-8")
        try:
            ast.parse(source)
        except SyntaxError as exc:
            print(
                f"error: {src_file.name} is not valid English Python: {exc}",
                file=sys.stderr,
            )
            raise SystemExit(1)
        slug = src_file.stem
        identifiers = {
            lang: per_snippet[slug]
            for lang, per_snippet in glossaries.items()
            if per_snippet.get(slug)
        }
        variants = {}
        for code in ordered:
            mapping = identifiers.get(code)
            if mapping:
                _validate_glossary(code, slug, mapping, bundles[code])
            spans = categorize_tokens(source, bundles[code], mapping)
            variants[code] = {
                "code": "".join(t for t, _ in spans),
                "spans": [[t, c] for t, c in spans],
                "rtl": bundles[code]["rtl"],
            }
        payload = {"slug": slug, "variants": variants, "identifiers": identifiers}
        (out_dir / "snippets" / f"{src_file.stem}.json").write_text(
            json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snippets", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--version", default=PACK_VERSION_DEFAULT)
    args = parser.parse_args()
    emit_artifacts(args.snippets, args.out, args.version)


if __name__ == "__main__":
    main()
