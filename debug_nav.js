/**
 * Debug Navigation Test - More detailed inspection
 */

const { chromium } = require('playwright');

async function debugNavigation() {
  console.log('🔍 Debugging mobile navigation in detail...');
  
  const browser = await chromium.launch({ headless: false }); // Show browser
  const context = await browser.newContext();
  const page = await context.newPage();
  
  // Test mobile viewport
  await page.setViewportSize({ width: 375, height: 667 });
  
  try {
    await page.goto('http://localhost:8001', { timeout: 10000 });
    await page.waitForLoadState('domcontentloaded');
    
    // Wait a bit for JavaScript to load
    await page.waitForTimeout(2000);
    
    console.log('\n📱 iPhone SE (375px) Debug:');
    
    // Check if elements exist in DOM
    const navTabsExists = await page.locator('.nav-tabs').count() > 0;
    const tabButtonsExist = await page.locator('.tab-button').count() > 0;
    const progressBarExists = await page.locator('.progress-bar').count() > 0;
    
    console.log(`  🔍 .nav-tabs exists: ${navTabsExists}`);
    console.log(`  🔍 .tab-button exists: ${tabButtonsExist}`);
    console.log(`  🔍 .progress-bar exists: ${progressBarExists}`);
    
    // Get computed styles
    if (navTabsExists) {
      const navStyles = await page.locator('.nav-tabs').evaluate(el => {
        const styles = window.getComputedStyle(el);
        return {
          display: styles.display,
          visibility: styles.visibility,
          height: styles.height,
          minHeight: styles.minHeight,
          position: styles.position,
          top: styles.top,
          zIndex: styles.zIndex,
          backgroundColor: styles.backgroundColor
        };
      });
      console.log('  🎨 .nav-tabs computed styles:', navStyles);
    }
    
    // Check if login is blocking content
    const loginContainer = await page.locator('.login-container').isVisible();
    const loginActive = await page.evaluate(() => document.body.classList.contains('login-active'));
    
    console.log(`  🔐 Login container visible: ${loginContainer}`);
    console.log(`  🔐 Body has login-active class: ${loginActive}`);
    
    // Check main app visibility
    const mainAppVisible = await page.locator('.main-app').isVisible();
    console.log(`  📱 Main app visible: ${mainAppVisible}`);
    
    // If login is active, try to login
    if (loginActive) {
      console.log('  🔑 Attempting to login...');
      await page.fill('input[name="api_key"]', 'dev-key-change-me');
      await page.click('button[type="submit"]');
      await page.waitForTimeout(1000);
      
      // Recheck navigation after login
      const navVisibleAfterLogin = await page.locator('.nav-tabs').isVisible();
      console.log(`  ✅ Navigation visible after login: ${navVisibleAfterLogin}`);
      
      if (navVisibleAfterLogin) {
        const tabCount = await page.locator('.tab-button').count();
        console.log(`  ✅ Tab count after login: ${tabCount}`);
        
        // Try to click a tab
        try {
          await page.locator('[data-tab="connect"]').click();
          await page.waitForTimeout(300);
          console.log(`  ✅ Tab clicking works after login`);
        } catch (e) {
          console.log(`  ❌ Tab clicking failed: ${e.message}`);
        }
      }
    }
    
  } catch (error) {
    console.log(`❌ ERROR: ${error.message}`);
  }
  
  // Keep browser open for manual inspection
  console.log('\n🔍 Browser kept open for manual inspection. Press Ctrl+C to close.');
  await new Promise(resolve => {
    process.on('SIGINT', () => {
      console.log('\n👋 Closing browser...');
      browser.close().then(() => resolve());
    });
  });
}

debugNavigation().catch(console.error);