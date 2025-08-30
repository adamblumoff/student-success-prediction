/**
 * Accessibility Test - Verify ARIA labels and roles
 */

const { chromium } = require('playwright');

async function testAccessibility() {
  console.log('🔍 Testing accessibility improvements...');
  
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();
  
  try {
    await page.goto('http://localhost:8001', { timeout: 10000 });
    await page.waitForLoadState('domcontentloaded');
    
    // Login
    await page.fill('input[name="username"]', 'demo');
    await page.fill('input[name="password"]', 'demo123');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(1500);
    
    console.log('\n🎯 Accessibility Test Results:');
    
    // Count buttons with aria-label
    const buttonsWithAriaLabel = await page.locator('button[aria-label]').count();
    const totalButtons = await page.locator('button').count();
    
    console.log(`  📊 Buttons with aria-label: ${buttonsWithAriaLabel}/${totalButtons} (${Math.round(buttonsWithAriaLabel/totalButtons*100)}%)`);
    
    // Test specific accessibility improvements
    const tests = [
      { selector: 'button[id="notifications-toggle"][aria-label]', name: 'Notifications button' },
      { selector: 'button[id="settings-toggle"][aria-label]', name: 'Settings button' },
      { selector: 'button[id="logout-btn"][aria-label]', name: 'Logout button' },
      { selector: 'button[data-tab="upload"][role="tab"][aria-selected]', name: 'Upload tab with ARIA' },
      { selector: 'button[data-tab="connect"][role="tab"][aria-selected]', name: 'Connect tab with ARIA' },
      { selector: 'button[data-tab="analyze"][role="tab"][aria-selected]', name: 'Analyze tab with ARIA' },
      { selector: 'div[role="tablist"]', name: 'Tab list with role' },
      { selector: 'button[onclick*="showIntegrationForm"][aria-label]', name: 'Integration buttons' },
      { selector: 'button[class*="filter-btn"][aria-label]', name: 'Filter buttons' },
    ];
    
    console.log('\n  🔍 Specific Accessibility Tests:');
    for (const test of tests) {
      const count = await page.locator(test.selector).count();
      const status = count > 0 ? '✅ PASS' : '❌ FAIL';
      console.log(`    ${status} ${test.name}: ${count} found`);
    }
    
    // Test for proper heading structure
    const headings = await page.locator('h1, h2, h3, h4, h5, h6').count();
    console.log(`\n  📝 Heading structure: ${headings} headings found`);
    
    // Test for alt text on images (if any)
    const imagesWithAlt = await page.locator('img[alt]').count();
    const totalImages = await page.locator('img').count();
    if (totalImages > 0) {
      console.log(`  🖼️  Images with alt text: ${imagesWithAlt}/${totalImages}`);
    }
    
    // Test tab navigation
    console.log('\n  ⌨️  Keyboard Navigation Test:');
    try {
      await page.keyboard.press('Tab');
      await page.keyboard.press('Tab');
      await page.keyboard.press('Tab');
      const focusedElement = await page.evaluate(() => {
        return document.activeElement ? document.activeElement.tagName : 'None';
      });
      console.log(`    ✅ Tab navigation works - Focus on: ${focusedElement}`);
    } catch (e) {
      console.log(`    ❌ Tab navigation failed: ${e.message}`);
    }
    
  } catch (error) {
    console.log(`❌ ERROR: ${error.message}`);
  }
  
  await browser.close();
  console.log('\n✅ Accessibility test completed!');
}

testAccessibility().catch(console.error);