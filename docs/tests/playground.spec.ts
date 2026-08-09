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

// Node-side twin of src/playground/share.ts for building/reading share URLs.
const toBase64url = (text: string) => Buffer.from(text, 'utf8').toString('base64url');
const fromBase64url = (param: string) => Buffer.from(param, 'base64url').toString('utf8');

test('renders with the default Spanish seed and an RTL note', async ({ page }) => {
  await page.goto('/playground/');

  // Selector defaults to Spanish (fresh context has no saved preference).
  await expect(page.locator('#pg-lang')).toHaveValue('es');

  // Editor mounted and seeded with the Spanish hello-world variant, sample
  // identifiers localized via the pilot glossary.
  const content = page.locator('#pg-editor .cm-content');
  await expect(content).toContainText('definir');
  await expect(content).toContainText('imprimir');
  await expect(content).toContainText('saludar(nombre)');

  // RTL languages are announced as not-yet-editable.
  await expect(page.getByText(/coming soon/i)).toBeVisible();
});

test('share URL params reproduce language and code', async ({ page }) => {
  const code = 'imprimer("partagé")';
  await page.goto(`/playground/?code=${toBase64url(code)}&src=en&tgt=fr`);

  await expect(page.locator('#pg-lang')).toHaveValue('fr');
  await expect(page.locator('#pg-editor .cm-content')).toContainText('imprimer("partagé")');
});

test('invalid share params fall back silently to the default seed', async ({ page }) => {
  await page.goto('/playground/?code=!!!not-base64url&src=en&tgt=xx');

  await expect(page.locator('#pg-lang')).toHaveValue('es');
  await expect(page.locator('#pg-editor .cm-content')).toContainText('imprimir');
});

test('editing updates the share URL after the debounce', async ({ page }) => {
  await page.goto('/playground/');

  await page.locator('#pg-editor .cm-content').click();
  await page.keyboard.type('# compartido\n');

  await expect
    .poll(async () => {
      const search = await page.evaluate(() => location.search);
      const param = new URLSearchParams(search).get('code');
      return param ? fromBase64url(param) : '';
    })
    .toContain('# compartido');

  const search = await page.evaluate(() => location.search);
  const params = new URLSearchParams(search);
  expect(params.get('src')).toBe('en');
  expect(params.get('tgt')).toBe('es');
  expect(params.get('sample')).toBe('hello-world');
});

test('sample URL param restores the sample context', async ({ page }) => {
  await page.goto('/playground/?src=en&tgt=es&sample=classes');

  await expect(page.locator('#pg-sample')).toHaveValue('classes');
  await expect(page.locator('#pg-editor .cm-content')).toContainText('clase Animal');

  // Unknown slugs fall back silently to the first sample.
  await page.goto('/playground/?src=en&tgt=es&sample=not-a-sample');
  await expect(page.locator('#pg-sample')).toHaveValue('hello-world');
  await expect(page.locator('#pg-editor .cm-content')).toContainText('saludar');
});

test('copy link flushes the URL and copies it', async ({ page, context }) => {
  await context.grantPermissions(['clipboard-read', 'clipboard-write']);
  await page.goto('/playground/');

  await page.locator('#pg-share').click();
  await expect(page.locator('#pg-share')).toHaveText('Copied');

  const copied = await page.evaluate(() => navigator.clipboard.readText());
  expect(copied).toContain('code=');
  expect(copied).toContain('src=en');
  expect(copied).toContain('tgt=es');
});

