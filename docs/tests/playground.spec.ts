import { readdirSync, readFileSync } from 'node:fs';

import { expect, test, type Page } from '@playwright/test';

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

// Which languages are right-to-left, and every localized keyword used below,
// come from the generated artifacts the site itself reads: the registry's
// `rtl` flag and the shipped packs' own words. The two hand-written programs
// in RICH_SAMPLES are the exception: they supply the identifiers, strings and
// comments, in the two scripts that carry marks on every word.
type LangMeta = { code: string; native: string; name: string; rtl: boolean };
type SnippetArtifact = { variants: Record<string, { code: string; spans: [string, string][] }> };
const generated = (path: string) =>
  JSON.parse(readFileSync(new URL(`../generated/${path}`, import.meta.url), 'utf8'));
const LANGS = generated('snippet-langs.json') as LangMeta[];
const VENDORED = new Set(
  Object.keys(
    JSON.parse(readFileSync(new URL('../public/wheels/wheels-manifest.json', import.meta.url), 'utf8'))
      .packs,
  ),
);
const RTL_LANGS = LANGS.filter((l) => l.rtl);
const SNIPPET_SLUGS = readdirSync(new URL('../generated/snippets/', import.meta.url))
  .filter((name) => name.endsWith('.json'))
  .map((name) => name.replace(/\.json$/, ''));

/** English keyword/builtin → the pack's word, read off the generated variants. */
function packTerms(lang: string): Record<string, string> {
  const terms: Record<string, string> = {};
  for (const slug of SNIPPET_SLUGS) {
    const { variants } = generated(`snippets/${slug}.json`) as SnippetArtifact;
    const en = variants.en.spans;
    const localized = variants[lang].spans;
    expect(localized.length, `${slug}: ${lang} spans align with en`).toBe(en.length);
    en.forEach(([text], i) => {
      if (['keyword', 'builtin', 'exception'].includes(localized[i][1])) terms[text] = localized[i][0];
    });
  }
  return terms;
}

/**
 * Swap every whole-word occurrence of the listed English keywords for the
 * pack's words. It does not parse: the samples keep those words out of their
 * strings and comments.
 */
function localize(english: string, lang: string, words: string[]): string {
  const terms = packTerms(lang);
  let out = english;
  for (const word of words) {
    expect(terms[word], `${lang} pack word for '${word}'`).toBeTruthy();
    out = out.replace(new RegExp(`\\b${word}\\b`, 'g'), terms[word]);
  }
  return out.normalize('NFC');
}

/**
 * Open a playground URL and wait for the editor. The page mounts the editor
 * after it has loaded the language's highlight terms, which the load event
 * does not wait for.
 */
async function openPlayground(page: Page, url: string) {
  await page.goto(url);
  await expect(page.locator('#pg-editor .cm-content')).toBeVisible();
}

/** Full buffer text, newlines included (.cm-content textContent drops them). */
const editorText = (page: Page) =>
  page.evaluate(() =>
    Array.from(document.querySelectorAll('#pg-editor .cm-line'))
      .map((line) => line.textContent)
      .join('\n'),
  );

/**
 * Where a substring is painted: the bounding box of the text range inside the
 * first editor line that contains it. Layout, not DOM order, is what
 * right-to-left changes, so the direction assertions measure boxes.
 */
const paintedBox = (page: Page, text: string) =>
  page.evaluate((needle) => {
    for (const line of Array.from(document.querySelectorAll('#pg-editor .cm-line'))) {
      const content = line.textContent ?? '';
      const at = content.indexOf(needle);
      if (at < 0) continue;
      const walker = document.createTreeWalker(line, NodeFilter.SHOW_TEXT);
      const range = document.createRange();
      let seen = 0;
      let started = false;
      for (let node = walker.nextNode(); node; node = walker.nextNode()) {
        const length = node.textContent?.length ?? 0;
        if (!started && at < seen + length) {
          range.setStart(node, at - seen);
          started = true;
        }
        if (started && at + needle.length <= seen + length) {
          range.setEnd(node, at + needle.length - seen);
          const box = range.getBoundingClientRect();
          const lineBox = line.getBoundingClientRect();
          return { left: box.left, right: box.right, lineLeft: lineBox.left, lineRight: lineBox.right };
        }
        seen += length;
      }
    }
    throw new Error(`"${needle}" is not on any editor line`);
  }, text);

