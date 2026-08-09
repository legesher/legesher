// Stock CodeMirror 6 editor for the playground (CORE-1551).
//
// Deliberately LTR-only for v1 (RTL editing is CORE-1552). Uses only stock
// @codemirror/* packages — no @legesher/* dependency (the npm scope is
// unpublished, CORE-1381). The editor itself is grammar-agnostic about which
// natural language the keywords are in: python() gives structural/string/
// comment highlighting, and the pack-driven decoration layer (highlight.ts,
// passed in via `extensions`) colors localized keywords and names to match
// the English view.

import { EditorView, keymap } from "@codemirror/view";
import { EditorState, type Extension } from "@codemirror/state";
import { basicSetup } from "codemirror";
import { python } from "@codemirror/lang-python";

export interface PlaygroundEditor {
  /** Current editor contents (the localized source to translate + run). */
  getDoc(): string;
  /** Replace the whole document, e.g. when the language seed changes. */
  setDoc(text: string): void;
  focus(): void;
  destroy(): void;
}

export interface MountOptions {
  parent: HTMLElement;
  doc: string;
  /** Invoked on Mod-Enter (Cmd/Ctrl-Enter) so the page can trigger a Run. */
  onRun?: () => void;
  /** Invoked whenever the document changes (typing or setDoc). */
  onChange?: () => void;
  /** Additional extensions, e.g. the localized highlight layer. */
  extensions?: Extension[];
}

export function mountEditor({ parent, doc, onRun, onChange, extensions = [] }: MountOptions): PlaygroundEditor {
  const runKey = keymap.of([
    {
      key: "Mod-Enter",
      preventDefault: true,
      run: () => {
        onRun?.();
        return true;
      },
    },
  ]);

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
        runKey,
        changeListener,
        EditorState.tabSize.of(4),
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
    focus: () => view.focus(),
    destroy: () => view.destroy(),
  };
}
