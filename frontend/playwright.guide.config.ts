import { defineConfig, devices } from "@playwright/test";

// Takes the portal guide's screenshots on the throwaway demo database (docs/guides/_source/guide_seed.py).
const guideEnv = {
  ...process.env,
  DJANGO_DEBUG: "true",
  PYTHONPATH: "docs/guides/_source",
  DJANGO_SETTINGS_MODULE: "guide_settings",
  DJANGO_CSRF_TRUSTED_ORIGINS: "http://127.0.0.1:4173",
} as Record<string, string>;

export default defineConfig({
  testDir: "./guide-capture",
  workers: 1,
  timeout: 300_000,
  expect: { timeout: 15_000 },
  reporter: "list",
  outputDir: "test-results/guide",
  use: {
    baseURL: "http://127.0.0.1:4173",
    actionTimeout: 15_000,
    navigationTimeout: 15_000,
    viewport: { width: 1440, height: 900 },
  },
  webServer: [
    {
      command:
        ".venv\\Scripts\\python.exe manage.py runserver 127.0.0.1:8010 --noreload",
      cwd: "..",
      env: guideEnv,
      url: "http://127.0.0.1:8010/health/",
      reuseExistingServer: false,
    },
    {
      command: "npm run dev -- --host 127.0.0.1 --port 4173",
      env: { ...process.env, BACKEND_URL: "http://127.0.0.1:8010" } as Record<
        string,
        string
      >,
      url: "http://127.0.0.1:4173",
      reuseExistingServer: false,
    },
  ],
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
