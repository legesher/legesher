import { defineConfig } from '@vscode/test-cli';
import * as os from 'node:os';
import * as path from 'node:path';

// VS Code opens a unix domain socket under the user-data directory, and macOS
// caps socket paths at 103 characters. The default lands inside the package
// (…/libs/vs-code/.vscode-test/user-data/…), which already sits near the limit
// and blows past it from a git worktree, failing with EINVAL before any test
// runs. Anchor it in the system temp directory so the harness works regardless
// of how deep the checkout is.
const userDataDir = path.join(os.tmpdir(), 'legesher-vscode-test');

export default defineConfig({
    files: 'out/test/**/*.test.js',
    version: 'stable',
    workspaceFolder: './test/fixtures',
    launchArgs: ['--user-data-dir', userDataDir],
    mocha: {
        timeout: 20000,
        ui: 'bdd',
    },
});
