import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  webServer: { command: 'pnpm preview --port 4321', port: 4321, reuseExistingServer: true },
  use: { baseURL: 'http://localhost:4321' },
});
