import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

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
        execFileSync(python, [script, '--snippets', snippets, '--out', outDir], {
          stdio: 'inherit',
        });
      },
    },
  };
}
