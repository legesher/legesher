// Dark theme for the playground editor, following the docs site's theme.
//
// CodeMirror's default highlight colours are made for a white background; on
// the site's dark background they fall well below readable contrast. This
// module adds a dark-only highlight style and dark surfaces (gutter, current
// line, selection), and switches them on when the site is dark.
//
// Light theme is left exactly as it was: a highlight style typed "dark" is
// only used while the editor's dark flag is on, and CodeMirror falls back to
// its default style otherwise. The colours are the site's own variables, so
// they follow its palette.
//
// The site marks its resolved theme on <html data-theme="light|dark"> and
// changes it when the reader picks a theme or the system preference changes;
// the editor follows that attribute while it is mounted.

import { HighlightStyle, syntaxHighlighting } from "@codemirror/language";
import { Compartment, type Extension } from "@codemirror/state";
import { EditorView } from "@codemirror/view";
import { tags } from "@lezer/highlight";

// Tag for tag the same list as CodeMirror's defaultHighlightStyle, so every
// token that has a colour in light theme has a readable one in dark.
const darkHighlightStyle = HighlightStyle.define(
  [
    { tag: tags.meta, color: "var(--sl-color-gray-2)" },
    { tag: tags.link, textDecoration: "underline" },
    { tag: tags.heading, textDecoration: "underline", fontWeight: "bold" },
    { tag: tags.emphasis, fontStyle: "italic" },
    { tag: tags.strong, fontWeight: "bold" },
    { tag: tags.strikethrough, textDecoration: "line-through" },
    { tag: tags.keyword, color: "var(--sl-color-purple-high)" },
    {
      tag: [tags.atom, tags.bool, tags.url, tags.contentSeparator, tags.labelName],
      color: "var(--sl-color-blue-high)",
    },
    { tag: [tags.literal, tags.inserted], color: "var(--sl-color-green)" },
    { tag: [tags.string, tags.deleted], color: "var(--sl-color-red-high)" },
    { tag: [tags.regexp, tags.escape, tags.special(tags.string)], color: "var(--sl-color-orange)" },
    { tag: tags.definition(tags.variableName), color: "var(--sl-color-blue-high)" },
    { tag: tags.local(tags.variableName), color: "var(--sl-color-purple-high)" },
    { tag: [tags.typeName, tags.namespace], color: "var(--sl-color-green-high)" },
    { tag: tags.className, color: "var(--sl-color-blue-high)" },
    { tag: [tags.special(tags.variableName), tags.macroName], color: "var(--sl-color-accent-high)" },
    { tag: tags.definition(tags.propertyName), color: "var(--sl-color-blue-high)" },
    { tag: tags.comment, color: "var(--sl-color-orange)" },
    { tag: tags.invalid, color: "var(--sl-color-red)" },
  ],
  { themeType: "dark" },
);

// Turning this theme on is what sets the editor's dark flag. Its surfaces use
// the site's greys: CodeMirror's own dark current-line tint is light enough
// to pull text on that line below readable contrast.
const darkSurfaces = EditorView.theme(
  {
    ".cm-gutters": {
      backgroundColor: "var(--sl-color-gray-6)",
      color: "var(--sl-color-gray-2)",
      borderColor: "var(--sl-color-gray-5)",
    },
    ".cm-activeLineGutter": {
      backgroundColor: "var(--sl-color-gray-5)",
      color: "var(--sl-color-white)",
    },
    ".cm-activeLine": { backgroundColor: "var(--sl-color-gray-6)" },
    "&.cm-focused > .cm-scroller > .cm-selectionLayer .cm-selectionBackground": {
      background: "var(--sl-color-accent-low)",
    },
  },
  { dark: true },
);

/** Is the site currently dark? */
function siteIsDark(root: HTMLElement): boolean {
  return root.dataset.theme === "dark";
}

export interface SiteTheme {
  /** Add to the editor's extensions. */
  extension: Extension;
  /** Follow the site's theme from now on; returns a function that stops. */
  follow(view: EditorView): () => void;
}

/** An editor theme that matches the site's light or dark theme. */
export function siteTheme(root: HTMLElement = document.documentElement): SiteTheme {
  const compartment = new Compartment();
  const surfaces = (dark: boolean) => (dark ? darkSurfaces : []);
  return {
    extension: [syntaxHighlighting(darkHighlightStyle), compartment.of(surfaces(siteIsDark(root)))],
    follow(view) {
      let dark = siteIsDark(root);
      const observer = new MutationObserver(() => {
        const next = siteIsDark(root);
        if (next === dark) return;
        dark = next;
        view.dispatch({ effects: compartment.reconfigure(surfaces(next)) });
      });
      observer.observe(root, { attributes: true, attributeFilter: ["data-theme"] });
      return () => observer.disconnect();
    },
  };
}
