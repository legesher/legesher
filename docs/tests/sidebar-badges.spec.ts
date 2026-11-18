import { expect, test } from '@playwright/test';

// A sidebar badge ("revisión", "مراجعة") sits a word space after its label.
// The space comes from the whitespace between the two spans in Starlight's
// markup, so an HTML minifier that drops it puts the badge against the label.
test.use({ viewport: { width: 1280, height: 800 } });

for (const path of ['/es/why-legesher/', '/ar/why-legesher/']) {
  test(`sidebar badges stand a word space clear of their labels on ${path}`, async ({ page }) => {
    await page.goto(path);
    const gaps = await page.locator('#starlight__sidebar a:has(.sl-badge)').evaluateAll((links) =>
      links.map((link) => {
        const label = link.querySelector(':scope > span:not(.sl-badge)')!.getBoundingClientRect();
        const badge = link.querySelector('.sl-badge')!.getBoundingClientRect();
        const rtl = getComputedStyle(link).direction === 'rtl';
        const between = link.querySelector(':scope > span:not(.sl-badge)')!.nextSibling;
        return {
          link: link.getAttribute('href'),
          gap: Math.round((rtl ? label.left - badge.right : badge.left - label.right) * 10) / 10,
          // Font-independent: a whitespace text node sits between the spans.
          spaced: between?.nodeType === Node.TEXT_NODE && between.textContent !== '' && between.textContent!.trim() === '',
        };
      }),
    );
    expect(gaps.length, 'no review badges left on this page; point this test at a page that has one').toBeGreaterThan(0);
    for (const { link, gap, spaced } of gaps) {
      expect(spaced, `whitespace between the label and the badge of ${link}`).toBe(true);
      expect(gap, `gap between the label and the badge of ${link}`).toBeGreaterThanOrEqual(6);
    }
  });
}