/** Where a substring of the program output is painted, and the output's own edges. */
const outputBox = (page: Page, text: string) =>
  page.evaluate((needle) => {
    const pre = document.querySelector('#pg-output');
    if (!pre) throw new Error('no output pane');
    const walker = document.createTreeWalker(pre, NodeFilter.SHOW_TEXT);
    const nodes: Text[] = [];
    for (let node = walker.nextNode(); node; node = walker.nextNode()) nodes.push(node as Text);
    const at = nodes.map((node) => node.data).join('').indexOf(needle);
    if (at < 0) throw new Error(`"${needle}" is not in the output`);
    const range = document.createRange();
    let seen = 0;
    for (const node of nodes) {
      const end = seen + node.data.length;
      if (at >= seen && at < end) range.setStart(node, at - seen);
      if (at + needle.length > seen && at + needle.length <= end) {
        range.setEnd(node, at + needle.length - seen);
        break;
      }
      seen = end;
    }
    const box = range.getBoundingClientRect();
    const edges = pre.getBoundingClientRect();
    return { left: box.left, right: box.right, outLeft: edges.left, outRight: edges.right };
  }, text.normalize('NFC'));

/** The layout facts that differ between a left-to-right and a right-to-left editor. */
const layout = (page: Page) =>
  page.evaluate(() => {
    const one = (selector: string) => {
      const el = document.querySelector(selector);
      if (!el) throw new Error(`missing ${selector}`);
      return el;
    };
    const content = one('#pg-editor .cm-content');
    const gutterEl = one('#pg-editor .cm-gutters');
    const gutter = gutterEl.getBoundingClientRect();
    const gutterStyle = getComputedStyle(gutterEl);
    const contentBox = content.getBoundingClientRect();
    const run = one('#pg-run').getBoundingClientRect();
    const lang = one('#pg-lang').getBoundingClientRect();
    return {
      editor: getComputedStyle(content).direction,
      output: getComputedStyle(one('#pg-output')).direction,
      controls: getComputedStyle(one('#pg-root .pg-toolbar')).direction,
      outputHeading: getComputedStyle(one('#pg-root .pg-output-head')).direction,
      gutterSide: gutter.left >= contentBox.right - 1 ? 'right' : 'left',
      // The gutter's separator faces the text, whichever side the gutter is on.
      gutterSeparator:
        parseFloat(gutterStyle.borderLeftWidth) > parseFloat(gutterStyle.borderRightWidth) ? 'left' : 'right',
      // In a mirrored toolbar the language picker sits to the right of Run.
      pickerSide: lang.left > run.left ? 'right' : 'left',
    };
  });

const RTL_LAYOUT = {
  editor: 'rtl',
  output: 'rtl',
  controls: 'rtl',
  outputHeading: 'rtl',
  gutterSide: 'right',
  gutterSeparator: 'left',
  pickerSide: 'right',
};
const LTR_LAYOUT = {
  editor: 'ltr',
  output: 'ltr',
  controls: 'ltr',
  outputHeading: 'ltr',
  gutterSide: 'left',
  gutterSeparator: 'right',
  pickerSide: 'left',
};

