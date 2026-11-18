import { expect, test, type Page } from '@playwright/test';

// Code on the docs site uses one palette: the colours the ordinary code blocks
// (Expressive Code's Night Owl themes) render with, kept as --lg-code-*
// variables in src/styles/custom.css. The localized sample and the playground
// editor read them. Every coloured token must stay readable (WCAG AA, 4.5:1)
// on every background it can sit on, overlays included.

const SCHEMES = ['light', 'dark'] as const;

// The palette as the code blocks render it. Pinned so a change is deliberate:
// update it together with custom.css if the code blocks' theme changes.
const PALETTE = {
  dark: {
    bg: '#23262f', fg: '#d6deeb', keyword: '#c792ea', builtin: '#c5e478', function: '#82aaff',
    class: '#ffcb8b', self: '#7fdbca', atom: '#ff6a83', string: '#ecc48d', number: '#f78c6c', comment: '#919f9f',
  },
  light: {
    bg: '#f6f7f9', fg: '#403f53', keyword: '#8844ae', builtin: '#3b61b0', function: '#3b61b0',
    class: '#111111', self: '#096e72', atom: '#a24848', string: '#984e4d', number: '#aa0982', comment: '#5f636f',
  },
} as const;

const hex = (rgb: string) =>
  '#' + rgb.match(/\d+/g)!.slice(0, 3).map((v) => Number(v).toString(16).padStart(2, '0')).join('');

// Contrast helpers, shipped into the page as strings.
const HELPERS = `
  const parse = (c) => c.match(/[\\d.]+/g).map(Number);
  const over = (top, under) => { const [r, g, b, a = 1] = parse(top); const [R, G, B] = parse(under); return 'rgb(' + [r * a + R * (1 - a), g * a + G * (1 - a), b * a + B * (1 - a)].map(Math.round).join(', ') + ')'; };
  const alpha = (c) => { const p = parse(c); return p.length < 4 ? 1 : p[3]; };
  // The background behind an element: translucent layers composited over the
  // first opaque ancestor (the page counts as white if none is found).
  const bgOf = (node) => { const layers = []; for (let e = node; e; e = e.parentElement) { const c = getComputedStyle(e).backgroundColor; if (alpha(c) === 0) continue; layers.push(c); if (alpha(c) === 1) break; } let bg = 'rgb(255, 255, 255)'; for (const c of layers.reverse()) bg = alpha(c) === 1 ? c : over(c, bg); return bg; };
  const lum = (c) => { const [r, g, b] = parse(c).slice(0, 3).map((v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; }); return 0.2126 * r + 0.7152 * g + 0.0722 * b; };
  const ratio = (a, b) => { const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p); return Math.round(((x + 0.05) / (y + 0.05)) * 100) / 100; };
`;

type Row = { text: string; color: string; bg: string; ratio: number };

// Every visible text run under `root`, with its colour and the background behind it.
const runs = (page: Page, root: string): Promise<Row[]> =>
  page.locator(root).first().evaluate((el, helpers) => {
    const h = new Function(`${helpers}; return { bgOf, ratio };`)();
    const out: Row[] = [];
    const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
    for (let n = walker.nextNode(); n; n = walker.nextNode()) {
      const host = n.parentElement!;
      if (!n.textContent!.trim() || !host.getClientRects().length) continue;
      const color = getComputedStyle(host).color;
      const bg = h.bgOf(host);
      out.push({ text: n.textContent!.trim().slice(0, 20), color, bg, ratio: h.ratio(color, bg) });
    }
    return out;
  }, HELPERS);

const unreadable = (rows: Row[]) => rows.filter((r) => r.ratio < 4.5).map((r) => `${r.text} ${r.color} on ${r.bg} = ${r.ratio}`);

