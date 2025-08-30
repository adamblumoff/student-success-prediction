/**
 * Playwright Test Configuration
 */

const { defineConfig, devices } = require('@playwright/test');

module.exports = defineConfig({
  // Test directory
  testDir: './tests/e2e',
  
  // Test timeout
  timeout: 30000,
  
  // Number of workers
  workers: 1,
  
  // Reporter configuration
  reporter: [
    ['html', { outputFolder: 'tests/e2e/playwright-report' }],
    ['list']
  ],
  
  // Shared settings for all tests
  use: {
    // Base URL for the application
    baseURL: 'http://localhost:8001',
    
    // Collect trace when retrying the failed test
    trace: 'on-first-retry',
    
    // Screenshot on failure
    screenshot: 'only-on-failure',
    
    // Video on failure
    video: 'retain-on-failure',
  },

  // Configure projects for different browsers
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
  ],

  // Server is already running, no need to start it
  // webServer configuration removed - using existing server on port 8001
});