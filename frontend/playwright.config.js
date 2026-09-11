import { defineConfig } from '@playwright/test';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const frontendRoot = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(frontendRoot, '..');
const databasePath = path.join(os.tmpdir(), `pangeaworld-e2e-${process.pid}.db`).replaceAll('\\', '/');
const backendPython = process.platform === 'win32'
  ? path.join('backend', '.venv', 'Scripts', 'python.exe')
  : path.join('backend', '.venv', 'bin', 'python');

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  workers: 1,
  timeout: 300000,
  expect: { timeout: 25000 },
  use: {
    baseURL: 'http://127.0.0.1:5173',
    channel: 'chrome',
    headless: true,
    trace: 'retain-on-failure',
  },
  webServer: [
    {
      command: `"${backendPython}" -m uvicorn backend.main:app --host 127.0.0.1 --port 8001`,
      cwd: projectRoot,
      env: { ...process.env, PANGEAWORLD_DATABASE_URL: `sqlite:///${databasePath}` },
      url: 'http://127.0.0.1:8001/',
      reuseExistingServer: false,
      timeout: 120000,
    },
    {
      command: 'npm run dev -- --host 127.0.0.1 --port 5173',
      cwd: frontendRoot,
      env: { ...process.env, VITE_API_URL: 'http://127.0.0.1:8001' },
      url: 'http://127.0.0.1:5173/',
      reuseExistingServer: false,
      timeout: 120000,
    },
  ],
});
