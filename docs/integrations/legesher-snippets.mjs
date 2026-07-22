import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

// Runs the localized-snippet generator (docs/scripts/generate_snippets.py) at
// both dev and build time via the astro:config:setup hook. The generator needs
// a Python 3.10+ interpreter that can import the workspace pack libraries
// (pyyaml + pydantic + packaging). Set LEGESHER_PYTHON to point at one; it
// defaults to `python3` on PATH (what the CI / Vercel install step provisions).
export function legesherSnippets() {
  return {
    name: 'legesher-snippets',
    hooks: {
      'astro:config:setup': ({ createCodegenDir, logger }) => {
        const outDir = fileURLToPath(createCodegenDir());
        const script = fileURLToPath(new URL('../scripts/generate_snippets.py', import.meta.url));
        const snippets = fileURLToPath(new URL('../snippets/', import.meta.url));
        const python = process.env.LEGESHER_PYTHON ?? 'python3';
        logger.info(`generating localized snippets → ${outDir}`);
        try {
          execFileSync(python, [script, '--snippets', snippets, '--out', outDir], {
            stdio: 'inherit',
          });
        } catch (err) {
          // The Python traceback already printed above (stdio: inherit); add an
          // actionable pointer so a broken interpreter/deps env reads clearly in
          // the build log instead of a bare "Command failed".
          logger.error(
            `snippet generation failed using "${python}". ` +
              'The generator needs Python 3.10+ with the pack deps: ' +
              '`pip install -r docs/scripts/requirements.txt`, or set ' +
              'LEGESHER_PYTHON to an interpreter that has them.',
          );
          throw err;
        }
      },
    },
  };
}
