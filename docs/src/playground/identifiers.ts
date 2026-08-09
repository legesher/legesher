// Sample identifier glossaries, client side (CORE-1696).
//
// The engine translates keywords/builtins only; sample identifiers are
// localized as a display layer (generated variants carry them, canonical
// sources stay English). This module is the toggle's half of that layer: a
// token-level bidirectional swap so the canonical view shows English
// identifiers and toggling back restores localized ones. Matching mirrors
// highlight.ts — Unicode word runs compared NFC, never inside strings or
// comments (via the python() parse tree). Attribute names ARE swapped:
// the generator substitutes glossary words for every NAME token including
// attribute position (es Classes carries `.hablar()`), so this layer must
// be symmetric or the canonical view ends up mixed-language and un-runnable.

import { pythonLanguage } from "@codemirror/lang-python";

import { STRING_COMMENT_NODES, WORD_RE } from "./scan";

/** {english: localized} → {localized: english} (validated injective). */
export function invertGlossary(glossary: Record<string, string>): Record<string, string> {
  return Object.fromEntries(Object.entries(glossary).map(([en, loc]) => [loc, en]));
}

export function swapIdentifiers(code: string, mapping: Record<string, string>): string {
  if (!Object.keys(mapping).length) return code;
  const tree = pythonLanguage.parser.parse(code);
  let out = "";
  let last = 0;
  for (const match of code.matchAll(WORD_RE)) {
    const target = mapping[match[0].normalize("NFC")];
    if (target === undefined) continue;
    const from = match.index;
    if (STRING_COMMENT_NODES.has(tree.resolveInner(from + 1, -1).name)) continue;
    out += code.slice(last, from) + target;
    last = from + match[0].length;
  }
  return out + code.slice(last);
}
