import { readFileSync } from 'node:fs';
import { expect, test } from '@playwright/test';

// The Legesher Bridge API reference is generated from public/api/openapi.json at
// build time. Read the same file here, so an operation in the document without
// a page, or a reference page the document no longer backs, fails this suite.
type Operation = { operationId?: string; summary?: string };
const METHODS = ['get', 'put', 'post', 'delete', 'options', 'head', 'patch', 'trace'];
const spec = JSON.parse(readFileSync(new URL('../public/api/openapi.json', import.meta.url), 'utf-8')) as {
  servers: { url: string }[];
  paths: Record<string, Record<string, Operation>>;
};
const operations = Object.entries(spec.paths).flatMap(([path, item]) =>
  Object.entries(item)
    .filter(([method]) => METHODS.includes(method))
    .map(([method, op]) => ({ ...op, route: `${method.toUpperCase()} ${path}` })),
);

test('every operation has an id and a summary, and the only server is production', () => {
  expect(operations.length).toBeGreaterThan(0);
  for (const op of operations) {
    expect(op.operationId, `${op.route} has no operationId, so it has no stable page`).toBeTruthy();
    expect(op.summary, `${op.route} has no summary to title its page`).toBeTruthy();
  }
  expect(spec.servers.map((s) => s.url)).toEqual(['https://api.legesher.io']);
});

test('the reference links exactly the operations in the document', async ({ page }) => {
  await page.goto('/api/reference/');
  const hrefs = await page
    .locator('#starlight__sidebar a[href^="/api/reference/operations/"]')
    .evaluateAll((links) => links.map((link) => link.getAttribute('href') ?? ''));
  const linked = hrefs
    .filter((href) => !href.includes('/operations/tags/'))
    .map((href) => href.replace('/api/reference/operations/', '').replace(/\/$/, ''));
  expect(linked.sort()).toEqual(operations.map((op) => op.operationId as string).sort());
});

for (const op of operations.filter((op) => op.operationId)) {
  test(`reference page for ${op.operationId}`, async ({ page }) => {
    const response = await page.goto(`/api/reference/operations/${op.operationId}/`);
    expect(response?.status(), `no page for ${op.operationId}`).toBe(200);
    await expect(page.locator('h1')).toHaveText(op.summary as string);
  });
}

test('the OpenAPI document is served as-is', async ({ request }) => {
  const response = await request.get('/api/openapi.json');
  expect(response.status()).toBe(200);
  expect(await response.text()).toBe(readFileSync(new URL('../public/api/openapi.json', import.meta.url), 'utf-8'));
});

test('the guide pages and the reference share one sidebar group', async ({ page }) => {
  await page.goto('/api/');
  await expect(page.locator('h1')).toHaveText('Legesher Bridge API');
  const sidebar = page.locator('#starlight__sidebar');
  await expect(sidebar.getByText('Bridge API', { exact: true }).first()).toBeAttached();
  for (const label of ['Keys and sign-in', 'Errors and limits', 'Languages', 'Versioning', 'Endpoint reference']) {
    await expect(sidebar.getByText(label, { exact: true }).first()).toBeAttached();
  }
  await expect(sidebar.locator('a[href="/api/reference/"]')).toBeAttached();
});

for (const path of ['/es/api/', '/ar/api/']) {
  test(`${path} falls back to the English guide`, async ({ page }) => {
    const response = await page.goto(path);
    expect(response?.status()).toBe(200);
    await expect(page.locator('h1')).toHaveText('Legesher Bridge API');
  });
}
