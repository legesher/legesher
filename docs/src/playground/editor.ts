// Stock CodeMirror 6 editor for the playground (CORE-1551).
//
// Uses only stock @codemirror/* packages, with no @legesher/* dependency
// (that npm scope is not published). The editor itself is grammar-agnostic
// about which natural language the keywords are in: python() gives
// structural/string/comment highlighting, and the pack-driven decoration
// layer (highlight.ts, passed in via `extensions`) colors localized keywords
// and names to match the English view. The base text direction comes from
// direction.ts and can be switched while the editor is mounted; theme.ts
// gives it a dark theme that follows the site's.

import { EditorView, keymap } from "@codemirror/view";
import { EditorState, Prec, type Extension } from "@codemirror/state";
import { basicSetup } from "codemirror";
import { python } from "@codemirror/lang-python";
import { HighlightStyle, syntaxHighlighting } from "@codemirror/language";
import { tags as t } from "@lezer/highlight";

// The site's code palette (src/styles/custom.css: --lg-code-*), the one the
// ordinary code blocks use. The variables switch with the light and dark
// themes, so the editor follows the page. basicSetup's default style stays as
// a fallback only; this one wins. The localized highlight layer (highlight.ts)
// asks the active style for its classes, so localized words get these too.
const palette = HighlightStyle.define([
  { tag: [t.keyword, t.controlKeyword, t.definitionKeyword, t.moduleKeyword, t.operatorKeyword], color: "var(--lg-code-keyword)" },
  { tag: [t.bool, t.null, t.atom], color: "var(--lg-code-atom)" },
  { tag: t.self, color: "var(--lg-code-self)" },
  { tag: [t.string, t.special(t.string)], color: "var(--lg-code-string)" },
  { tag: t.number, color: "var(--lg-code-number)" },
  { tag: t.comment, color: "var(--lg-code-comment)" },
  // Definition names only. Call names stay in the text colour: the grammar
  // does not know localized keywords, so it reads `saludar(nombre)` after
  // `definir` as a call, and a call colour would sit inside the definition
  // colour the localized layer gives that name.
  { tag: t.function(t.definition(t.variableName)), color: "var(--lg-code-function)" },
  { tag: [t.className, t.definition(t.className)], color: "var(--lg-code-class)" },
  { tag: [t.punctuation, t.paren, t.squareBracket, t.brace, t.separator], color: "var(--lg-code-punctuation)" },
  // Plain names and operators take the editor's text colour by inheritance;
  // styling them here would add spans the localized layer does not mirror.
]);

const surface = EditorView.theme({
  "&": { backgroundColor: "var(--lg-code-bg)", color: "var(--lg-code-fg)" },
  ".cm-content": { caretColor: "var(--lg-code-fg)" },
  ".cm-cursor, .cm-dropCursor": { borderLeftColor: "var(--lg-code-fg)" },
  ".cm-gutters": {
    backgroundColor: "var(--lg-code-bg)",
    color: "var(--lg-code-comment)",
    borderRight: "1px solid var(--sl-color-gray-5)",
  },
  ".cm-activeLine, .cm-activeLineGutter": { backgroundColor: "rgba(127, 127, 127, 0.1)" },
  "&.cm-focused > .cm-scroller > .cm-selectionLayer .cm-selectionBackground, .cm-selectionBackground, ::selection": {
    backgroundColor: "rgba(130, 170, 255, 0.3)",
  },
});

import { editorDirection, type TextDirection } from "./direction";
import { siteTheme } from "./theme";

export interface PlaygroundEditor {
  /** Current editor contents (the localized source to translate + run). */
  getDoc(): string;
  /** Replace the whole document, e.g. when the language seed changes. */
  setDoc(text: string): void;
  /** Switch the base text direction, e.g. when the language changes. */
  setDirection(direction: TextDirection): void;
  focus(): void;
  destroy(): void;
}

export interface MountOptions {
  parent: HTMLElement;
  doc: string;
  /** Base text direction of the buffer. Defaults to left-to-right. */
  direction?: TextDirection;
  /** Invoked on Mod-Enter (Cmd/Ctrl-Enter) so the page can trigger a Run. */
  onRun?: () => void;
  /** Invoked whenever the document changes (typing or setDoc). */
  onChange?: () => void;
  /** Additional extensions, e.g. the localized highlight layer. */
  extensions?: Extension[];
}

export function mountEditor({
  parent,
  doc,
  direction = "ltr",
  onRun,
  onChange,
  extensions = [],
}: MountOptions): PlaygroundEditor {
  const baseDirection = editorDirection(direction);
  const theme = siteTheme();
  // Highest precedence: basicSetup's default keymap also binds Mod-Enter (to
  // insert a blank line), and it would otherwise win.
  const runKey = Prec.highest(keymap.of([
    {
      key: "Mod-Enter",
      preventDefault: true,
      run: () => {
        onRun?.();
        return true;
      },
    },
  ]));

  const changeListener = EditorView.updateListener.of((update) => {
    if (update.docChanged) onChange?.();
  });

  const view = new EditorView({
    parent,
    state: EditorState.create({
      doc,
      extensions: [
        basicSetup,
        python(),
        syntaxHighlighting(palette),
        surface,
        runKey,
        changeListener,
        EditorState.tabSize.of(4),
        baseDirection.extension,
        theme.extension,
        EditorView.theme({
          "&": { fontSize: "0.9rem", borderRadius: "0.5rem" },
          "&.cm-focused": { outline: "2px solid var(--sl-color-accent)" },
          ".cm-scroller": { fontFamily: "var(--__sl-font-mono, ui-monospace, monospace)" },
        }),
        ...extensions,
      ],
    }),
  });

  const stopFollowingTheme = theme.follow(view);

  return {
    getDoc: () => view.state.doc.toString(),
    setDoc: (text: string) =>
      view.dispatch({
        changes: { from: 0, to: view.state.doc.length, insert: text },
      }),
    setDirection: (next: TextDirection) => baseDirection.set(view, next),
    focus: () => view.focus(),
    destroy: () => {
      stopFollowingTheme();
      view.destroy();
    },
  };
}
