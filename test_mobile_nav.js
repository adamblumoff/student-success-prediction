/**
 * Quick Mobile Navigation Test
 */

const { chromium } = require('playwright');

async function testMobileNavigation() {
  console.log('📱 Testing mobile navigation fixes...');
  
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  
  // Test different mobile viewports
  const viewports = [
    { width: 375, height: 667, name: 'iPhone SE' },
    { width: 414, height: 896, name: 'iPhone 11' },
    { width: 768, height: 1024, name: 'iPad' }
  ];
  
  for (const viewport of viewports) {
    const page = await context.newPage();
    await page.setViewportSize(viewport);
    
    try {
      await page.goto('http://localhost:8001', { timeout: 10000 });
      await page.waitForLoadState('domcontentloaded');
      
      // Check if login is required and handle it
      const loginRequired = await page.locator('.login-container').isVisible();
      if (loginRequired) {
        await page.fill('input[name="username"]', 'demo');
        await page.fill('input[name="password"]', 'demo123');
        await page.click('button[type="submit"]');
        await page.waitForTimeout(2000); // Give more time for login process
        console.log(`  🔑 ${viewport.name}: Logged in successfully`);
      }
      
      // Now check navigation visibility after login
      const navVisible = await page.locator('.nav-tabs').isVisible();
      const tabsCount = await page.locator('.tab-button').count();
      const progressBarVisible = await page.locator('.progress-bar').isVisible();
      
      // Check if tabs are clickable
      let tabClickable = false;
      try {
        const connectTab = page.locator('[data-tab="connect"]');
        if (await connectTab.isVisible()) {
          await connectTab.click();
          await page.waitForTimeout(300);
          tabClickable = true;
        }
      } catch (e) {
        tabClickable = false;
      }
      
      console.log(`${viewport.name}:`);
      console.log(`  ✅ Navigation visible: ${navVisible ? 'YES' : 'NO'}`);
      console.log(`  ✅ Tab count: ${tabsCount}`);
      console.log(`  ✅ Progress bar visible: ${progressBarVisible ? 'YES' : 'NO'}`);
      console.log(`  ✅ Tab switching works: ${tabClickable ? 'YES' : 'NO'}`);
      console.log('');
      
    } catch (error) {
      console.log(`${viewport.name}: ERROR - ${error.message}`);
    }
    
    await page.close();
  }
  
  await browser.close();
  console.log('✅ Mobile navigation test completed!');
}

testMobileNavigation().catch(console.error);