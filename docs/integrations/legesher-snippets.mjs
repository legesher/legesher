import { cpSync, existsSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

// Populates Astro's codegen dir with the localized-snippet artifacts that
// SnippetLangSelect / LocalizedCode import (snippet-langs.json,
// legesher-snippets.css, snippets/*.json).
//
// Default: COPY the pre-generated artifacts committed under docs/generated/.
// This is pure Node, so the docs build needs no Python and runs in Vercel's
// Node-only build image. Refresh docs/generated/ with `pnpm generate:snippets`
// (needs Python 3.10+ with the pack deps) whenever the snippet sources or packs
// change, then commit it. Set LEGESHER_GENERATE_SNIPPETS=1 to regenerate inline
// as part of a build instead of copying.
export function legesherSnippets() {
  return {
    name: 'legesher-snippets',
    hooks: {
      'astro:config:setup': ({ createCodegenDir, logger }) => {
        const outDir = fileURLToPath(createCodegenDir());
        const committed = fileURLToPath(new URL('../generated/', import.meta.url));

        if (process.env.LEGESHER_GENERATE_SNIPPETS) {
          const script = fileURLToPath(new URL('../scripts/generate_snippets.py', import.meta.url));
          const snippets = fileURLToPath(new URL('../snippets/', import.meta.url));
          const python = process.env.LEGESHER_PYTHON ?? 'python3';
          logger.info(`regenerating localized snippets → ${committed}`);
          execFileSync(python, [script, '--snippets', snippets, '--out', committed], {
            stdio: 'inherit',
          });
        }

        if (!existsSync(committed)) {
          throw new Error(
            'docs/generated/ is missing — the docs build reads pre-generated snippet ' +
              'artifacts from there. Run `pnpm generate:snippets` (Python 3.10+ with the pack ' +
              'deps) and commit it, or set LEGESHER_GENERATE_SNIPPETS=1 to regenerate inline.',
          );
        }

        logger.info(`copying pre-generated snippets → ${outDir}`);
        cpSync(committed, outDir, { recursive: true });
      },
    },
  };
}
