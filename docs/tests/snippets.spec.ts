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

test('english page starts in english without a stored pick', async ({ page }) => {
  await page.goto('/getting-started/');
  await expect(page.locator('.lg-code pre[data-lang="en"]')).toBeVisible();
  await expect(page.locator('select.lg-snippet-lang:visible')).toHaveValue('en');
});

test('spanish page starts the code in spanish without a stored pick', async ({ page }) => {
  await page.goto('/es/getting-started/');
  await expect(page.locator('.lg-code pre[data-lang="es"]')).toBeVisible();
  await expect(page.locator('.lg-code pre[data-lang="en"]')).toBeHidden();
  await expect(page.locator('select.lg-snippet-lang:visible')).toHaveValue('es');
});

test('arabic page starts the code in arabic, right to left, without a stored pick', async ({ page }) => {
  await page.goto('/ar/getting-started/');
  const pre = page.locator('.lg-code pre[data-lang="ar"]');
  await expect(pre).toBeVisible();
  await expect(pre).toHaveAttribute('dir', 'rtl');
  await expect(page.locator('.lg-code pre[data-lang="en"]')).toBeHidden();
  await expect(page.locator('select.lg-snippet-lang:visible')).toHaveValue('ar');
});

test('a stored pick wins over the page language', async ({ page }) => {
  await page.goto('/getting-started/');
  await page.locator('select.lg-snippet-lang:visible').selectOption('hi');
  await page.goto('/es/getting-started/');
  await expect(page.locator('.lg-code pre[data-lang="hi"]')).toBeVisible();
  await expect(page.locator('.lg-code pre[data-lang="es"]')).toBeHidden();
  await expect(page.locator('select.lg-snippet-lang:visible')).toHaveValue('hi');
});

test('the picker switches the code on a localized page, and english sticks', async ({ page }) => {
  await page.goto('/es/getting-started/');
  await page.locator('select.lg-snippet-lang:visible').selectOption('en');
  await expect(page.locator('.lg-code pre[data-lang="en"]')).toBeVisible();
  await expect(page.locator('.lg-code pre[data-lang="es"]')).toBeHidden();
  await page.reload();
  await expect(page.locator('.lg-code pre[data-lang="en"]')).toBeVisible();
  await expect(page.locator('select.lg-snippet-lang:visible')).toHaveValue('en');
});

test('ar docs locale serves rtl chrome', async ({ page }) => {
  await page.goto('/ar/');
  await expect(page.locator('html')).toHaveAttribute('dir', 'rtl');
});
