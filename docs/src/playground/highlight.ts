// Pack-driven syntax highlighting for localized buffers (CORE-1696).
//
// @codemirror/lang-python only knows English keywords, so localized code
// renders almost unstyled. This layer decorates localized keywords, booleans
// and builtins with the SAME classes the active highlight style gives their
// English counterparts (via highlightingFor), so both toggle views colorize
// identically. Matching is Unicode-correct — \p{L}/\p{N} word runs compared
// NFC — and driven purely by generated pack data, zero per-language rules.
// The python() syntax tree is consulted so nothing fires inside strings,
// comments, or attribute names (English obj.print is unstyled too).
//
// Beyond token classes, it mirrors lezer-python's STRUCTURAL inference: the
// identifier after the pack's def/class keyword colors like an English
// definition name, and identifiers in call position color like English call
// names. The target tag compositions are derived empirically by parsing a
// tiny English probe and reading getStyleTags off its nodes — never guessed —
// so if the active theme leaves English call names plain, localized call
// names stay plain too. Parity with English is the contract.

import { pythonLanguage } from "@codemirror/lang-python";
import { highlightingFor, syntaxTree } from "@codemirror/language";
import { RangeSetBuilder } from "@codemirror/state";
import {
  Decoration,
  type DecorationSet,
  EditorView,
  ViewPlugin,
  type ViewUpdate,
} from "@codemirror/view";
import { getStyleTags, type Tag, tags } from "@lezer/highlight";

import { STRING_COMMENT_NODES, WORD_RE } from "./scan";

/** Localized token sets, one generated highlight-terms/<lang>.json each. */
export interface HighlightTerms {
  /** Keywords — colored like English keywords. */
  k: Set<string>;
  /** True/False — colored like English booleans. */
  a: Set<string>;
  /** Builtins + exceptions — colored like English call names. */
  b: Set<string>;
  /** Structural keywords by canonical key: the pack's def/class words. */
  s: Record<string, string>;
}

export function toTermSets(raw: {
  k: string[];
  a: string[];
  b: string[];
  s?: Record<string, string>;
}): HighlightTerms {
  return { k: new Set(raw.k), a: new Set(raw.a), b: new Set(raw.b), s: raw.s ?? {} };
}

// On top of the shared string/comment guards, PropertyName is excluded HERE
// (not in identifiers.ts): it keeps obj.metodo( matching English
// obj.method( for free — localized attribute names are real PropertyName
// nodes, so lezer already renders them exactly as it renders English ones.
const EXCLUDED_NODES = new Set([...STRING_COMMENT_NODES, "PropertyName"]);

// English probe: read the tag compositions lezer-python actually assigns at
// a function-definition name, a class-definition name, and a call name.
const PROBE = "def dn(x):\n    pass\n\nclass Kn:\n    pass\n\ncn(x)\n";
let probed: { def: readonly Tag[]; cls: readonly Tag[]; call: readonly Tag[] } | null = null;

function englishTags() {
  if (!probed) {
    const tree = pythonLanguage.parser.parse(PROBE);
    const at = (word: string): readonly Tag[] => {
      const node = tree.resolveInner(PROBE.indexOf(word) + 1, -1);
      return getStyleTags(node)?.tags ?? [];
    };
    probed = { def: at("dn"), cls: at("Kn"), call: at("cn") };
  }
  return probed;
}

export function localizedHighlight(getTerms: () => HighlightTerms | null) {
  return ViewPlugin.fromClass(
    class {
      decorations: DecorationSet;

      constructor(view: EditorView) {
        this.decorations = build(view, getTerms());
      }

      update(update: ViewUpdate) {
        const reparsed = syntaxTree(update.state) !== syntaxTree(update.startState);
        if (update.docChanged || update.viewportChanged || reparsed) {
          this.decorations = build(update.view, getTerms());
        }
      }
    },
    { decorations: (plugin) => plugin.decorations },
  );
}

/** Does an opening paren follow at `pos` (same line, whitespace skipped)? */
function callFollows(text: string, pos: number): boolean {
  while (pos < text.length && (text[pos] === " " || text[pos] === "\t")) pos++;
  return text[pos] === "(";
}

function build(view: EditorView, terms: HighlightTerms | null): DecorationSet {
  if (!terms) return Decoration.none;
  const probe = englishTags();
  const forTags = (t: readonly Tag[]) => (t.length ? highlightingFor(view.state, t) : null);
  const classes = {
    k: highlightingFor(view.state, [tags.keyword]),
    a: highlightingFor(view.state, [tags.bool]),
    b: highlightingFor(view.state, [tags.function(tags.variableName)]),
    def: forTags(probe.def),
    cls: forTags(probe.cls),
    call: forTags(probe.call),
  };
  const builder = new RangeSetBuilder<Decoration>();
  const tree = syntaxTree(view.state);
  for (const range of view.visibleRanges) {
    const text = view.state.doc.sliceString(range.from, range.to);
    // Which definition keyword (if any) the previous word was: the next
    // identifier is a definition name, exactly as lezer infers for English.
    let pending: "def" | "cls" | null = null;
    for (const match of text.matchAll(WORD_RE)) {
      const word = match[0].normalize("NFC");
      const from = range.from + match.index;
      if (EXCLUDED_NODES.has(tree.resolveInner(from + 1, -1).name)) continue;

      const kind = terms.k.has(word) ? "k" : terms.a.has(word) ? "a" : terms.b.has(word) ? "b" : null;
      let cls: string | null;
      if (pending && kind !== "k" && kind !== "a") {
        // Definition names win even over builtins: English `def print(`
        // colors as a definition name too.
        cls = classes[pending];
      } else if (kind) {
        cls = classes[kind];
      } else if (callFollows(text, match.index + match[0].length)) {
        cls = classes.call;
      } else {
        cls = null;
      }
      if (cls) builder.add(from, from + match[0].length, Decoration.mark({ class: cls }));

      pending = word === terms.s.def ? "def" : word === terms.s.class ? "cls" : null;
    }
  }
  return builder.finish();
}
