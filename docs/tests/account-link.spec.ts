import { readFileSync } from 'node:fs';
import { expect, test as base, type Page } from '@playwright/test';

// The site shows one link to the account app. Both links are in the static
// HTML with the sign-up one showing; an inline head script reads the sign-in
// marker cookie that the account app leaves on the parent domain and switches
// to the account one. The site loads no sign-in code and makes no request to
// do this, so these tests also hold with every other origin unreachable.

// A wide window, stated here so the tests that load the home page (which has
// no sidebar, so only the header placement) do not lean on a default.
base.use({ viewport: { width: 1280, height: 720 } });

const SIGN_UP = 'https://app.legesher.io/signup';
const ACCOUNT = 'https://app.legesher.io/';

// The marker: a timestamp while signed in, `0` after signing out. The account
// app writes a plain name and a per-instance name (the plain name plus a
// suffix). A per-instance marker, when there is one, decides.
const PLAIN = '__client_uat';
const SUFFIXED = '__client_uat_Ab3dE9xZ';
const OTHER_SUFFIXED = '__client_uat_Zx9Ed3bA';
const SIGNED_IN_AT = '1794873600';
const SIGNED_IN = { [PLAIN]: SIGNED_IN_AT, [SUFFIXED]: SIGNED_IN_AT };

type Labels = Record<string, { signedOut: string; signedIn: string }>;
// The registry the component renders from, so a new locale is covered here
// the moment it gets labels.
const LABELS: Labels = JSON.parse(
  readFileSync(new URL('../src/account/labels.json', import.meta.url), 'utf-8'),
);
const home = (lang: string) => (lang === 'en' ? '/' : `/${lang}/`);
const guide = (lang: string) => `${home(lang)}getting-started/`;

const test = base.extend<{ setMarkers: (markers: Record<string, string>) => Promise<void> }>({
  setMarkers: async ({ context, baseURL }, use) => {
    await use((markers) =>
      context.addCookies(Object.entries(markers).map(([name, value]) => ({ name, value, url: baseURL! }))),
    );
  },
});

const shown = (page: Page, state: 'signed-out' | 'signed-in') =>
  page.locator(`a[data-account-link="${state}"]:visible`);

async function expectSignedOut(page: Page) {
  await expect(shown(page, 'signed-out')).toHaveCount(1);
  await expect(shown(page, 'signed-in')).toHaveCount(0);
  await expect(page.locator('html')).not.toHaveAttribute('data-account');
}

async function expectSignedIn(page: Page) {
  await expect(shown(page, 'signed-in')).toHaveCount(1);
  await expect(shown(page, 'signed-out')).toHaveCount(0);
  await expect(page.locator('html')).toHaveAttribute('data-account', 'signed-in');
}

test('a reader with no marker gets the sign-up link', async ({ page }) => {
  await page.goto('/');
  await expectSignedOut(page);
  await expect(shown(page, 'signed-out')).toHaveText('Create an account');
  await expect(shown(page, 'signed-out')).toHaveAttribute('href', SIGN_UP);
});

test('a signed-in reader gets the account link', async ({ page, setMarkers }) => {
  await setMarkers(SIGNED_IN);
  await page.goto('/');
  await expectSignedIn(page);
  await expect(shown(page, 'signed-in')).toHaveText('Your account');
  await expect(shown(page, 'signed-in')).toHaveAttribute('href', ACCOUNT);
});

test('the plain marker alone counts as signed in', async ({ page, setMarkers }) => {
  await setMarkers({ [PLAIN]: SIGNED_IN_AT });
  await page.goto('/');
  await expectSignedIn(page);
});

test('the per-instance marker alone counts as signed in', async ({ page, setMarkers }) => {
  await setMarkers({ [SUFFIXED]: SIGNED_IN_AT });
  await page.goto('/');
  await expectSignedIn(page);
});

test('a marker of 0 means signed out', async ({ page, setMarkers }) => {
  await setMarkers({ [PLAIN]: '0', [SUFFIXED]: '0' });
  await page.goto('/');
  await expectSignedOut(page);
});

test('a per-instance marker of 0 wins over a stale plain marker', async ({ page, setMarkers }) => {
  await setMarkers({ [PLAIN]: SIGNED_IN_AT, [SUFFIXED]: '0' });
  await page.goto('/');
  await expectSignedOut(page);
});

test('a signed-in per-instance marker wins over a plain marker of 0', async ({ page, setMarkers }) => {
  await setMarkers({ [PLAIN]: '0', [SUFFIXED]: SIGNED_IN_AT });
  await page.goto('/');
  await expectSignedIn(page);
});

