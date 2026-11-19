import { expect, test } from '@playwright/test';

// A sidebar badge ("revisión", "مراجعة") sits a word space after its label.
// The space comes from the whitespace between the two spans in Starlight's
// markup, so an HTML minifier that drops it puts the badge against the label.
test.use({ viewport: { width: 1280, height: 800 } });

for (const path of ['/es/why-legesher/', '/ar/why-legesher/']) {
  test(`sidebar badges stand a word space clear of their labels on ${path}`, async ({ page }) => {
    await page.goto(path);
    // Measure in the page's own font: a fallback font is wider and can wrap a label.
    await page.evaluate(() => document.fonts.ready);
    const gaps = await page.locator('#starlight__sidebar a:has(.sl-badge)').evaluateAll((links) =>
      links.map((link) => {
        const span = link.querySelector(':scope > span:not(.sl-badge)')!;
        // The label may wrap: measure from the end of its last line, not its box.
        const lines = span.getClientRects();
        const end = lines[lines.length - 1];
        const badge = link.querySelector('.sl-badge')!.getBoundingClientRect();
        const rtl = getComputedStyle(link).direction === 'rtl';
        const sameLine = badge.top < end.bottom && badge.bottom > end.top;
        const between = span.nextSibling;
        return {
          link: link.getAttribute('href'),
          // On a new line the line break separates the badge, and there is no gap to measure.
          gap: sameLine ? Math.round((rtl ? end.left - badge.right : badge.left - end.right) * 10) / 10 : null,
          // Font-independent: a whitespace text node sits between the spans.
          spaced: between?.nodeType === Node.TEXT_NODE && between.textContent !== '' && between.textContent!.trim() === '',
        };
      }),
    );
    expect(gaps.length, 'no review badges left on this page; point this test at a page that has one').toBeGreaterThan(0);
    for (const { link, gap, spaced } of gaps) {
      expect(spaced, `whitespace between the label and the badge of ${link}`).toBe(true);
      if (gap !== null) expect(gap, `gap between the label and the badge of ${link}`).toBeGreaterThanOrEqual(6);
    }
  });
}
