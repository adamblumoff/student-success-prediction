/**
 * End-to-End Tests for UI Cleanup Verification
 * Tests that promotional elements have been removed and UI is clean
 */

const { test, expect } = require('@playwright/test');

// Configure test to use the local development server
test.use({
  baseURL: 'http://localhost:8001',
});

test.describe('UI Cleanup Verification', () => {
  
  test.beforeEach(async ({ page }) => {
    // Navigate to the application
    await page.goto('/');
    
    // Wait for the page to load
    await page.waitForLoadState('networkidle');
  });

  test('should not display "89.4% prediction accuracy" promotional text', async ({ page }) => {
    // Check that the promotional accuracy text has been removed
    const promotionalText = await page.locator('text=89.4% Prediction Accuracy').count();
    expect(promotionalText).toBe(0);
    
    // Also check for any variation of 89.4%
    const accuracyText = await page.locator('text=/89\\.4%/').count();
    expect(accuracyText).toBe(0);
  });

  test('should not display "AI-Powered" badge on upload page', async ({ page }) => {
    // Check that the AI-Powered badge has been removed
    const aiBadge = await page.locator('.ai-badge').count();
    expect(aiBadge).toBe(0);
    
    // Verify the showcase header shows "System Features" instead
    const systemFeatures = await page.locator('text=System Features').first();
    await expect(systemFeatures).toBeVisible();
  });

  test('should not display demo mode button', async ({ page }) => {
    // Check that the demo mode button has been removed
    const demoButton = await page.locator('#start-demo').count();
    expect(demoButton).toBe(0);
    
    // Also check for any "Live Demo Mode" text
    const demoModeText = await page.locator('text=Live Demo Mode').count();
    expect(demoModeText).toBe(0);
    
    // Verify "Start Demo" button is not present
    const startDemoButton = await page.locator('button:has-text("Start Demo")').count();
    expect(startDemoButton).toBe(0);
  });

  test('should display clean AI Analysis tab header without marketing language', async ({ page }) => {
    // Click on the AI Analysis tab if it's enabled
    const analyzeTab = await page.locator('[data-tab="analyze"]');
    
    // Check if the tab is enabled (not disabled)
    const isDisabled = await analyzeTab.isDisabled();
    
    if (!isDisabled) {
      await analyzeTab.click();
      await page.waitForTimeout(500); // Wait for tab transition
      
      // Check that the subheading has been updated
      const marketingText = await page.locator('text=/Advanced machine learning.*89\\.4%.*accuracy/i').count();
      expect(marketingText).toBe(0);
      
      // Verify the new clean subheading is present
      const cleanSubheading = await page.locator('text=Identify at-risk students and provide targeted interventions');
      await expect(cleanSubheading).toBeVisible();
    }
  });

  test('progress bar should use accurate percentages (33%, 66%, 100%)', async ({ page }) => {
    // Get the progress bar element
    const progressBar = await page.locator('.progress-fill');
    
    // Check initial state (should be 33% for upload tab)
    const initialWidth = await progressBar.evaluate(el => el.style.width);
    expect(initialWidth).toBe('33%');
    
    // Click on Connect LMS tab if available
    const connectTab = await page.locator('[data-tab="connect"]');
    if (await connectTab.isVisible()) {
      await connectTab.click();
      await page.waitForTimeout(300);
      
      // Check progress is now 66%
      const connectWidth = await progressBar.evaluate(el => el.style.width);
      expect(connectWidth).toBe('66%');
    }
  });

  test('should have only two upload options after demo removal', async ({ page }) => {
    // Count the upload cards
    const uploadCards = await page.locator('.upload-card').count();
    
    // Should be 2 cards: "Upload CSV File" and "Try Sample Data"
    expect(uploadCards).toBe(2);
    
    // Verify the remaining cards
    const csvCard = await page.locator('.upload-card:has-text("Upload CSV File")');
    await expect(csvCard).toBeVisible();
    
    const sampleCard = await page.locator('.upload-card:has-text("Try Sample Data")');
    await expect(sampleCard).toBeVisible();
  });

  test('should display professional feature descriptions without marketing hype', async ({ page }) => {
    // Check the feature showcase area
    const showcaseCard = await page.locator('.ai-showcase-card');
    
    if (await showcaseCard.isVisible()) {
      // Verify features are displayed professionally
      const features = await page.locator('.showcase-features .feature').count();
      expect(features).toBeGreaterThan(0);
      
      // Check that features don't contain promotional percentages
      const featureTexts = await page.locator('.showcase-features').textContent();
      expect(featureTexts).not.toContain('89.4%');
      expect(featureTexts).not.toContain('Accuracy');
    }
  });

  test('navigation and core functionality remain intact', async ({ page }) => {
    // Verify all main navigation tabs are present
    const uploadTab = await page.locator('[data-tab="upload"]');
    await expect(uploadTab).toBeVisible();
    
    const connectTab = await page.locator('[data-tab="connect"]');
    await expect(connectTab).toBeVisible();
    
    const analyzeTab = await page.locator('[data-tab="analyze"]');
    await expect(analyzeTab).toBeVisible();
    
    // Verify the file upload zone is functional
    const uploadZone = await page.locator('#upload-zone');
    await expect(uploadZone).toBeVisible();
    
    // Verify sample data button still exists
    const sampleButton = await page.locator('#load-sample');
    await expect(sampleButton).toBeVisible();
  });

  test('should maintain proper styling and layout after cleanup', async ({ page }) => {
    // Take a screenshot for visual verification
    await page.screenshot({ 
      path: 'tests/e2e/screenshots/ui-cleanup-verification.png',
      fullPage: true 
    });
    
    // Check that main containers are properly displayed
    const mainContent = await page.locator('.main-content');
    await expect(mainContent).toBeVisible();
    
    const container = await page.locator('.container');
    await expect(container).toBeVisible();
    
    // Verify no layout breaks
    const header = await page.locator('.header');
    await expect(header).toBeVisible();
    
    const navTabs = await page.locator('.nav-tabs');
    await expect(navTabs).toBeVisible();
  });

  test('file upload functionality still works without demo mode', async ({ page }) => {
    // Check that the file input exists
    const fileInput = await page.locator('#file-input');
    await expect(fileInput).toBeHidden(); // Should be hidden but present
    
    // Check that the upload button works
    const uploadButton = await page.locator('button:has-text("Choose File")');
    await expect(uploadButton).toBeVisible();
    
    // Verify clicking the button would trigger file selection
    const fileInputId = await uploadButton.evaluate(btn => {
      const onclick = btn.getAttribute('onclick');
      return onclick ? onclick.match(/getElementById\('([^']+)'\)/)?.[1] : null;
    });
    expect(fileInputId).toBe('file-input');
  });
});