test('localized keywords colorize exactly like English keywords', async ({ page }) => {
  // English view: 'def' is colored by the stock python() grammar.
  await page.goto('/playground/?src=en&tgt=en');
  const enKeyword = page.locator('#pg-editor .cm-content span', { hasText: 'def' }).first();
  await expect(enKeyword).toBeVisible();
  const enColor = await enKeyword.evaluate((el) => getComputedStyle(el).color);

  // Spanish view: 'definir' must pick up the SAME class via the pack layer.
  await page.goto('/playground/?src=en&tgt=es');
  const esKeyword = page.locator('#pg-editor .cm-content span', { hasText: 'definir' }).first();
  await expect(esKeyword).toBeVisible();
  expect(await esKeyword.evaluate((el) => getComputedStyle(el).color)).toBe(enColor);

  // And it is genuinely colored, not just wrapped.
  const plainColor = await page
    .locator('#pg-editor .cm-content')
    .evaluate((el) => getComputedStyle(el).color);
  expect(enColor).not.toBe(plainColor);

  // Non-Latin pack, same machinery: zh 'def' is 定义.
  await page.goto('/playground/?src=en&tgt=zh');
  const zhKeyword = page.locator('#pg-editor .cm-content span', { hasText: '定义' }).first();
  await expect(zhKeyword).toBeVisible();
  expect(await zhKeyword.evaluate((el) => getComputedStyle(el).color)).toBe(enColor);
});

test('definition and call names colorize exactly like English', async ({ page }) => {
  const content = '#pg-editor .cm-content';
  const colorOf = (locator: ReturnType<typeof page.locator>) =>
    locator.evaluate((el) => getComputedStyle(el).color);

  // English reference: hello-world has 'greet' at a def site and a call site,
  // and builtin 'print' in call position. Span counts capture whether this
  // theme styles call names at all — parity is the spec, not a fixed color.
  await page.goto('/playground/?src=en&tgt=en');
  await expect(page.locator(content)).toContainText('def greet');
  const enDef = page.locator(`${content} span`, { hasText: 'greet' }).first();
  await expect(enDef).toBeVisible();
  const enDefColor = await colorOf(enDef);
  const enGreetSpans = await page.locator(`${content} span`, { hasText: 'greet' }).count();
  const enPrintSpans = await page.locator(`${content} span`, { hasText: 'print' }).count();

  // Spanish: 'saludar' after 'definir' must compute the English def color,
  // and its call site (plus builtin 'imprimir') must mirror English exactly.
  await page.goto('/playground/?src=en&tgt=es');
  await expect(page.locator(content)).toContainText('definir saludar');
  const esDef = page.locator(`${content} span`, { hasText: 'saludar' }).first();
  await expect(esDef).toBeVisible();
  expect(await colorOf(esDef)).toBe(enDefColor);
  expect(await page.locator(`${content} span`, { hasText: 'saludar' }).count()).toBe(enGreetSpans);
  expect(await page.locator(`${content} span`, { hasText: 'imprimir' }).count()).toBe(enPrintSpans);

  // Non-Latin pack, no identifier glossary: 'greet' sits after 定义.
  await page.goto('/playground/?src=en&tgt=zh');
  const zhDef = page.locator(`${content} span`, { hasText: 'greet' }).first();
  await expect(zhDef).toBeVisible();
  expect(await colorOf(zhDef)).toBe(enDefColor);
});

test('highlighting never fires inside strings', async ({ page }) => {
  // 'imprimir' appears once as a builtin call and once inside a string.
  const code = 'imprimir("imprimir")';
  await page.goto(`/playground/?code=${toBase64url(code)}&src=en&tgt=es`);

  const line = page.locator('#pg-editor .cm-line').first();
  await expect(line).toContainText('imprimir("imprimir")');
  // The string token keeps its string styling: exactly one span wraps the
  // quoted part, and no decoration splits it.
  await expect(line.locator('span', { hasText: '"imprimir"' })).toHaveCount(1);
});

