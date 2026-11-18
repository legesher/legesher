import { expect, test, type Page } from '@playwright/test';

// Code on the docs site uses one palette: the one the ordinary code blocks
// (Expressive Code's Night Owl, light and dark) already use. Every coloured
// token must stay readable (WCAG AA, 4.5:1) against the background it sits on.

const SCHEMES = ['light', 'dark'] as const;

// Every visible text run under `root` whose colour differs from nothing in
// particular: the run's colour, the first opaque background behind it, and a
// short sample of its text.
const runs = (page: Page, root: string) =>
  page.locator(root).first().evaluate((el) => {
    const parse = (c: string) => c.match(/[\d.]+/g)!.map(Number);
    const opaque = (c: string) => { const p = parse(c); return p.length < 4 || p[3] === 1; };
    const bgOf = (node: Element | null): string => {
      for (let e = node; e; e = e.parentElement) {
        const c = getComputedStyle(e).backgroundColor;
        if (opaque(c) && !/^rgba?\(0, 0, 0(, 0)?\)$/.test(c)) return c;
      }
      return 'rgb(255, 255, 255)';
    };
    const lum = (c: string) => {
      const [r, g, b] = parse(c).slice(0, 3).map((v) => {
        v /= 255;
        return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4;
      });
      return 0.2126 * r + 0.7152 * g + 0.0722 * b;
    };
    const ratio = (a: string, b: string) => {
      const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p);
      return (x + 0.05) / (y + 0.05);
    };
    const out: { text: string; color: string; bg: string; ratio: number }[] = [];
    const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
    for (let n = walker.nextNode(); n; n = walker.nextNode()) {
      const host = n.parentElement!;
      if (!n.textContent!.trim() || !host.getClientRects().length) continue;
      const color = getComputedStyle(host).color;
      const bg = bgOf(host);
      out.push({ text: n.textContent!.trim().slice(0, 20), color, bg, ratio: Math.round(ratio(color, bg) * 100) / 100 });
    }
    return out;
  });

const unreadable = (rows: { text: string; color: string; bg: string; ratio: number }[]) =>
  rows.filter((r) => r.ratio < 4.5).map((r) => `${r.text} ${r.color} on ${r.bg} = ${r.ratio}`);

for (const scheme of SCHEMES) {
  for (const prefix of ['', '/es', '/ar']) {
    test(`every token in the localized sample is readable (${scheme}, ${prefix || '/'})`, async ({ page }) => {
      await page.emulateMedia({ colorScheme: scheme });
      await page.goto(`${prefix}/getting-started/`);
      const rows = await runs(page, '.lg-code pre:visible');
      expect(rows.length).toBeGreaterThan(5);
      expect(unreadable(rows), 'tokens below 4.5:1').toEqual([]);
    });
  }

  test(`the localized sample matches the ordinary code blocks (${scheme})`, async ({ page }) => {
    await page.emulateMedia({ colorScheme: scheme });
    await page.goto('/getting-started/');
    const look = (sel: string) =>
      page.locator(sel).first().evaluate((pre) => ({
        background: getComputedStyle(pre).backgroundColor,
        text: getComputedStyle(pre.querySelector('code') ?? pre).color,
      }));
    expect(await look('.lg-code pre:visible')).toEqual(await look('.expressive-code pre'));
  });

  for (const toggleToEnglish of [false, true]) {
    test(`every token in the playground editor is readable (${scheme}, ${toggleToEnglish ? 'English view' : 'localized view'})`, async ({ page }) => {
      test.setTimeout(180_000);
      await page.emulateMedia({ colorScheme: scheme });
      await page.goto('/playground/');
      const content = page.locator('#pg-editor .cm-content');
      await expect(content).toContainText('imprimir', { timeout: 60_000 });
      if (toggleToEnglish) {
        await page.locator('#pg-toggle').click();
        await expect(content).toContainText('print(', { timeout: 110_000 });
      }
      // Leave the editor unfocused so no active-line or selection colour is measured.
      await page.locator('h1').first().click();
      const rows = await runs(page, '#pg-editor .cm-content');
      expect(rows.length).toBeGreaterThan(5);
      expect(unreadable(rows), 'tokens below 4.5:1').toEqual([]);
    });
  }

  test(`review badges read as one quiet label in the text font (${scheme})`, async ({ page }) => {
    await page.emulateMedia({ colorScheme: scheme });
    await page.goto('/ar/why-legesher/');
    const badges = await page.locator('#starlight__sidebar .sl-badge').evaluateAll((all) =>
      all.map((b) => {
        const cs = getComputedStyle(b);
        return { font: cs.fontFamily, spacing: cs.letterSpacing, bg: cs.backgroundColor, border: cs.borderColor, color: cs.color };
      }),
    );
    expect(badges.length).toBeGreaterThan(1);
    for (const b of badges) {
      expect(b.font, 'badge font').not.toMatch(/mono/i);
      expect(['normal', '0px']).toContain(b.spacing);
    }
    // The badge on the page you are reading looks like the others.
    const looks = new Set(badges.map((b) => `${b.bg}|${b.border}|${b.color}`));
    expect([...looks], 'distinct badge looks').toHaveLength(1);
    expect(unreadable(await runs(page, '#starlight__sidebar')), 'sidebar text, badges included, below 4.5:1').toEqual([]);
  });
}
