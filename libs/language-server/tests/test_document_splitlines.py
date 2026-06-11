"""Tests that the LSP line splitter does not over-split on Unicode separators.

The separator characters are built with ``chr()`` so the invisible/format
characters never appear literally in this source file. Each test embeds the
real character it names, so the test would FAIL if ``split_lines_lsp`` fell
back to ``str.splitlines()`` (which splits on all of these).
"""

from legesher_language_server.document import DocumentState, split_lines_lsp

U2028 = chr(0x2028)  # LINE SEPARATOR
U2029 = chr(0x2029)  # PARAGRAPH SEPARATOR
NEL = chr(0x0085)  # NEXT LINE
VT = chr(0x000B)  # VERTICAL TAB
FF = chr(0x000C)  # FORM FEED


class TestSplitLinesLsp:
    def test_u2028_stays_one_line(self):
        # A single editor line containing U+2028 must remain ONE logical line
        # (str.splitlines() would wrongly make it two).
        text = f"a = 1{U2028}still_same_line = 2"
        lines = split_lines_lsp(text)
        assert len(lines) == 1
        assert lines[0] == text

    def test_u2029_paragraph_separator_stays_one_line(self):
        text = f"x{U2029}y"
        assert split_lines_lsp(text) == [text]

    def test_nel_and_vertical_tab_stay_one_line(self):
        text = f"ab{NEL}cd{VT}ef{FF}gh"
        assert split_lines_lsp(text) == [text]

    def test_lf_splits(self):
        assert split_lines_lsp("a\nb\nc") == ["a", "b", "c"]

    def test_crlf_splits(self):
        assert split_lines_lsp("a\r\nb") == ["a", "b"]

    def test_lone_cr_splits(self):
        assert split_lines_lsp("a\rb") == ["a", "b"]

    def test_trailing_newline_no_empty_tail(self):
        assert split_lines_lsp("a\nb\n") == ["a", "b"]

    def test_empty_string(self):
        assert split_lines_lsp("") == []


class TestDocumentStateUsesLspSplitter:
    def test_line_count_with_u2028(self):
        # The U+2028 lives inside line 0; only the '\n' is a real line break,
        # so a correct splitter yields exactly 2 lines.
        doc = DocumentState(
            uri="file:///t.py",
            text=f"line0{U2028}still0\nline1",
            version=1,
            language_id="python",
        )
        assert doc.get_line_count() == 2

    def test_get_line_with_u2028(self):
        doc = DocumentState(
            uri="file:///t.py",
            text=f"line0{U2028}still0\nline1",
            version=1,
            language_id="python",
        )
        assert doc.get_line(0) == f"line0{U2028}still0"
        assert doc.get_line(1) == "line1"
        assert doc.get_line(2) is None
