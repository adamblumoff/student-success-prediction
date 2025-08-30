/**
 * Debug Login Process
 * Checks what happens during and after login
 */

const { chromium } = require('playwright');

async function debugLogin() {
  console.log('🔍 Debugging login process...');
  
  const browser = await chromium.launch({ headless: false }); // Visual debugging
  const context = await browser.newContext();
  const page = await context.newPage();
  
  await page.setViewportSize({ width: 375, height: 667 });
  
  try {
    await page.goto('http://localhost:8001', { timeout: 10000 });
    await page.waitForLoadState('domcontentloaded');
    
    console.log('\n📋 Initial state:');
    const initialLoginActive = await page.evaluate(() => document.body.classList.contains('login-active'));
    const initialMainAppVisible = await page.locator('.main-app').isVisible();
    console.log(`  Body has login-active: ${initialLoginActive}`);
    console.log(`  Main app visible: ${initialMainAppVisible}`);
    
    console.log('\n🔑 Attempting login...');
    await page.fill('input[name="username"]', 'teacher');
    await page.fill('input[name="password"]', 'demo123');
    
    // Listen for network requests to see what happens
    page.on('response', response => {
      if (response.url().includes('auth') || response.url().includes('login')) {
        console.log(`  🌐 Auth response: ${response.status()} ${response.url()}`);
      }
    });
    
    await page.click('button[type="submit"]');
    console.log('  📤 Login form submitted');
    
    // Wait and check states at different intervals
    for (let i = 1; i <= 5; i++) {
      await page.waitForTimeout(1000);
      const loginActive = await page.evaluate(() => document.body.classList.contains('login-active'));
      const mainAppVisible = await page.locator('.main-app').isVisible();
      const loginContainerVisible = await page.locator('.login-container').isVisible();
      
      console.log(`  ⏰ After ${i}s: login-active=${loginActive}, main-app=${mainAppVisible}, login-container=${loginContainerVisible}`);
      
      if (!loginActive && mainAppVisible) {
        console.log('  ✅ Login successful!');
        break;
      }
    }
    
    // Final check of navigation
    const navVisible = await page.locator('.nav-tabs').isVisible();
    console.log(`\n🧭 Final navigation check: ${navVisible}`);
    
    // Check for any JavaScript errors
    const jsErrors = [];
    page.on('pageerror', error => jsErrors.push(error.message));
    
    if (jsErrors.length > 0) {
      console.log('\n❌ JavaScript errors:');
      jsErrors.forEach(error => console.log(`  ${error}`));
    }
    
    console.log('\n🔍 Keeping browser open for manual inspection...');
    await new Promise(resolve => {
      process.on('SIGINT', () => {
        console.log('\n👋 Closing browser...');
        browser.close().then(() => resolve());
      });
    });
    
  } catch (error) {
    console.log(`❌ ERROR: ${error.message}`);
    await browser.close();
  }
}

debugLogin().catch(console.error);