// Real right-to-left source: vocalised Arabic and pointed Hebrew identifiers
// (combining marks on every word), digits, a dotted path, strings and comments
// on the same lines as Latin text. Written in English keywords here and
// localized through the pack at run time by localize().
const RICH_SAMPLES: Record<string, { english: string; words: string[]; identifier: string; stdout: string[] }> = {
  ar: {
    english: [
      'import statistics',
      '',
      '# مُعَدَّل الدَّرَجَات: 3 أَرْقَام',
      'def مُعَدَّل(أَرْقَام):',
      '    return statistics.mean(أَرْقَام)',
      '',
      'دَرَجَات = [90, 85, 77]',
      'print("النَّتِيجَة:", مُعَدَّل(دَرَجَات))',
      'for عَدَد in range(3):',
      '    print(عَدَد + 10, "ok")',
      '',
    ].join('\n'),
    words: ['import', 'def', 'return', 'print', 'for', 'in', 'range'],
    identifier: 'مُعَدَّل',
    stdout: ['النَّتِيجَة: 84', '10 ok', '11 ok', '12 ok'],
  },
  he: {
    english: [
      'import statistics',
      '',
      '# מְמֻצָּע הַצִּיּוּנִים: 3 מִסְפָּרִים',
      'def מְמֻצָּע(מִסְפָּרִים):',
      '    return statistics.mean(מִסְפָּרִים)',
      '',
      'צִיּוּנִים = [90, 85, 77]',
      'print("תּוֹצָאָה:", מְמֻצָּע(צִיּוּנִים))',
      'for מִסְפָּר in range(3):',
      '    print(מִסְפָּר + 10, "ok")',
      '',
    ].join('\n'),
    words: ['import', 'def', 'return', 'print', 'for', 'in', 'range'],
    identifier: 'מְמֻצָּע',
    stdout: ['תּוֹצָאָה: 84', '10 ok', '11 ok', '12 ok'],
  },
};

test('renders with the default Spanish seed, laid out left to right', async ({ page }) => {
  await page.goto('/playground/');

  // Selector defaults to Spanish (fresh context has no saved preference).
  await expect(page.locator('#pg-lang')).toHaveValue('es');

  // Editor mounted and seeded with the Spanish hello-world variant, sample
  // identifiers localized via the pilot glossary.
  const content = page.locator('#pg-editor .cm-content');
  await expect(content).toContainText('definir');
  await expect(content).toContainText('imprimir');
  await expect(content).toContainText('saludar(nombre)');

  // Nothing announces right-to-left editing as missing any more.
  await expect(page.getByText(/coming soon/i)).toHaveCount(0);

  // A left-to-right language keeps the left-to-right layout it always had.
  expect(await layout(page)).toEqual(LTR_LAYOUT);
});

test('every right-to-left pack language is offered in the picker', async ({ page }) => {
  expect(RTL_LANGS.length, 'the registry marks at least one language right-to-left').toBeGreaterThan(0);
  await page.goto('/playground/');

  for (const lang of RTL_LANGS) {
    expect(VENDORED.has(lang.code), `${lang.code} has a vendored wheel`).toBe(true);
    await expect(page.locator(`#pg-lang option[value="${lang.code}"]`)).toHaveCount(1);
  }
});

for (const lang of RTL_LANGS) {
  test(`${lang.name} seed loads right-to-left and switches back to left-to-right`, async ({ page }) => {
    const { variants } = generated('snippets/hello-world.json') as SnippetArtifact;
    const keyword = packTerms(lang.code).def;

    await openPlayground(page, '/playground/');
    expect(await layout(page)).toEqual(LTR_LAYOUT);

    await page.locator('#pg-lang').selectOption(lang.code);
    // The seed is the pack's own variant, byte for byte.
    await expect.poll(() => editorText(page)).toBe(variants[lang.code].code);
    await expect.poll(() => layout(page)).toEqual(RTL_LAYOUT);

    // The first word of the first line is painted at the right edge of its
    // line, not the left: this is what a right-to-left base direction means.
    const box = await paintedBox(page, keyword);
    expect(box.lineRight - box.right).toBeLessThan(8);
    // The line keeps its padding next to the gutter, mirrored from the
    // left-to-right side, so the first letter does not touch the separator.
    expect(box.lineRight - box.right, 'room between the gutter and the first letter').toBeGreaterThanOrEqual(4);
    expect(box.left - box.lineLeft).toBeGreaterThan(100);

    // Back to a left-to-right language: everything returns.
    await page.locator('#pg-lang').selectOption('es');
    await expect.poll(() => layout(page)).toEqual(LTR_LAYOUT);
    const esBox = await paintedBox(page, 'definir');
    expect(esBox.left - esBox.lineLeft).toBeLessThan(8);
    expect(esBox.left - esBox.lineLeft, 'room between the gutter and the first letter').toBeGreaterThanOrEqual(4);
  });
}

