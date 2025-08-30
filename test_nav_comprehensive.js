/**
 * Comprehensive Navigation Test
 * Tests navigation functionality in detail after login
 */

const { chromium } = require('playwright');

async function testNavigation() {
  console.log('🔍 Comprehensive navigation testing...');
  
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  
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
      
      // Login
      await page.fill('input[name="username"]', 'demo');
      await page.fill('input[name="password"]', 'demo123');
      await page.click('button[type="submit"]');
      
      // Wait for authentication to complete - check for class changes
      let loginCompleted = false;
      for (let i = 0; i < 10; i++) {
        await page.waitForTimeout(500);
        const loginActive = await page.evaluate(() => document.body.classList.contains('login-active'));
        const loggedIn = await page.evaluate(() => document.body.classList.contains('logged-in'));
        
        if (!loginActive || loggedIn) {
          loginCompleted = true;
          console.log(`  🔑 Login completed after ${(i + 1) * 0.5}s`);
          break;
        }
      }
      
      if (!loginCompleted) {
        console.log(`  ❌ Login failed - body still has login-active class`);
      }
      
      console.log(`\n📱 ${viewport.name} (${viewport.width}x${viewport.height}):`);
      
      // Detailed navigation checks
      const navExists = await page.locator('.nav-tabs').count() > 0;
      const navVisible = await page.locator('.nav-tabs').isVisible();
      const tabsCount = await page.locator('.tab-button').count();
      
      console.log(`  🔍 Navigation exists: ${navExists}`);
      console.log(`  👁️  Navigation visible: ${navVisible}`);
      console.log(`  🏷️  Tab count: ${tabsCount}`);
      
      if (navExists) {
        // Get computed styles
        const navStyles = await page.locator('.nav-tabs').evaluate(el => {
          const styles = window.getComputedStyle(el);
          return {
            display: styles.display,
            visibility: styles.visibility,
            opacity: styles.opacity,
            height: styles.height,
            position: styles.position,
            top: styles.top,
            zIndex: styles.zIndex
          };
        });
        console.log(`  🎨 Navigation styles:`, navStyles);
        
        // Check individual tabs
        const tabs = await page.locator('.tab-button').all();
        for (let i = 0; i < tabs.length; i++) {
          const tabVisible = await tabs[i].isVisible();
          const tabText = await tabs[i].textContent();
          console.log(`    Tab ${i + 1}: "${tabText?.trim()}" - Visible: ${tabVisible}`);
        }
        
        // Test tab functionality
        try {
          const connectTab = page.locator('[data-tab="connect"]');
          if (await connectTab.isVisible()) {
            await connectTab.click();
            await page.waitForTimeout(500);
            
            const activeTab = await page.locator('.tab-button.active').textContent();
            console.log(`  🖱️  Tab switching: SUCCESS - Active tab: "${activeTab?.trim()}"`);
          } else {
            console.log(`  🖱️  Tab switching: FAILED - Connect tab not visible`);
          }
        } catch (e) {
          console.log(`  🖱️  Tab switching: ERROR - ${e.message}`);
        }
      }
      
      // Check progress bar
      const progressExists = await page.locator('.progress-bar').count() > 0;
      const progressVisible = await page.locator('.progress-bar').isVisible();
      console.log(`  📊 Progress bar exists: ${progressExists}, visible: ${progressVisible}`);
      
      // Check main content visibility
      const modularAppVisible = await page.locator('.modular-app').isVisible();
      console.log(`  📱 Modular app visible: ${modularAppVisible}`);
      
    } catch (error) {
      console.log(`❌ ${viewport.name}: ERROR - ${error.message}`);
    }
    
    await page.close();
  }
  
  await browser.close();
  console.log('\n✅ Comprehensive navigation test completed!');
}

testNavigation().catch(console.error);