// The site does not know which instance suffix is current, so any signed-in
// per-instance marker counts, whichever order the browser lists them in.
for (const [first, second] of [
  [SUFFIXED, OTHER_SUFFIXED],
  [OTHER_SUFFIXED, SUFFIXED],
]) {
  test(`one signed-in per-instance marker is enough (${first} signed out)`, async ({ page, setMarkers }) => {
    await setMarkers({ [first]: '0', [second]: SIGNED_IN_AT });
    await page.goto('/');
    await expectSignedIn(page);
  });
}

test('a cookie that only starts like the marker is ignored', async ({ page, setMarkers }) => {
  await setMarkers({ [`${PLAIN}x`]: SIGNED_IN_AT, [`x${PLAIN}`]: SIGNED_IN_AT });
  await page.goto('/');
  await expectSignedOut(page);
});

// Anything but a plain positive whole number reads as signed out, and none of
// it may throw: a broken value must never cost the reader the page.
for (const value of ['abc', '-1', '1.5', '1e9', '0x10', '00', '%E0%A4%A', '1794873600x', '9'.repeat(40)]) {
  test(`a malformed marker (${JSON.stringify(value)}) reads as signed out`, async ({ page, setMarkers }) => {
    const errors: string[] = [];
    page.on('pageerror', (error) => errors.push(error.message));
    await setMarkers({ [PLAIN]: value, [SUFFIXED]: value });
    await page.goto('/');
    await expectSignedOut(page);
    expect(errors).toEqual([]);
  });
}

test.describe('without JavaScript', () => {
  test.use({ javaScriptEnabled: false });

  test('the sign-up link still shows, even to a signed-in reader', async ({ page, setMarkers }) => {
    await setMarkers(SIGNED_IN);
    await page.goto('/');
    await expect(shown(page, 'signed-out')).toHaveCount(1);
    await expect(shown(page, 'signed-in')).toHaveCount(0);
    await expect(shown(page, 'signed-out')).toHaveAttribute('href', SIGN_UP);
  });
});

// The sign-in provider is never contacted: with every origin but this site
// refused, the page renders, the link is right, and nothing was even asked for.
for (const path of ['/', '/getting-started/', '/privacy/', '/ar/']) {
  test(`${path} renders and reads the marker with every other origin unreachable`, async ({
    page,
    context,
    baseURL,
    setMarkers,
  }) => {
    const leaving: string[] = [];
    await context.route('**/*', (route) => {
      const url = new URL(route.request().url());
      if (url.origin === new URL(baseURL!).origin) return route.continue();
      leaving.push(url.origin);
      return route.abort();
    });
    await setMarkers(SIGNED_IN);
    await page.goto(path);
    await expect(page.locator('main h1')).toBeVisible();
    await expectSignedIn(page);
    await page.waitForLoadState('networkidle');
    expect(leaving).toEqual([]);
  });
}

test('the marker is read by an inline script in the head, before the page paints', async ({ page }) => {
  await page.goto('/');
  // Inline and blocking: an external, deferred or module script would run
  // after first paint and flash the wrong link.
  const readers = await page.evaluate(
    (name) =>
      [...document.head.querySelectorAll('script')]
        .filter((script) => (script.textContent ?? '').includes(name))
        .map((script) => script.getAttributeNames()),
    PLAIN,
  );
  expect(readers).toEqual([[]]);
});

test('the site sets no cookie of its own', async ({ page, context, setMarkers }) => {
  await setMarkers(SIGNED_IN);
  await page.goto('/');
  await expectSignedIn(page);
  const names = (await context.cookies()).map((cookie) => cookie.name).sort();
  expect(names).toEqual(Object.keys(SIGNED_IN).sort());
});

for (const [lang, labels] of Object.entries(LABELS)) {
  test(`${lang} pages label the sign-up link in the page language`, async ({ page }) => {
    await page.goto(home(lang));
    await expect(page.locator('html')).toHaveAttribute('lang', lang);
    await expect(shown(page, 'signed-out')).toHaveText(labels.signedOut);
  });

  test(`${lang} pages label the account link in the page language`, async ({ page, setMarkers }) => {
    await setMarkers(SIGNED_IN);
    await page.goto(home(lang));
    await expect(shown(page, 'signed-in')).toHaveText(labels.signedIn);
  });
}

test('the arabic labels are Arabic script on a right-to-left page', async ({ page }) => {
  await page.goto('/ar/');
  await expect(page.locator('html')).toHaveAttribute('dir', 'rtl');
  await expect(shown(page, 'signed-out')).toHaveText(/^[\p{Script=Arabic}\s]+$/u);
});

// Where the link sits on a page with a sidebar. The header bar has room for
// it only in a wide window; in anything narrower it sits under the sidebar,
// which is the menu on a phone. At every width exactly one link shows, whole
// and inside the window, and in the header bar it costs the site title
// nothing.
const WIDE = 1232;
const STATES = [
  ['signed-out', {}],
  ['signed-in', SIGNED_IN],
] as const;

