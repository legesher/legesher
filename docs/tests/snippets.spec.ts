import { expect, test } from '@playwright/test';

test('picker persists across pages and reloads', async ({ page }) => {
  await page.goto('/getting-started/');
  await page.locator('select.lg-snippet-lang:visible').selectOption('es');
  await expect(page.locator('.lg-code pre[data-lang="es"]')).toBeVisible();
  await expect(page.locator('.lg-code pre[data-lang="en"]')).toBeHidden();
  await page.goto('/');
  await page.goto('/getting-started/');
  await expect(page.locator('.lg-code pre[data-lang="es"]')).toBeVisible();
});

test('arabic variant renders rtl with isolated tokens', async ({ page }) => {
  await page.goto('/getting-started/');
  await page.locator('select.lg-snippet-lang:visible').selectOption('ar');
  const pre = page.locator('.lg-code pre[data-lang="ar"]');
  await expect(pre).toBeVisible();
  await expect(pre).toHaveAttribute('dir', 'rtl');
  await expect(pre.locator('span.lg-keyword').first()).toHaveCSS('unicode-bidi', 'isolate');
});

test('ar docs locale serves rtl chrome', async ({ page }) => {
  await page.goto('/ar/');
  await expect(page.locator('html')).toHaveAttribute('dir', 'rtl');
});
