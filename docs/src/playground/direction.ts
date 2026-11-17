// Base text direction for the playground, driven by language metadata.
//
// A language is right-to-left when the language registry says so: the `rtl`
// flag that generate_snippets.py copies into snippet-langs.json. Nothing here
// names a language, so a pack that ships with `rtl: true` is laid out
// right-to-left without a code change.
//
// This is container-level direction only: the editor, the output and the
// surrounding controls take one base direction, and the browser's bidi
// algorithm orders the runs inside each line. Neutral punctuation between a
// right-to-left run and a left-to-right run can therefore reorder visually;
// per-token isolation is a separate layer and is not applied here.
//
// The module has no dependency on the page: an embedded runner or another
// editor host can import it as is.

import { Compartment, type Extension } from "@codemirror/state";
import { EditorView } from "@codemirror/view";

export type TextDirection = "ltr" | "rtl";

/** The slice of language metadata that decides direction. */
export interface DirectionMeta {
  rtl?: boolean;
}

/** Resolve a language's base direction from its metadata; unknown is LTR. */
export function directionOf(meta: DirectionMeta | null | undefined): TextDirection {
  return meta?.rtl === true ? "rtl" : "ltr";
}

// In a right-to-left editor the line-number gutter sits on the right, so its
// separator belongs on the gutter's left edge. CodeMirror's default style
// draws it on the right for a "before" gutter whatever the direction.
const gutterSeparator = EditorView.theme({
  '&[dir="rtl"] .cm-gutters.cm-gutters-before': {
    borderRightWidth: "0",
    borderLeftWidth: "1px",
  },
});

function directionAttributes(direction: TextDirection): Extension {
  // Always explicit, including "ltr": a left-to-right buffer must stay
  // left-to-right when the host page itself is right-to-left. The attribute
  // goes on the editor root, not only the content, so the gutter moves to the
  // start side with the text and CodeMirror's scroll margins stay correct.
  return EditorView.editorAttributes.of({ dir: direction });
}

export interface EditorDirection {
  /** Add to the editor's extensions. */
  extension: Extension;
  /** Switch the base direction of a mounted editor. */
  set(view: EditorView, direction: TextDirection): void;
}

/** A reconfigurable base direction for one editor instance. */
export function editorDirection(initial: TextDirection): EditorDirection {
  const compartment = new Compartment();
  let current = initial;
  return {
    extension: [gutterSeparator, compartment.of(directionAttributes(initial))],
    set(view, direction) {
      if (direction === current) return;
      current = direction;
      // The dispatch schedules a measure, which is where CodeMirror reads the
      // new direction from computed style.
      view.dispatch({ effects: compartment.reconfigure(directionAttributes(direction)) });
    },
  };
}
