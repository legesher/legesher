import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from generate_snippets import categorize_tokens, load_packs  # noqa: E402

SOURCE = (
    Path(__file__)
    .resolve()
    .parents[2]
    .joinpath("snippets", "hello-world.py")
    .read_text()
)
PACKS = load_packs("3.12")


def joined(spans):
    return "".join(t for t, _ in spans)


def test_spanish_keyword_and_builtin_categories():
    spans = categorize_tokens(SOURCE, PACKS["es"])
    cats = {t: c for t, c in spans}
    assert cats.get("definir") == "keyword"  # def
    assert cats.get("imprimir") == "builtin"  # print
    assert any(c == "exception" for _, c in spans)  # TypeError -> exception category


def test_output_reconstructs_full_source_shape():
    spans = categorize_tokens(SOURCE, PACKS["es"])
    out = joined(spans)
    assert out.count("\n") == SOURCE.count("\n")
    assert '"Hello, "' in out  # strings pass through byte-faithfully
    assert "definir greet(name):" in out  # identifiers untouched


def test_english_passthrough_is_identity():
    spans = categorize_tokens(SOURCE, PACKS["en"])
    assert joined(spans) == SOURCE


def test_ascii_digits_stay_ascii_in_arabic():
    src = "x = 42\n"
    spans = categorize_tokens(src, PACKS["ar"])
    assert "42" in joined(spans)
    assert "٤" not in joined(spans)


def test_nfc_verbatim_no_cf_stripping():
    # Sinhala/Thai values must come through with exact codepoints (NFC, ZWJ kept)
    for code in ("th", "si"):
        for t, c in categorize_tokens(SOURCE, PACKS[code]):
            if c in {"keyword", "builtin", "exception", "reserved"}:
                assert unicodedata.normalize("NFC", t) == t