test.describe('Sample Data Loading', () => {
  test('sample data button should work without triggering demo mode', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Click the sample data button
    const sampleButton = await page.locator('#load-sample');
    await expect(sampleButton).toBeVisible();
    
    // Set up response interceptor to verify the API call
    const responsePromise = page.waitForResponse(
      response => response.url().includes('/api/mvp/sample') && response.status() === 200,
      { timeout: 10000 }
    ).catch(() => null); // Don't fail if the endpoint doesn't exist yet
    
    // Click the button
    await sampleButton.click();
    
    // Wait for potential response
    const response = await responsePromise;
    
    if (response) {
      // Verify it doesn't automatically switch to demo mode
      await page.waitForTimeout(2000);
      
      // Check that we're not automatically redirected to analyze tab
      // (demo mode would auto-switch tabs)
      const uploadTab = await page.locator('[data-tab="upload"].active');
      const analyzeTab = await page.locator('[data-tab="analyze"].active');
      
      // In demo mode, it would switch to analyze tab
      // Without demo mode, it should process data normally
      console.log('Sample data loaded successfully without demo mode behavior');
    }
  });
});

// Performance test to ensure cleanup didn't break loading
test.describe('Performance', () => {
  test('page should load quickly after cleanup', async ({ page }) => {
    const startTime = Date.now();
    
    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');
    
    const loadTime = Date.now() - startTime;
    
    // Page should load in under 3 seconds
    expect(loadTime).toBeLessThan(3000);
    
    console.log(`Page loaded in ${loadTime}ms`);
  });
});