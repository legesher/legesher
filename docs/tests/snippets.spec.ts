import { expect, test, type Page } from '@playwright/test';

// The code-language picker lives on the localized sample, not in the header.
const picker = (page: Page) => page.locator('.lg-code select.lg-snippet-lang');

test('picker persists across pages and reloads', async ({ page }) => {
  await page.goto('/getting-started/');
  await picker(page).selectOption('es');
  await expect(page.locator('.lg-code pre[data-lang="es"]')).toBeVisible();
  await expect(page.locator('.lg-code pre[data-lang="en"]')).toBeHidden();
  await page.goto('/');
  await page.goto('/getting-started/');
  await expect(page.locator('.lg-code pre[data-lang="es"]')).toBeVisible();
});

test('arabic variant renders rtl with isolated tokens', async ({ page }) => {
  await page.goto('/getting-started/');
  await picker(page).selectOption('ar');
  const pre = page.locator('.lg-code pre[data-lang="ar"]');
  await expect(pre).toBeVisible();
  await expect(pre).toHaveAttribute('dir', 'rtl');
  await expect(pre.locator('span.lg-keyword').first()).toHaveCSS('unicode-bidi', 'isolate');
});

test('english page starts in english without a stored pick', async ({ page }) => {
  await page.goto('/getting-started/');
  await expect(page.locator('.lg-code pre[data-lang="en"]')).toBeVisible();
  await expect(picker(page)).toHaveValue('en');
});

test('spanish page starts the code in spanish without a stored pick', async ({ page }) => {
  await page.goto('/es/getting-started/');
  await expect(page.locator('.lg-code pre[data-lang="es"]')).toBeVisible();
  await expect(page.locator('.lg-code pre[data-lang="en"]')).toBeHidden();
  await expect(picker(page)).toHaveValue('es');
});

test('arabic page starts the code in arabic, right to left, without a stored pick', async ({ page }) => {
  await page.goto('/ar/getting-started/');
  const pre = page.locator('.lg-code pre[data-lang="ar"]');
  await expect(pre).toBeVisible();
  await expect(pre).toHaveAttribute('dir', 'rtl');
  await expect(page.locator('.lg-code pre[data-lang="en"]')).toBeHidden();
  await expect(picker(page)).toHaveValue('ar');
});

test('a stored pick wins over the page language', async ({ page }) => {
  await page.goto('/getting-started/');
  await picker(page).selectOption('hi');
  await page.goto('/es/getting-started/');
  await expect(page.locator('.lg-code pre[data-lang="hi"]')).toBeVisible();
  await expect(page.locator('.lg-code pre[data-lang="es"]')).toBeHidden();
  await expect(picker(page)).toHaveValue('hi');
});

test('the picker switches the code on a localized page, and english sticks', async ({ page }) => {
  await page.goto('/es/getting-started/');
  await picker(page).selectOption('en');
  await expect(page.locator('.lg-code pre[data-lang="en"]')).toBeVisible();
  await expect(page.locator('.lg-code pre[data-lang="es"]')).toBeHidden();
  await page.reload();
  await expect(page.locator('.lg-code pre[data-lang="en"]')).toBeVisible();
  await expect(picker(page)).toHaveValue('en');
});

test('a stale stored pick falls back to the page language', async ({ page }) => {
  await page.addInitScript(() => localStorage.setItem('legesher-snippet-lang', 'xx'));
  await page.goto('/es/getting-started/');
  await expect(page.locator('.lg-code pre[data-lang="es"]')).toBeVisible();
  await expect(picker(page)).toHaveValue('es');
});

test('the picker still switches the code when storage is blocked', async ({ page }) => {
  await page.addInitScript(() => {
    Storage.prototype.setItem = () => { throw new Error('blocked'); };
  });
  await page.goto('/es/getting-started/');
  await picker(page).selectOption('hi');
  await expect(page.locator('.lg-code pre[data-lang="hi"]')).toBeVisible();
  await expect(page.locator('.lg-code pre[data-lang="es"]')).toBeHidden();
});

test('ar docs locale serves rtl chrome', async ({ page }) => {
  await page.goto('/ar/');
  await expect(page.locator('html')).toHaveAttribute('dir', 'rtl');
});