/** How far the header's controls reach past the window edge, in pixels. */
const headerOverflow = (page: Page) =>
  page.evaluate(() => {
    const box = document.querySelector('header .right-group')!.getBoundingClientRect();
    return Math.round(Math.max(0, -box.left, box.right - window.innerWidth));
  });
const titleWidth = (page: Page) =>
  page.evaluate(() => Math.round(document.querySelector('header .title-wrapper')!.getBoundingClientRect().width));
const withoutLink = async (page: Page, measure: (page: Page) => Promise<number>) => {
  const style = await page.addStyleTag({ content: '.lg-account-slot { display: none !important; }' });
  const value = await measure(page);
  await style.evaluate((node) => node.remove());
  return value;
};

/** Opens the phone menu: a popover button from Starlight 0.42, a custom element before it. */
const openMenu = (page: Page) =>
  page.locator('button[popovertarget="starlight__sidebar"], starlight-menu-button button').click();

async function expectWholeAndInside(page: Page, state: 'signed-out' | 'signed-in') {
  const link = shown(page, state);
  await expect(link).toHaveCount(1);
  const box = (await link.boundingBox())!;
  const width = page.viewportSize()!.width;
  expect(box.x).toBeGreaterThanOrEqual(0);
  expect(box.x + box.width).toBeLessThanOrEqual(width);
  const other = state === 'signed-out' ? 'signed-in' : 'signed-out';
  await expect(shown(page, other)).toHaveCount(0);
}

for (const lang of Object.keys(LABELS)) {
  for (const [state, markers] of STATES) {
    for (const width of [WIDE, 1280, 1440]) {
      test(`${lang} ${state}: the link is in the header bar of a ${width}px window`, async ({ page, setMarkers }) => {
        await setMarkers(markers);
        await page.setViewportSize({ width, height: 720 });
        await page.goto(guide(lang));
        await expectWholeAndInside(page, state);
        await expect(page.locator('header').locator(`a[data-account-link="${state}"]:visible`)).toHaveCount(1);
        expect(await headerOverflow(page)).toBe(0);
        expect(await titleWidth(page)).toBe(await withoutLink(page, titleWidth));
      });
    }

    for (const width of [800, 900, 1000, 1100, WIDE - 1]) {
      test(`${lang} ${state}: the link is in the sidebar of a ${width}px window`, async ({ page, setMarkers }) => {
        await setMarkers(markers);
        await page.setViewportSize({ width, height: 720 });
        await page.goto(guide(lang));
        await expectWholeAndInside(page, state);
        await expect(page.locator('#starlight__sidebar').locator(`a[data-account-link="${state}"]:visible`)).toHaveCount(1);
      });
    }

    for (const width of [320, 360, 390]) {
      test(`${lang} ${state}: the link is in the menu of a ${width}px phone`, async ({ page, setMarkers }) => {
        await setMarkers(markers);
        await page.setViewportSize({ width, height: 844 });
        await page.goto(guide(lang));
        await expect(shown(page, state)).toHaveCount(0);
        await openMenu(page);
        await expectWholeAndInside(page, state);
        const sideways = await page
          .locator('#starlight__sidebar')
          .evaluate((pane) => pane.scrollWidth - pane.clientWidth);
        expect(sideways).toBe(0);
      });
    }
  }
}

// The pill has a border close in colour to the browser's focus ring, so a
// ring drawn against it reads as a thicker border. The ring must stand clear.
for (const lang of Object.keys(LABELS)) {
  test(`${lang} keyboard focus on the link draws a ring that stands clear of its border`, async ({ page }) => {
    await page.goto(guide(lang));
    const link = shown(page, 'signed-out');
    await expect(link).toHaveCount(1);
    for (let presses = 0; presses < 20; presses++) {
      await page.keyboard.press('Tab');
      if (await link.evaluate((el) => el === document.activeElement)) break;
    }
    const ring = await link.evaluate((el) => {
      const style = getComputedStyle(el);
      return { focusVisible: el.matches(':focus-visible'), style: style.outlineStyle, offset: parseFloat(style.outlineOffset) };
    });
    expect(ring.focusVisible).toBe(true);
    expect(ring.style).not.toBe('none');
    expect(ring.offset).toBeGreaterThanOrEqual(2);
  });
}

test('the privacy page says what the site reads', async ({ page }) => {
  await page.goto('/privacy/');
  const section = page.locator('main');
  await expect(section.getByRole('heading', { name: 'Sign-in state' })).toBeVisible();
  await expect(section).toContainText('sign-in cookie');
  await expect(section).toContainText('sets no cookie of its own');
});
