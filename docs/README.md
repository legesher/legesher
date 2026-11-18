# Legesher Documentation

[![Built with Starlight](https://astro.badg.es/v2/built-with-starlight/tiny.svg)](https://starlight.astro.build)

**Site**: [docs.legesher.io](https://docs.legesher.io)
**Deployed via**: Vercel (static adapter)

This directory contains the official Legesher documentation site built with [Astro](https://astro.build) and [Starlight](https://starlight.astro.build).

## Project Structure

```text
docs/
├── public/                     # Static assets (favicon, CNAME)
├── src/
│   ├── assets/                 # Images (Peggy branding, screenshots)
│   └── content/
│       └── docs/               # Starlight site pages (.md / .mdx)
│           ├── index.mdx       # Homepage
│           ├── getting-started.md
│           ├── why-legesher.md
│           ├── privacy.md
│           └── reference/
│               └── supported-languages.md
├── astro.config.mjs            # Astro + Starlight configuration
├── package.json
└── tsconfig.json
```

**Site pages** live in `src/content/docs/` — each `.md` or `.mdx` file becomes a route.

**Developer reference docs** — see CORE-577 for the plan to add more pages to this site.

## Commands

All commands are run from the `docs/` directory:

| Command          | Action                                      |
| :--------------- | :------------------------------------------ |
| `pnpm install`   | Install dependencies                        |
| `pnpm dev`       | Start local dev server at `localhost:4321`   |
| `pnpm build`     | Build production site to `./dist/`           |
| `pnpm preview`   | Preview production build locally             |

## Account link

The site shows one link to the account app: "Create an account" for everyone, and "Your account" for a
reader who is signed in at app.legesher.io.

- Both links are in every page's static HTML (`src/components/AccountLink.astro`) and the sign-up link
  shows by default, so the page works without JavaScript and on preview deployments.
- An inline head script (`src/account/marker-script.mjs`) reads the sign-in marker cookie the account
  app leaves on legesher.io and marks `<html data-account="signed-in">`. The site loads no sign-in
  code, makes no request and sets no cookie for this. The privacy page describes it; keep the two in
  step.
- Labels per locale live in `src/account/labels.json`. A locale without labels fails the build.
- The link is in the header bar in a wide window (77rem and up) and under the sidebar in anything
  narrower, which is the menu on a phone. Pages without a sidebar (the home page and the 404 page)
  show it only in a wide window.
- A preview deployment or `localhost` cannot see the legesher.io cookie, so it always shows the sign-up
  link. To see the signed-in state locally, set a cookie named `__client_uat` to `1` for `localhost` in
  the browser's developer tools. `tests/account-link.spec.ts` covers both states.

## Adding Content

- Add new pages as `.md` or `.mdx` files in `src/content/docs/`
- Update the sidebar in `astro.config.mjs` to include new pages
- Images go in `src/assets/` and are referenced with relative imports
- Run `pnpm build` to verify — Starlight will fail if any sidebar slug references a missing file