for (const [code, sample] of Object.entries(RICH_SAMPLES)) {
  test(`${code}: marked identifiers, digits, a dotted path, strings and comments render right-to-left`, async ({
    page,
  }) => {
    const source = localize(sample.english, code, sample.words);
    const terms = packTerms(code);
    await openPlayground(page, `/playground/?code=${toBase64url(source)}&src=en&tgt=${code}`);

    // The NFC source comes back exactly: the combining marks survive the
    // share URL and the editor.
    await expect.poll(() => editorText(page)).toBe(source);
    expect(source).toContain(sample.identifier);
    expect(await layout(page)).toEqual(RTL_LAYOUT);

    // The definition line starts at the right edge with the pack's keyword,
    // and the marked identifier is painted to its left.
    const def = await paintedBox(page, terms.def);
    const name = await paintedBox(page, `${sample.identifier}(`);
    expect(def.lineRight - def.right).toBeLessThan(8);
    expect(name.right).toBeLessThanOrEqual(def.left + 1);

    // Indented lines are indented from the right.
    const ret = await paintedBox(page, terms.return);
    expect(ret.lineRight - ret.right).toBeGreaterThan(20);

    // A dotted Latin path keeps its own left-to-right order inside the line:
    // `statistics` is painted left of `mean`, and the whole path sits left of
    // the keyword that precedes it in the source.
    const module = await paintedBox(page, 'statistics.mean');
    const attribute = await paintedBox(page, 'mean');
    expect(module.left).toBeLessThan(attribute.left);
    expect(module.right).toBeLessThanOrEqual(ret.left + 1);

    // Digits inside a number keep their order (9 left of 0 in 90), while the
    // list reads right to left (90 is painted right of 77).
    const ninety = await paintedBox(page, '90');
    const nine = await paintedBox(page, '9');
    const seventySeven = await paintedBox(page, '77');
    expect(nine.right).toBeLessThan(ninety.right);
    expect(ninety.left).toBeGreaterThan(seventySeven.right);

    // The comment line also starts at the right edge.
    const comment = await paintedBox(page, '#');
    expect(comment.lineRight - comment.right).toBeLessThan(8);
  });
}