for (const scheme of SCHEMES) {
  test(`the palette variables are the code blocks' palette (${scheme})`, async ({ page }) => {
    await page.emulateMedia({ colorScheme: scheme });
    await page.goto('/getting-started/');
    const vars = await page.evaluate((names) => {
      const cs = getComputedStyle(document.documentElement);
      // Expand #abc to #aabbcc: the build may shorten hex values.
      const full = (v: string) => (/^#[0-9a-f]{3}$/.test(v) ? '#' + [...v.slice(1)].map((c) => c + c).join('') : v);
      return Object.fromEntries(names.map((n) => [n, full(cs.getPropertyValue(`--lg-code-${n}`).trim().toLowerCase())]));
    }, Object.keys(PALETTE[scheme]));
    expect(vars).toEqual(PALETTE[scheme]);

    // Where the site's code blocks render the same kind of token, they agree.
    const ec = await page.locator('.expressive-code pre').evaluateAll((pres) => {
      const python = pres.find((p) => p.textContent!.includes('definir'))!;
      const colourOf = (pred: (t: string) => boolean) => {
        const span = [...python.querySelectorAll('.ec-line span')].find((s) => !s.children.length && pred(s.textContent!.trim()));
        return span ? getComputedStyle(span).color : null;
      };
      return {
        bg: getComputedStyle(python).backgroundColor,
        comment: colourOf((t) => t.startsWith('#')),
        number: colourOf((t) => /^\d+$/.test(t)),
        string: colourOf((t) => t.includes('joven')),
      };
    });
    expect(hex(ec.bg)).toBe(PALETTE[scheme].bg);
    expect(hex(ec.comment!)).toBe(PALETTE[scheme].comment);
    expect(hex(ec.number!)).toBe(PALETTE[scheme].number);
    expect(hex(ec.string!)).toBe(PALETTE[scheme].string);
  });

  test(`the localized sample's tokens take the palette (${scheme})`, async ({ page }) => {
    await page.emulateMedia({ colorScheme: scheme });
    await page.goto('/getting-started/');
    const got = await page.locator('.lg-code pre[data-lang="en"]').evaluate((pre) => {
      const c = (sel: string) => { const e = pre.querySelector(sel); return e ? getComputedStyle(e).color : null; };
      return {
        bg: getComputedStyle(pre).backgroundColor, fg: getComputedStyle(pre).color,
        keyword: c('.lg-keyword'), builtin: c('.lg-builtin'), exception: c('.lg-exception'), string: c('.lg-string'),
      };
    });
    const p = PALETTE[scheme];
    expect({ bg: hex(got.bg), fg: hex(got.fg), keyword: hex(got.keyword!), builtin: hex(got.builtin!), exception: hex(got.exception!), string: hex(got.string!) })
      .toEqual({ bg: p.bg, fg: p.fg, keyword: p.keyword, builtin: p.builtin, exception: p.builtin, string: p.string });
  });

  for (const prefix of ['', '/es', '/ar']) {
    test(`every token in the localized sample is readable (${scheme}, ${prefix || '/'})`, async ({ page }) => {
      await page.emulateMedia({ colorScheme: scheme });
      await page.goto(`${prefix}/getting-started/`);
      const rows = await runs(page, '.lg-code pre:visible');
      expect(rows.length).toBeGreaterThan(5);
      expect(unreadable(rows), 'tokens below 4.5:1').toEqual([]);
    });
  }

  test.describe(`playground editor (${scheme})`, () => {
    test.setTimeout(180_000);
    const content = '#pg-editor .cm-content';

    const open = async (page: Page, view: 'localized' | 'English') => {
      await page.emulateMedia({ colorScheme: scheme });
      await page.goto('/playground/');
      await expect(page.locator(content)).toContainText('imprimir', { timeout: 60_000 });
      if (view === 'English') {
        await page.locator('#pg-toggle').click();
        await expect(page.locator(content)).toContainText('print(', { timeout: 110_000 });
      }
    };

    // The middle of the first occurrence of `word` in the editor's text.
    const wordAt = async (page: Page, word: string) => {
      const p = await page.evaluate(({ word, content }) => {
        const w = document.createTreeWalker(document.querySelector(content)!, NodeFilter.SHOW_TEXT);
        for (let n = w.nextNode(); n; n = w.nextNode()) {
          const i = n.textContent!.indexOf(word);
          if (i < 0) continue;
          const r = document.createRange();
          r.setStart(n, i);
          r.setEnd(n, i + word.length);
          const b = r.getBoundingClientRect();
          return { x: b.x + b.width / 2, y: b.y + b.height / 2 };
        }
        return null;
      }, { word, content });
      expect(p, `"${word}" is in the editor`).not.toBeNull();
      return p!;
    };

    // Every token colour in the editor, against a background from `overlay`.
    const tokensOn = (page: Page, overlay: string) =>
      page.evaluate(({ overlay, helpers, content }) => {
        const h = new Function(`${helpers}; return { bgOf, ratio, over };`)();
        const boxes = [...document.querySelectorAll(overlay)];
        if (!boxes.length) return { found: 0, low: [] as string[] };
        const editorBg = h.bgOf(document.querySelector('#pg-editor .cm-editor'));
        const colours = new Set<string>([getComputedStyle(document.querySelector(content)!).color]);
        for (const s of document.querySelectorAll(`${content} span`)) colours.add(getComputedStyle(s).color);
        const low: string[] = [];
        for (const b of boxes) {
          const bg = h.over(getComputedStyle(b).backgroundColor, editorBg);
          for (const c of colours) { const r = h.ratio(c, bg); if (r < 4.5) low.push(`${c} on ${overlay} ${bg} = ${r}`); }
        }
        return { found: boxes.length, low: [...new Set(low)] };
      }, { overlay, helpers: HELPERS, content });

    for (const view of ['localized', 'English'] as const) {
      test(`every token is readable at rest (${view} view)`, async ({ page }) => {
        await open(page, view);
        await page.locator('h1').first().click();
        const rows = await runs(page, content);
        expect(rows.length).toBeGreaterThan(5);
        expect(unreadable(rows), 'tokens below 4.5:1').toEqual([]);
        expect(unreadable(await runs(page, '#pg-editor .cm-gutters')), 'line numbers below 4.5:1').toEqual([]);
      });
    }

    test('every token is readable on the selection, a word match and the active line', async ({ page }) => {
      await open(page, 'localized');
      const word = await wordAt(page, 'nombre');
      await page.mouse.dblclick(word.x, word.y);
      const match = await tokensOn(page, '.cm-selectionMatch');
      expect(match.found, 'other occurrences are marked').toBeGreaterThan(0);
      expect(match.low).toEqual([]);
      const line = await tokensOn(page, '.cm-activeLine');
      expect(line.low).toEqual([]);
      await page.keyboard.press('ControlOrMeta+a');
      const selection = await tokensOn(page, '.cm-selectionBackground');
      expect(selection.found).toBeGreaterThan(0);
      expect(selection.low).toEqual([]);
    });

    test('every token is readable on search matches, and the search panel is readable', async ({ page }) => {
      await open(page, 'localized');
      await page.locator(content).click();
      await page.keyboard.press('ControlOrMeta+f');
      await page.locator('.cm-search input[name=search]').fill('imprimir');
      // Enter moves to the next match; the current one is marked once selected.
      for (let i = 0; i < 3 && !(await page.locator('.cm-searchMatch-selected').count()); i++) await page.keyboard.press('Enter');
      const all = await tokensOn(page, '.cm-searchMatch');
      expect(all.found).toBeGreaterThan(1);
      expect(all.low).toEqual([]);
      const current = await tokensOn(page, '.cm-searchMatch-selected');
      expect(current.found).toBeGreaterThan(0);
      expect(current.low).toEqual([]);
      expect(unreadable(await runs(page, '.cm-panels')), 'search panel text below 4.5:1').toEqual([]);
      const close = await page.locator('.cm-search [name=close]').evaluate((b, helpers) => {
        const h = new Function(`${helpers}; return { bgOf, ratio };`)();
        return h.ratio(getComputedStyle(b).color, h.bgOf(b));
      }, HELPERS);
      expect(close, 'search panel close button').toBeGreaterThanOrEqual(4.5);
    });

    test('every token is readable on a matching bracket', async ({ page }) => {
      await open(page, 'localized');
      const word = await wordAt(page, 'nombre');
      await page.mouse.click(word.x, word.y);
      await page.keyboard.press('End');
      await page.keyboard.press('ArrowLeft');
      const bracket = await tokensOn(page, '.cm-matchingBracket');
      expect(bracket.found).toBeGreaterThan(0);
      expect(bracket.low).toEqual([]);
    });
  });

  test(`review badges are one soft amber label in the text font (${scheme})`, async ({ page }) => {
    await page.emulateMedia({ colorScheme: scheme });
    await page.goto('/ar/why-legesher/');
    const badges = await page.locator('#starlight__sidebar .sl-badge').evaluateAll((all, helpers) => {
      const h = new Function(`${helpers}; return { bgOf, ratio };`)();
      return all.map((b) => {
        const cs = getComputedStyle(b);
        return { font: cs.fontFamily, spacing: cs.letterSpacing, look: `${cs.backgroundColor}|${cs.borderColor}|${cs.color}`, ratio: h.ratio(cs.color, h.bgOf(b)) };
      });
    }, HELPERS);
    expect(badges.length).toBeGreaterThan(1);
    for (const b of badges) {
      expect(b.font, 'badge font').not.toMatch(/mono/i);
      expect(['normal', '0px']).toContain(b.spacing);
      expect(b.ratio, 'badge text contrast').toBeGreaterThanOrEqual(4.5);
    }
    // The badge on the page you are reading looks like the others.
    expect([...new Set(badges.map((b) => b.look))], 'distinct badge looks').toHaveLength(1);
    const [bg] = badges[0].look.split('|');
    const [r, g, b] = bg.match(/\d+/g)!.map(Number);
    expect(r > b && g > b, `amber fill (${bg})`).toBe(true);
  });
}
