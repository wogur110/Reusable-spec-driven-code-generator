const { defineConfig } = require('@playwright/test');
const path = require('node:path');
process.env.PLAYWRIGHT_BROWSERS_PATH ||= '/tmp/reusable-spec-playwright';
const native = '/tmp/reusable-spec-native/usr/lib/x86_64-linux-gnu';
if (require('node:fs').existsSync(native)) process.env.LD_LIBRARY_PATH = native + (process.env.LD_LIBRARY_PATH ? ':' + process.env.LD_LIBRARY_PATH : '');
module.exports = defineConfig({
  testDir: './browser', timeout: 120000, globalTimeout: 600000,
  expect: { timeout: 30000 }, workers: 1, retries: 0, fullyParallel: false,
  outputDir: process.env.TEST_ARTIFACTS || path.resolve(__dirname, '../artifacts/browser-results'),
  reporter: [['list'], ['json', { outputFile: process.env.TEST_JSON_REPORT || path.resolve(__dirname, '../artifacts/browser-report.json') }]],
  use: { headless: true, trace: 'retain-on-failure', screenshot: 'only-on-failure' },
});
