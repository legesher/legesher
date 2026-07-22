import { expect, test } from '@playwright/test';

// The execution cases boot Pyodide, which fetches ~6 MB from the jsdelivr CDN on
// first run. They're on by default; set PLAYGROUND_SKIP_PYODIDE=1 to skip them
// (e.g. if the CDN is flaky in a given CI environment). The DOM/seed case below
// needs no network and always runs.
const RUN_PYODIDE = process.env.PLAYGROUND_SKIP_PYODIDE !== '1';

// Keywords/built-ins are translated; string literals are not — so the seeded
// program prints "Hello, world" whatever the editor language is. That makes it a
// clean end-to-end assertion: the output only appears if the pack translated the
// localized `print` back to English and the code executed.
const EXPECTED_STDOUT = 'Hello, world';

test('renders with the default Spanish seed and an RTL note', async ({ page }) => {
  await page.goto('/playground/');

  // Selector defaults to Spanish (fresh context has no saved preference).
  await expect(page.locator('#pg-lang')).toHaveValue('es');

  // Editor mounted and seeded with the Spanish hello-world variant.
  const content = page.locator('#pg-editor .cm-content');
  await expect(content).toContainText('definir');
  await expect(content).toContainText('imprimir');

  // RTL languages are announced as not-yet-editable.
  await expect(page.getByText(/coming soon/i)).toBeVisible();
});

test('runs the localized program and shows its stdout', async ({ page }) => {
  test.skip(!RUN_PYODIDE, 'Pyodide execution disabled via PLAYGROUND_SKIP_PYODIDE');
  test.setTimeout(120_000); // first-run Pyodide + wheels download

  await page.goto('/playground/');
  await expect(page.locator('#pg-lang')).toHaveValue('es');

  await page.locator('#pg-run').click();

  await expect(page.locator('#pg-output')).toContainText(EXPECTED_STDOUT, {
    timeout: 110_000,
  });
});

test('switching language runs that language’s pack', async ({ page }) => {
  test.skip(!RUN_PYODIDE, 'Pyodide execution disabled via PLAYGROUND_SKIP_PYODIDE');
  test.setTimeout(120_000);

  await page.goto('/playground/');

  await page.locator('#pg-lang').selectOption('fr');
  // Editor reseeds to the French variant (localized built-in `imprimer`).
  await expect(page.locator('#pg-editor .cm-content')).toContainText('imprimer');

  await page.locator('#pg-run').click();

  await expect(page.locator('#pg-output')).toContainText(EXPECTED_STDOUT, {
    timeout: 110_000,
  });
});
