import { defineConfig } from '@vscode/test-cli';

export default defineConfig({
    files: 'out/test/**/*.test.js',
    version: 'stable',
    workspaceFolder: './test/fixtures',
    mocha: {
        timeout: 20000,
        ui: 'bdd',
    },
});
