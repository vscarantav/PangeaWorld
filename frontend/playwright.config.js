import { defineConfig } from '@playwright/test';
import { randomUUID } from 'node:crypto';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const frontendRoot = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(frontendRoot, '..');
// Process IDs are recycled on Windows. A per-run ID keeps a prior temporary
// database from turning a later registration into a false duplicate-user test
// failure.
const runId = process.env.E2E_RUN_ID || randomUUID();
const databasePath = path.join(os.tmpdir(), `pangeaworld-e2e-${runId}.db`).replaceAll('\\', '/');
const backendPort = Number(process.env.E2E_BACKEND_PORT || 8001);
const frontendPort = Number(process.env.E2E_FRONTEND_PORT || 5173);
const backendPython = process.platform === 'win32'
  ? path.join('backend', '.venv', 'Scripts', 'python.exe')
  : path.join('backend', '.venv', 'bin', 'python');

export default defineConfig({
  testDir: './e2e',
  outputDir: process.env.E2E_ARTIFACT_DIR || 'test-results',
  fullyParallel: false,
  workers: 1,
  timeout: 300000,
  expect: { timeout: 25000 },
  use: {
    baseURL: `http://127.0.0.1:${frontendPort}`,
    channel: 'chrome',
    headless: true,
    trace: 'retain-on-failure',
  },
  webServer: [
    {
      command: `"${backendPython}" -m uvicorn backend.main:app --host 127.0.0.1 --port ${backendPort}`,
      cwd: projectRoot,
      env: {
        ...process.env,
        PANGEAWORLD_DATABASE_URL: `sqlite:///${databasePath}`,
        PANGEAWORLD_CORS_ORIGINS: `http://127.0.0.1:${frontendPort}`,
      },
      url: `http://127.0.0.1:${backendPort}/`,
      reuseExistingServer: false,
      timeout: 120000,
    },
    {
      command: `npm run dev -- --host 127.0.0.1 --port ${frontendPort}`,
      cwd: frontendRoot,
      env: { ...process.env, VITE_API_URL: `http://127.0.0.1:${backendPort}` },
      url: `http://127.0.0.1:${frontendPort}/`,
      reuseExistingServer: false,
      timeout: 120000,
    },
  ],
});
