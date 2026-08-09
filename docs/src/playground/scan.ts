// Shared lexical helpers for the playground's localized-token layers
// (highlight.ts, identifiers.ts).

/** Identifier-shaped word runs, Unicode classes rather than ASCII \w. */
export const WORD_RE = /[\p{L}\p{Nl}_][\p{L}\p{N}\p{Mn}\p{Mc}_]*/gu;

/**
 * Leaf nodes whose contents are never code tokens. FormatString covers
 * f-string interpolations too — a small, accepted divergence.
 */
export const STRING_COMMENT_NODES: ReadonlySet<string> = new Set([
  "String",
  "FormatString",
  "Comment",
]);
