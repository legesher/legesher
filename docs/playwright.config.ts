import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  // --ignore-lock keeps `astro preview` in the foreground for Playwright to
  // manage. Without it, Astro 7 detaches the server when it is started by an
  // AI coding agent, and Playwright reports that the web server exited early.
  webServer: { command: 'pnpm preview --port 4321 --ignore-lock', port: 4321, reuseExistingServer: true },
  use: { baseURL: 'http://localhost:4321' },
});
