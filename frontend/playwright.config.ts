import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  timeout: 120_000,
  expect: { timeout: 15_000 },
  reporter: [['html', { open: 'never' }]],
  use: {
    baseURL: 'http://localhost',
    trace: 'on-first-retry',
  },
})
