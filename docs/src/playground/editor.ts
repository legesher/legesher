// Stock CodeMirror 6 editor for the playground (CORE-1551).
//
// Uses only stock @codemirror/* packages, with no @legesher/* dependency
// (that npm scope is not published). The editor itself is grammar-agnostic
// about which natural language the keywords are in: python() gives
// structural/string/comment highlighting, and the pack-driven decoration
// layer (highlight.ts, passed in via `extensions`) colors localized keywords
// and names to match the English view. The base text direction comes from
// direction.ts and can be switched while the editor is mounted; theme.ts
// gives it the site's code palette, light and dark.

import { EditorView, keymap } from "@codemirror/view";
import { EditorState, Prec, type Extension } from "@codemirror/state";
import { basicSetup } from "codemirror";
import { python } from "@codemirror/lang-python";

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
        siteTheme,
        runKey,
        changeListener,
        EditorState.tabSize.of(4),
        baseDirection.extension,
        EditorView.theme({
          "&": { fontSize: "0.9rem", borderRadius: "0.5rem" },
          "&.cm-focused": { outline: "2px solid var(--sl-color-accent)" },
          ".cm-scroller": { fontFamily: "var(--__sl-font-mono, ui-monospace, monospace)" },
        }),
        ...extensions,
      ],
    }),
  });

  return {
    getDoc: () => view.state.doc.toString(),
    setDoc: (text: string) =>
      view.dispatch({
        changes: { from: 0, to: view.state.doc.length, insert: text },
      }),
    setDirection: (next: TextDirection) => baseDirection.set(view, next),
    focus: () => view.focus(),
    destroy: () => view.destroy(),
  };
}
