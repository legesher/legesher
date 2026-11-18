import { expect, test, type Page } from '@playwright/test';

// The site header carries one language selector: the page language. The code
// language is chosen on the localized sample itself, in its title bar. The two
// settings stay separate; only where the code picker sits changes.

const LOCALES = [
  { prefix: '', picker: 'Code language', copy: 'Copy' },
  { prefix: '/es', picker: 'Idioma del código', copy: 'Copiar' },
  { prefix: '/ar', picker: 'لغة الشيفرة', copy: 'نسخ' },
] as const;

const PAGES = ['/', '/getting-started/', '/why-legesher/', '/playground/'];

// Every select on the page that is not inside the localized sample.
const selectsOutsideSample = (page: Page) =>
  page.locator('select').evaluateAll((all) =>
    all.filter((s) => !s.closest('.lg-code')).map((s) => s.className || s.outerHTML.slice(0, 80)),
  );

const openMenu = (page: Page) =>
  page.locator('button[popovertarget="starlight__sidebar"], starlight-menu-button button').click();

for (const { prefix } of LOCALES) {
  test(`the header has one language selector, the page language (${prefix || '/'})`, async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto(`${prefix}/getting-started/`);
    // The theme select (dark, light, auto) is not a language selector.
    await expect(page.locator('header select:visible:not(starlight-theme-select select)')).toHaveCount(1);
    await expect(page.locator('header starlight-lang-select select')).toBeVisible();
  });

  test(`the phone menu has one language selector, the page language (${prefix || '/'})`, async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 800 });
    await page.goto(`${prefix}/getting-started/`);
    await openMenu(page);
    await expect(page.locator('#starlight__sidebar select:visible:not(starlight-theme-select select)')).toHaveCount(1);
    await expect(page.locator('#starlight__sidebar starlight-lang-select select')).toBeVisible();
  });
}

for (const path of PAGES) {
  test(`no code-language picker outside the sample on ${path}`, async ({ page }) => {
    await page.goto(path);
    const stray = (await selectsOutsideSample(page)).filter((c) => c.includes('lg-snippet-lang'));
    expect(stray, 'code-language pickers outside .lg-code').toEqual([]);
  });
}

for (const { prefix, picker, copy } of LOCALES) {
  test(`the sample's picker and copy button are named in the page language (${prefix || '/'})`, async ({ page }) => {
    await page.goto(`${prefix}/getting-started/`);
    const bar = page.locator('.lg-code .lg-code-bar');
    await expect(bar.locator('select.lg-snippet-lang')).toHaveAccessibleName(picker);
    await expect(bar.getByRole('button', { name: copy })).toBeVisible();
    await expect(bar).toContainText('Python');
  });

  for (const width of [320, 390]) {
    test(`the sample's title bar fits a ${width} px phone (${prefix || '/'})`, async ({ page }) => {
      await page.setViewportSize({ width, height: 800 });
      await page.goto(`${prefix}/getting-started/`);
      for (const part of ['select.lg-snippet-lang', '.lg-code-copy']) {
        const box = await page.locator(`.lg-code .lg-code-bar ${part}`).boundingBox();
        expect(box, `${part} is rendered`).not.toBeNull();
        expect(box!.x, `${part} starts inside the window`).toBeGreaterThanOrEqual(0);
        expect(box!.x + box!.width, `${part} ends inside the window`).toBeLessThanOrEqual(width);
      }
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
      expect(overflow, 'sideways scroll').toBeLessThanOrEqual(0);
      // One line: the picker and the copy button share a row with "Python".
      const { lowestTop, highestBottom } = await page.locator('.lg-code .lg-code-bar').evaluate((bar) => {
        const boxes = [...bar.children].map((c) => c.getBoundingClientRect());
        return {
          lowestTop: Math.max(...boxes.map((b) => b.top)),
          highestBottom: Math.min(...boxes.map((b) => b.bottom)),
        };
      });
      expect(lowestTop, 'every item in the title bar overlaps one row').toBeLessThan(highestBottom);
    });
  }
}

test('copy puts the code shown on the clipboard', async ({ page, context }) => {
  await context.grantPermissions(['clipboard-read', 'clipboard-write']);
  await page.goto('/getting-started/');
  await page.locator('.lg-code select.lg-snippet-lang').selectOption('es');
  await page.locator('.lg-code .lg-code-copy').click();
  const shown = await page.locator('.lg-code pre[data-lang="es"]').innerText();
  const copied = await page.evaluate(() => navigator.clipboard.readText());
  expect(copied.trim()).toBe(shown.trim());
  expect(copied).toContain('definir');
  await expect(page.locator('.lg-code .lg-code-copy')).toHaveAccessibleName('Copied');
});