test('picking a sample updates the editor and the share URL', async ({ page }) => {
  await page.goto('/playground/');
  await expect(page.locator('#pg-sample')).toHaveValue('hello-world');

  await page.locator('#pg-sample').selectOption('loops');

  // The sample arrives in the selected language (engine-generated variant).
  const content = page.locator('#pg-editor .cm-content');
  await expect(content).toContainText('mientras');

  await expect
    .poll(async () => {
      const search = await page.evaluate(() => location.search);
      const param = new URLSearchParams(search).get('code');
      return param ? fromBase64url(param) : '';
    })
    .toContain('mientras');
  const search = await page.evaluate(() => location.search);
  const params = new URLSearchParams(search);
  expect(params.get('tgt')).toBe('es');
  expect(params.get('sample')).toBe('loops');

  // Switching language reseeds the same sample in the new language.
  await page.locator('#pg-lang').selectOption('en');
  await expect(content).toContainText('while total < 10');
});

test('languages without an identifier glossary keep English identifiers', async ({ page }) => {
  // Dutch has no pilot glossary: keywords localize, identifiers fall back.
  await page.goto('/playground/?src=en&tgt=nl');

  const content = page.locator('#pg-editor .cm-content');
  await expect(content).toContainText('greet');
  await expect(content).not.toContainText('saludar');
});

test('toggle is hidden when the editor language is English', async ({ page }) => {
  await page.goto('/playground/');

  await expect(page.locator('#pg-toggle')).toHaveText('Show English');
  await page.locator('#pg-lang').selectOption('en');
  await expect(page.locator('#pg-toggle')).toBeHidden();
});

test('toggle shows canonical English and restores the identical source', async ({ page }) => {
  test.skip(!RUN_PYODIDE, 'Pyodide translation disabled via PLAYGROUND_SKIP_PYODIDE');
  test.setTimeout(180_000); // first toggle boots Pyodide + wheels

  await page.goto('/playground/');
  await expect(page.locator('#pg-lang')).toHaveValue('es');

  // Full buffer text, newlines included (.cm-content textContent drops them).
  const editorText = () =>
    page.evaluate(() =>
      Array.from(document.querySelectorAll('#pg-editor .cm-line'))
        .map((line) => line.textContent)
        .join('\n'),
    );
  const original = await editorText();
  expect(original).toContain('definir');
  expect(original).toContain('saludar');

  await page.locator('#pg-toggle').click();
  // Keywords AND glossary identifiers arrive in English in the canonical view.
  await expect(page.locator('#pg-editor .cm-content')).toContainText('def greet(name)', {
    timeout: 110_000,
  });
  await expect(page.locator('#pg-editor .cm-content')).not.toContainText('saludar');
  await expect(page.locator('#pg-toggle')).toHaveText('Show Español');
  await expect(page.locator('#pg-view-note')).toBeVisible();

  await page.locator('#pg-toggle').click();
  await expect(page.locator('#pg-toggle')).toHaveText('Show English', { timeout: 30_000 });

  // Byte honesty: the untouched round trip restores the exact source.
  expect(await editorText()).toBe(original);
});

test('editing the canonical view translates the edits back to the source language', async ({ page }) => {
  test.skip(!RUN_PYODIDE, 'Pyodide translation disabled via PLAYGROUND_SKIP_PYODIDE');
  test.setTimeout(180_000);

  await page.goto('/playground/');
  await expect(page.locator('#pg-lang')).toHaveValue('es');

  await page.locator('#pg-toggle').click();
  await expect(page.locator('#pg-editor .cm-content')).toContainText('def greet', {
    timeout: 110_000,
  });

  // Replace the canonical buffer, then toggle back: the edit must arrive in
  // Spanish via the engine's forward (en→es) translation.
  await page.locator('#pg-editor .cm-content').click();
  await page.keyboard.press('ControlOrMeta+a');
  await page.keyboard.type('print(len("abc"))');
  await page.locator('#pg-toggle').click();

  await expect(page.locator('#pg-editor .cm-content')).toContainText('imprimir(longitud("abc"))', {
    timeout: 30_000,
  });
});