test('a left-to-right language stays left-to-right inside a right-to-left host', async ({ page }) => {
  // The Arabic docs locale is a right-to-left page. Spanish code inside it
  // must not take that direction.
  await openPlayground(page, '/ar/playground/?src=en&tgt=es');
  await expect(page.locator('html')).toHaveAttribute('dir', 'rtl');
  await expect(page.locator('#pg-editor .cm-content')).toContainText('definir');

  const leftToRight = async () => {
    const facts = await layout(page);
    expect(facts.editor).toBe('ltr');
    expect(facts.output).toBe('ltr');
    expect(facts.gutterSide).toBe('left');
    const box = await paintedBox(page, 'definir');
    expect(box.left - box.lineLeft).toBeLessThan(8);
    return facts;
  };
  await leftToRight();

  // Until the page is translated its body is marked left-to-right, which
  // would hide an editor that merely inherits. Make the playground's own
  // parent right-to-left, as a translated page or an embedding host would:
  // the editor and the output hold their direction, the controls follow.
  await page.evaluate(() => {
    const host = document.querySelector('#pg-root')?.parentElement;
    if (!host) throw new Error('playground has no parent');
    host.setAttribute('dir', 'rtl');
  });
  const hosted = await leftToRight();
  expect(hosted.controls).toBe('rtl');
  expect(hosted.pickerSide).toBe('right');
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

  const original = await editorText(page);
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
  expect(await editorText(page)).toBe(original);
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

  const original = await editorText(page);
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
  expect(await editorText(page)).toBe(original);
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

test('an Arabic sample loads, renders right-to-left and runs', async ({ page }) => {
  test.skip(!RUN_PYODIDE, 'Pyodide execution disabled via PLAYGROUND_SKIP_PYODIDE');
  test.setTimeout(180_000);
  const arabic = RTL_LANGS.find((l) => l.code === 'ar');
  expect(arabic, 'the registry marks Arabic right-to-left').toBeTruthy();

  await openPlayground(page, '/playground/');
  await page.locator('#pg-lang').selectOption('ar');
  await expect(page.locator('#pg-editor .cm-content')).toContainText(packTerms('ar').print);
  await expect.poll(() => layout(page)).toEqual(RTL_LAYOUT);

  await page.locator('#pg-run').click();
  const output = page.locator('#pg-output');
  await expect(output).toContainText(EXPECTED_STDOUT, { timeout: 110_000 });

  // The output line starts on the right, and its Latin text still reads in
  // order: the line is isolated with its own direction inside the output.
  await expect(output).toHaveAttribute('dir', 'rtl');
  const line = output.locator('span[dir="auto"]', { hasText: EXPECTED_STDOUT });
  await expect(line).toHaveCount(1);
  expect(await line.evaluate((el) => getComputedStyle(el).direction)).toBe('ltr');
  const boxes = await output.evaluate((el) => {
    const span = el.querySelector('span[dir="auto"]');
    if (!span) throw new Error('no output line');
    const text = span.getBoundingClientRect();
    const pre = el.getBoundingClientRect();
    return { gapRight: pre.right - text.right, gapLeft: text.left - pre.left };
  });
  expect(boxes.gapRight).toBeLessThan(30);
  expect(boxes.gapLeft).toBeGreaterThan(100);
});

test('every right-to-left pack language runs its hello world', async ({ page }) => {
  test.skip(!RUN_PYODIDE, 'Pyodide execution disabled via PLAYGROUND_SKIP_PYODIDE');
  test.setTimeout(240_000);

  await openPlayground(page, '/playground/');
  for (const lang of RTL_LANGS) {
    await page.locator('#pg-lang').selectOption(lang.code);
    await expect(page.locator('#pg-editor .cm-content')).toContainText(packTerms(lang.code).print);
    await expect(page.locator('#pg-output')).toHaveText('');

    await page.locator('#pg-run').click();
    await expect(page.locator('#pg-output'), `${lang.code} runs`).toContainText(EXPECTED_STDOUT, {
      timeout: 110_000,
    });
    await expect(page.locator('#pg-output .pg-error')).toHaveCount(0);
  }
});

for (const [code, sample] of Object.entries(RICH_SAMPLES)) {
  test(`${code}: marked identifiers, digits and a dotted path run and print right-to-left`, async ({ page }) => {
    test.skip(!RUN_PYODIDE, 'Pyodide execution disabled via PLAYGROUND_SKIP_PYODIDE');
    test.setTimeout(180_000);
    const source = localize(sample.english, code, sample.words);

    await openPlayground(page, `/playground/?code=${toBase64url(source)}&src=en&tgt=${code}`);
    await page.locator('#pg-run').click();

    const output = page.locator('#pg-output');
    await expect(output).toContainText(sample.stdout[sample.stdout.length - 1], { timeout: 110_000 });
    await expect(output.locator('.pg-error')).toHaveCount(0);
    const lines = (await output.textContent())?.split('\n').filter(Boolean);
    expect(lines).toEqual(sample.stdout);

    // A line that begins with right-to-left text resolves right-to-left.
    const first = output.locator('span').first();
    expect(await first.evaluate((el) => getComputedStyle(el).direction)).toBe('rtl');
  });
}

test('a traceback stays a left-to-right block inside a right-to-left output', async ({ page }) => {
  test.skip(!RUN_PYODIDE, 'Pyodide execution disabled via PLAYGROUND_SKIP_PYODIDE');
  test.setTimeout(180_000);
  // One line of output in vocalised Arabic, then a division by zero.
  const source = localize('print("قَبْل")\nprint(1 / 0)\n', 'ar', ['print']);

  await openPlayground(page, `/playground/?code=${toBase64url(source)}&src=en&tgt=ar`);
  await page.locator('#pg-run').click();

  const output = page.locator('#pg-output');
  await expect(output).toContainText('ZeroDivisionError', { timeout: 110_000 });
  await expect(output).toHaveAttribute('dir', 'rtl');

  const boxes = await output.evaluate((el) => {
    const pre = el.getBoundingClientRect();
    const edge = (node: Element) => {
      const range = document.createRange();
      range.selectNodeContents(node);
      const box = range.getBoundingClientRect();
      return { gapLeft: box.left - pre.left, gapRight: pre.right - box.right };
    };
    const [stdout] = Array.from(el.querySelectorAll('span[dir="auto"]'));
    const errors = Array.from(el.querySelectorAll('.pg-error'));
    return {
      stdout: edge(stdout),
      error: edge(errors[errors.length - 1]),
      errorDirection: getComputedStyle(errors[errors.length - 1]).direction,
    };
  });
  // The program's own Arabic line starts on the right.
  expect(boxes.stdout.gapRight).toBeLessThan(30);
  expect(boxes.stdout.gapLeft).toBeGreaterThan(100);
  // The traceback starts on the left, so its indentation still reads.
  expect(boxes.errorDirection).toBe('ltr');
  expect(boxes.error.gapLeft).toBeLessThan(30);
  expect(boxes.error.gapRight).toBeGreaterThan(100);
});

test('Show English turns an Arabic buffer left-to-right and back', async ({ page }) => {
  test.skip(!RUN_PYODIDE, 'Pyodide translation disabled via PLAYGROUND_SKIP_PYODIDE');
  test.setTimeout(180_000);

  await openPlayground(page, '/playground/?src=en&tgt=ar');
  const original = await editorText(page);
  expect(original).toContain(packTerms('ar').print);
  expect(await layout(page)).toEqual(RTL_LAYOUT);

  await page.locator('#pg-toggle').click();
  await expect(page.locator('#pg-editor .cm-content')).toContainText('def greet(name)', {
    timeout: 110_000,
  });
  // English text reads left to right; the output and the controls stay with
  // the selected language.
  const ENGLISH_VIEW = { ...RTL_LAYOUT, editor: 'ltr', gutterSide: 'left', gutterSeparator: 'right' };
  await expect.poll(() => layout(page)).toEqual(ENGLISH_VIEW);
  const def = await paintedBox(page, 'def');
  expect(def.left - def.lineLeft).toBeLessThan(8);

  await page.locator('#pg-toggle').click();
  await expect(page.locator('#pg-toggle')).toHaveText('Show English', { timeout: 30_000 });
  await expect.poll(() => layout(page)).toEqual(RTL_LAYOUT);
  expect(await editorText(page)).toBe(original);

  // Picking a sample from the English view reseeds the buffer in Arabic, so
  // the editor has to come back right-to-left with it.
  await page.locator('#pg-toggle').click();
  await expect.poll(() => layout(page), { timeout: 30_000 }).toEqual(ENGLISH_VIEW);
  await page.locator('#pg-sample').selectOption('loops');
  await expect(page.locator('#pg-editor .cm-content')).toContainText(packTerms('ar').while);
  await expect.poll(() => layout(page)).toEqual(RTL_LAYOUT);
});

test('right-to-left output keeps the indentation of each line', async ({ page }) => {
  test.skip(!RUN_PYODIDE, 'Pyodide execution disabled via PLAYGROUND_SKIP_PYODIDE');
  test.setTimeout(180_000);
  // A flush and an indented line of Latin text in an Arabic run.
  const source = localize('print("root")\nprint("        leaf")\n', 'ar', ['print']);
  await openPlayground(page, `/playground/?code=${toBase64url(source)}&src=en&tgt=ar`);
  await page.locator('#pg-run').click();

  const output = page.locator('#pg-output');
  await expect(output).toContainText('leaf', { timeout: 110_000 });
  await expect(output.locator('.pg-error')).toHaveCount(0);
  const root = await outputBox(page, 'root');
  const leaf = await outputBox(page, 'leaf');
  expect(root.outRight - root.right, 'the flush line starts at the right edge').toBeLessThan(30);
  expect(leaf.outRight - leaf.right - (root.outRight - root.right), 'eight spaces of indentation').toBeGreaterThan(40);
});

test('left-to-right output keeps the order the program printed', async ({ page }) => {
  test.skip(!RUN_PYODIDE, 'Pyodide execution disabled via PLAYGROUND_SKIP_PYODIDE');
  test.setTimeout(180_000);
  // In a Spanish run, a line that holds an Arabic word between Latin values,
  // and an indented line of Arabic. Both must read as they did before
  // right-to-left support: left to right, in the order printed.
  const source = localize('print(3, "عَرَبِي", "x")\nprint("        وَرَقَة")\n', 'es', ['print']);
  await openPlayground(page, `/playground/?code=${toBase64url(source)}&src=en&tgt=es`);
  await page.locator('#pg-run').click();

  const output = page.locator('#pg-output');
  await expect(output).toContainText('وَرَقَة'.normalize('NFC'), { timeout: 110_000 });
  await expect(output.locator('.pg-error')).toHaveCount(0);
  await expect(output).toHaveAttribute('dir', 'ltr');
  const three = await outputBox(page, '3');
  const x = await outputBox(page, 'x');
  expect(three.left - three.outLeft, 'the line starts at the left edge').toBeLessThan(30);
  expect(three.right, '3 is painted left of x, as printed').toBeLessThanOrEqual(x.left + 1);
  const leaf = await outputBox(page, 'وَرَقَة');
  expect(leaf.left - leaf.outLeft, 'eight spaces of indentation on the left').toBeGreaterThan(40);
});

/** The 1-based line the caret is on, read from the editor's current-line marker. */
const caretLine = (page: Page) =>
  page.evaluate(
    () =>
      Array.from(document.querySelectorAll('#pg-editor .cm-line')).findIndex((line) =>
        line.classList.contains('cm-activeLine'),
      ) + 1,
  );

/**
 * Contrast of the editor text that contains `needle` against what is painted
 * behind it (walking up through translucent layers), as WCAG computes it.
 */
const inkContrast = (page: Page, needle: string) =>
  page.evaluate((text) => {
    const rgb = (value: string) => (value.match(/[\d.]+/g) ?? []).map(Number);
    const luminance = ([r, g, b]: number[]) => {
      const channel = (c: number) => {
        const v = c / 255;
        return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4;
      };
      return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b);
    };
    const background = (el: Element) => {
      const layers: number[][] = [];
      for (let node: Element | null = el; node; node = node.parentElement) {
        const [r, g, b, a = 1] = rgb(getComputedStyle(node).backgroundColor);
        if (a > 0) layers.push([r, g, b, a]);
        if (a >= 1) break;
      }
      let base = [255, 255, 255];
      for (const [r, g, b, a] of layers.reverse()) {
        base = [r * a + base[0] * (1 - a), g * a + base[1] * (1 - a), b * a + base[2] * (1 - a)];
      }
      return base;
    };
    const holder = Array.from(document.querySelectorAll('#pg-editor .cm-line span')).find(
      (span) => span.textContent === text,
    );
    if (!holder) throw new Error(`no editor token "${text}"`);
    const [hi, lo] = [luminance(rgb(getComputedStyle(holder).color)), luminance(background(holder))].sort(
      (x, y) => y - x,
    );
    return (hi + 0.05) / (lo + 0.05);
  }, needle.normalize('NFC'));

for (const code of ['es', ...RTL_LANGS.map((l) => l.code)]) {
  test(`${code}: clicking a line puts the caret on that line`, async ({ page }) => {
    const rtl = RTL_LANGS.some((l) => l.code === code);
    await openPlayground(page, `/playground/?src=en&tgt=${code}&sample=loops`);
    const lines = page.locator('#pg-editor .cm-line');
    const count = await lines.count();
    expect(count).toBeGreaterThan(5);
    for (let i = 0; i < count; i++) {
      const box = await lines.nth(i).boundingBox();
      if (!box) throw new Error(`line ${i + 1} is not on screen`);
      // Inside the line's own box, a little in from its start edge.
      await page.mouse.click(rtl ? box.x + box.width - 20 : box.x + 20, box.y + box.height / 2);
      await expect.poll(() => caretLine(page), { message: `click on line ${i + 1}` }).toBe(i + 1);
    }
  });
}

test('Cmd or Ctrl and Enter runs the program without editing it', async ({ page }) => {
  test.skip(!RUN_PYODIDE, 'Pyodide execution disabled via PLAYGROUND_SKIP_PYODIDE');
  test.setTimeout(180_000);
  await openPlayground(page, '/playground/?src=en&tgt=ar');
  const before = await editorText(page);

  await page.locator('#pg-editor .cm-content').click();
  await page.keyboard.press('ControlOrMeta+Enter');

  await expect(page.locator('#pg-output')).toContainText(EXPECTED_STDOUT, { timeout: 110_000 });
  expect(await editorText(page), 'the shortcut runs; it does not insert a line').toBe(before);
});

test('errors and an empty run are styled apart from ordinary output', async ({ page }) => {
  test.skip(!RUN_PYODIDE, 'Pyodide execution disabled via PLAYGROUND_SKIP_PYODIDE');
  test.setTimeout(180_000);
  const output = page.locator('#pg-output');
  const style = (locator: ReturnType<typeof page.locator>) =>
    locator.evaluate((el) => {
      const s = getComputedStyle(el);
      return { color: s.color, weight: s.fontWeight, italic: s.fontStyle === 'italic' };
    });

  // A program that fails: the error lines take the error colour and weight.
  await openPlayground(page, `/playground/?code=${toBase64url(localize('print(1 / 0)\n', 'es', ['print']))}&src=en&tgt=es`);
  await page.locator('#pg-run').click();
  await expect(output).toContainText('ZeroDivisionError', { timeout: 110_000 });
  const plain = await style(output);
  const error = await style(output.locator('.pg-error').last());
  expect(error.color, 'error text has its own colour').not.toBe(plain.color);
  expect(Number(error.weight), 'error text is bold').toBeGreaterThanOrEqual(600);

  // A program that prints nothing: the placeholder is muted and italic.
  await openPlayground(page, `/playground/?code=${toBase64url('x = 1\n')}&src=en&tgt=es`);
  await page.locator('#pg-run').click();
  await expect(output).toContainText('(no output)', { timeout: 110_000 });
  const muted = await style(output.locator('.pg-muted'));
  expect(muted.italic, 'the placeholder is italic').toBe(true);
  expect(muted.color, 'the placeholder is muted').not.toBe(plain.color);
});

test('dark theme keeps the editor readable and follows a theme switch', async ({ page }) => {
  // Readable means at least 4.5:1, the minimum contrast for body text.
  const READABLE = 4.5;
  const terms = packTerms('ar');
  const colourOf = (token: string) =>
    page
      .locator('#pg-editor .cm-content span', { hasText: token })
      .first()
      .evaluate((el) => getComputedStyle(el).color);

  // English keyword colours in each theme, from the stock Python grammar.
  await openPlayground(page, '/playground/?src=en&tgt=en');
  const englishLight = await colourOf('def');
  await page.emulateMedia({ colorScheme: 'dark' });
  await openPlayground(page, '/playground/?src=en&tgt=en');
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
  const englishDark = await colourOf('def');
  expect(englishDark, 'dark theme has its own keyword colour').not.toBe(englishLight);

  await openPlayground(page, '/playground/?src=en&tgt=ar');
  // The first line carries the current-line band; check text on it and off it.
  expect(await caretLine(page)).toBe(1);
  for (const [what, token] of [
    ['keyword on the current line', terms.def],
    ['keyword on another line', terms.try],
    ['string', '"Please pass a string"'],
  ] as const) {
    expect(await inkContrast(page, token), what).toBeGreaterThanOrEqual(READABLE);
  }
  const gutter = await page.locator('#pg-editor .cm-gutters').evaluate((el) => getComputedStyle(el).backgroundColor);
  expect(gutter, 'the line-number column is not white').not.toBe('rgb(245, 245, 245)');
  // Localized keywords take exactly the colour English keywords have.
  expect(await colourOf(terms.def), 'localized keyword matches English in dark').toBe(englishDark);

  // Switching the site's theme with the editor mounted switches the editor,
  // localized keywords included.
  const picker = page.locator('starlight-theme-select select').first();
  await picker.selectOption('light');
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'light');
  await expect
    .poll(() => colourOf(terms.def), { message: 'localized keyword matches English after switching to light' })
    .toBe(englishLight);
  expect(await inkContrast(page, terms.def)).toBeGreaterThanOrEqual(READABLE);
  await picker.selectOption('dark');
  await expect
    .poll(() => colourOf(terms.def), { message: 'localized keyword matches English after switching back' })
    .toBe(englishDark);
});
