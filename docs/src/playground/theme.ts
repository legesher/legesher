// The playground editor's theme: the docs site's code palette.
//
// The colours are the --lg-code-* variables in src/styles/custom.css, the ones
// the ordinary code blocks use. They switch with the site's light and dark
// themes (<html data-theme>), so the editor follows the site without being
// reconfigured, including when the reader changes the theme while the editor
// is mounted.

import { HighlightStyle, syntaxHighlighting } from "@codemirror/language";
import type { Extension } from "@codemirror/state";
import { EditorView } from "@codemirror/view";
import { tags as t } from "@lezer/highlight";

// The site's code palette (src/styles/custom.css: --lg-code-*), the one the
// ordinary code blocks use. The variables switch with the light and dark
// themes, so the editor follows the page. basicSetup's default style stays as
// a fallback only; this one wins. The localized highlight layer (highlight.ts)
// asks the active style for its classes, so localized words get these too.
const palette = HighlightStyle.define([
  { tag: [t.keyword, t.controlKeyword, t.definitionKeyword, t.moduleKeyword, t.operatorKeyword], color: "var(--lg-code-keyword)" },
  { tag: [t.bool, t.null, t.atom], color: "var(--lg-code-atom)" },
  { tag: [t.string, t.special(t.string)], color: "var(--lg-code-string)" },
  { tag: t.number, color: "var(--lg-code-number)" },
  { tag: t.comment, color: "var(--lg-code-comment)" },
  // Definition names only. Call names stay in the text colour: the grammar
  // does not know localized keywords, so it reads `saludar(nombre)` after
  // `definir` as a call, and a call colour would sit inside the definition
  // colour the localized layer gives that name.
  { tag: t.function(t.definition(t.variableName)), color: "var(--lg-code-function)" },
  { tag: t.definition(t.className), color: "var(--lg-code-class)" },
  // Plain names, operators and punctuation take the editor's text colour by
  // inheritance; styling plain names would add spans the localized layer does
  // not mirror. (lezer-python gives `self` no tag of its own, so builtins,
  // calls and `self` stay in the text colour here, unlike the code blocks.)
]);

// The editor's surfaces and overlays, from the same variables. CodeMirror's
// own overlay colours are tuned for a light page; these keep every token at
// 4.5:1 or more on selection, word matches, search matches and brackets, with
// an outline where a tint alone would be too faint to see.
const surface = EditorView.theme({
  "&": { backgroundColor: "var(--lg-code-bg)", color: "var(--lg-code-fg)" },
  ".cm-content": { caretColor: "var(--lg-code-fg)" },
  ".cm-cursor, .cm-dropCursor": { borderLeftColor: "var(--lg-code-fg)" },
  ".cm-gutters": {
    backgroundColor: "var(--lg-code-bg)",
    color: "var(--lg-code-comment)",
    borderRight: "1px solid var(--sl-color-gray-5)",
  },
  ".cm-activeLine, .cm-activeLineGutter": { backgroundColor: "var(--lg-code-active-line)" },
  "&.cm-focused > .cm-scroller > .cm-selectionLayer .cm-selectionBackground, .cm-selectionBackground, .cm-content ::selection": {
    backgroundColor: "var(--lg-code-selection)",
  },
  ".cm-selectionMatch": {
    backgroundColor: "var(--lg-code-word-match)",
    outline: "1px solid var(--lg-code-word-match-edge)",
  },
  ".cm-searchMatch": {
    backgroundColor: "var(--lg-code-search-match)",
    outline: "1px solid var(--lg-code-search-edge)",
  },
  ".cm-searchMatch.cm-searchMatch-selected": {
    backgroundColor: "var(--lg-code-search-current)",
    outline: "2px solid var(--lg-code-search-edge)",
  },
  "&.cm-focused .cm-matchingBracket, .cm-matchingBracket": {
    backgroundColor: "var(--lg-code-bracket)",
    outline: "1px solid var(--lg-code-bracket-edge)",
  },
  ".cm-panels": {
    backgroundColor: "var(--lg-code-bg)",
    color: "var(--lg-code-fg)",
    borderColor: "var(--sl-color-gray-5)",
  },
  ".cm-panel.cm-search [name=close]": { color: "var(--lg-code-fg)" },
  ".cm-textfield": {
    backgroundColor: "transparent",
    color: "var(--lg-code-fg)",
    border: "1px solid var(--sl-color-gray-4)",
  },
  ".cm-button": {
    backgroundImage: "none",
    backgroundColor: "var(--sl-color-gray-6)",
    color: "var(--lg-code-fg)",
    border: "1px solid var(--sl-color-gray-4)",
  },
  ".cm-tooltip": {
    backgroundColor: "var(--lg-code-bg)",
    color: "var(--lg-code-fg)",
    border: "1px solid var(--sl-color-gray-5)",
  },
  ".cm-tooltip-autocomplete ul li[aria-selected]": {
    backgroundColor: "var(--lg-code-selection)",
    color: "var(--lg-code-fg)",
  },
});

/** Add to the editor's extensions. */
export const siteTheme: Extension = [syntaxHighlighting(palette), surface];