test('Classes sample canonical view is fully English, runs clean, restores bytes', async ({ page }) => {
  test.skip(!RUN_PYODIDE, 'Pyodide translation disabled via PLAYGROUND_SKIP_PYODIDE');
  test.setTimeout(180_000);

  await page.goto('/playground/');
  await expect(page.locator('#pg-lang')).toHaveValue('es');
  await page.locator('#pg-sample').selectOption('classes');

  const editorText = () =>
    page.evaluate(() =>
      Array.from(document.querySelectorAll('#pg-editor .cm-line'))
        .map((line) => line.textContent)
        .join('\n'),
    );
  const original = await editorText();
  expect(original).toContain('.hablar()');
  expect(original).toContain('mismo.nombre');

  await page.locator('#pg-toggle').click();
  const content = page.locator('#pg-editor .cm-content');
  // Attribute-position glossary words must come back to English too — a
  // mixed-language canonical view would raise AttributeError on Run.
  await expect(content).toContainText('.speak()', { timeout: 110_000 });
  await expect(content).toContainText('self.name');
  await expect(content).not.toContainText('hablar');
  await expect(content).not.toContainText('sonido');

  await page.locator('#pg-run').click();
  await expect(page.locator('#pg-output')).toContainText('Cat says meow', { timeout: 110_000 });
  await expect(page.locator('#pg-output')).toContainText('Rex says woof');

  await page.locator('#pg-toggle').click();
  await expect(page.locator('#pg-toggle')).toHaveText('Show English', { timeout: 30_000 });
  expect(await editorText()).toBe(original);
});

test('attribute calls added in the canonical view swap back to glossary terms', async ({ page }) => {
  test.skip(!RUN_PYODIDE, 'Pyodide translation disabled via PLAYGROUND_SKIP_PYODIDE');
  test.setTimeout(180_000);

  await page.goto('/playground/');
  await expect(page.locator('#pg-lang')).toHaveValue('es');
  await page.locator('#pg-sample').selectOption('classes');

  await page.locator('#pg-toggle').click();
  const content = page.locator('#pg-editor .cm-content');
  await expect(content).toContainText('.speak()', { timeout: 110_000 });

  // Append a new call at the end of the canonical buffer.
  await page.locator('#pg-editor .cm-content').click();
  await page.keyboard.press('ControlOrMeta+End');
  await page.keyboard.type('\nprint(Dog("Bo").speak())');

  await page.locator('#pg-toggle').click();
  await expect(content).toContainText('imprimir(Perro("Bo").hablar())', { timeout: 30_000 });
});

test('copy link in an edited canonical view shares the current code', async ({ page, context }) => {
  test.skip(!RUN_PYODIDE, 'Pyodide translation disabled via PLAYGROUND_SKIP_PYODIDE');
  test.setTimeout(180_000);
  await context.grantPermissions(['clipboard-read', 'clipboard-write']);

  await page.goto('/playground/');
  await expect(page.locator('#pg-lang')).toHaveValue('es');

  await page.locator('#pg-toggle').click();
  await expect(page.locator('#pg-editor .cm-content')).toContainText('def greet', {
    timeout: 110_000,
  });

  // Replace the canonical buffer, then copy: the URL must carry the
  // localized form of what is on screen NOW, not the pre-edit source.
  await page.locator('#pg-editor .cm-content').click();
  await page.keyboard.press('ControlOrMeta+a');
  await page.keyboard.type('print(2)');
  await page.locator('#pg-share').click();
  await expect(page.locator('#pg-share')).toHaveText('Copied', { timeout: 30_000 });

  const copied = await page.evaluate(() => navigator.clipboard.readText());
  const copiedParams = new URL(copied).searchParams;
  expect(fromBase64url(copiedParams.get('code')!)).toBe('imprimir(2)');
  expect(copiedParams.get('tgt')).toBe('es');

  // Toggling back restores exactly what the link carries.
  await page.locator('#pg-toggle').click();
  await expect(page.locator('#pg-editor .cm-content')).toContainText('imprimir(2)', {
    timeout: 30_000,
  });
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
