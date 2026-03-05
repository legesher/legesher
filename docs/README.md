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

## Adding Content

- Add new pages as `.md` or `.mdx` files in `src/content/docs/`
- Update the sidebar in `astro.config.mjs` to include new pages
- Images go in `src/assets/` and are referenced with relative imports
- Run `pnpm build` to verify — Starlight will fail if any sidebar slug references a missing file
