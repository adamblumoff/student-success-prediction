/**
 * Visual Hierarchy Test - Check spacing, prominence, and layout improvements
 */

const { chromium } = require('playwright');

async function testVisualHierarchy() {
  console.log('🎨 Testing visual hierarchy improvements...');
  
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();
  
  await page.setViewportSize({ width: 1200, height: 800 });
  
  try {
    await page.goto('http://localhost:8001', { timeout: 10000 });
    await page.waitForLoadState('domcontentloaded');
    
    // Login
    await page.fill('input[name="username"]', 'demo');
    await page.fill('input[name="password"]', 'demo123');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(1500);
    
    console.log('\n🎯 Visual Hierarchy Analysis:');
    
    // Test enhanced spacing
    const mainContentPadding = await page.locator('.main-content').evaluate(el => {
      const styles = window.getComputedStyle(el);
      return {
        paddingTop: styles.paddingTop,
        paddingBottom: styles.paddingBottom
      };
    });
    console.log(`  📏 Main content padding: ${mainContentPadding.paddingTop} top, ${mainContentPadding.paddingBottom} bottom`);
    
    // Test AI showcase card enhancements
    const showcaseCard = await page.locator('.ai-showcase-card').first();
    if (await showcaseCard.count() > 0) {
      const showcaseStyles = await showcaseCard.evaluate(el => {
        const styles = window.getComputedStyle(el);
        return {
          borderRadius: styles.borderRadius,
          boxShadow: styles.boxShadow,
          marginBottom: styles.marginBottom,
          padding: styles.padding
        };
      });
      console.log(`  ✨ AI Showcase card:`, showcaseStyles);
    }
    
    // Test upload card improvements  
    const uploadCards = await page.locator('.upload-card').count();
    if (uploadCards > 0) {
      const uploadCardStyle = await page.locator('.upload-card').first().evaluate(el => {
        const styles = window.getComputedStyle(el);
        return {
          borderRadius: styles.borderRadius,
          boxShadow: styles.boxShadow,
          padding: styles.padding,
          height: styles.height
        };
      });
      console.log(`  📤 Upload cards (${uploadCards} found):`, uploadCardStyle);
    }
    
    // Test enhanced upload icons
    const uploadIcons = await page.locator('.upload-icon').count();
    if (uploadIcons > 0) {
      const iconStyle = await page.locator('.upload-icon').first().evaluate(el => {
        const styles = window.getComputedStyle(el);
        return {
          width: styles.width,
          height: styles.height,
          borderRadius: styles.borderRadius,
          boxShadow: styles.boxShadow
        };
      });
      console.log(`  🎯 Upload icons (${uploadIcons} found):`, iconStyle);
    }
    
    // Test enhanced CTA buttons
    const primaryButtons = await page.locator('.btn-primary').count();
    if (primaryButtons > 0) {
      const buttonStyle = await page.locator('.upload-card .btn-primary').first().evaluate(el => {
        const styles = window.getComputedStyle(el);
        return {
          background: styles.background.substring(0, 50) + '...',
          borderRadius: styles.borderRadius,
          boxShadow: styles.boxShadow.substring(0, 50) + '...',
          padding: styles.padding,
          fontWeight: styles.fontWeight
        };
      });
      console.log(`  🎯 Primary CTAs (${primaryButtons} found):`, buttonStyle);
    }
    
    // Test integration cards
    const integrationCards = await page.locator('.integration-card').count();
    if (integrationCards > 0) {
      const integrationStyle = await page.locator('.integration-card').first().evaluate(el => {
        const styles = window.getComputedStyle(el);
        return {
          borderRadius: styles.borderRadius,
          boxShadow: styles.boxShadow,
          padding: styles.padding
        };
      });
      console.log(`  🔗 Integration cards (${integrationCards} found):`, integrationStyle);
    }
    
    // Test grid layouts
    const uploadGrid = await page.locator('.upload-options').evaluate(el => {
      const styles = window.getComputedStyle(el);
      return {
        display: styles.display,
        gap: styles.gap,
        gridTemplateColumns: styles.gridTemplateColumns.substring(0, 50) + '...'
      };
    });
    console.log(`  📐 Upload grid layout:`, uploadGrid);
    
    // Test hover effects by simulating hover
    console.log('\n  🖱️  Testing Hover Effects:');
    const uploadCard = page.locator('.upload-card').first();
    if (await uploadCard.count() > 0) {
      await uploadCard.hover();
      await page.waitForTimeout(300);
      
      const hoverTransform = await uploadCard.evaluate(el => {
        const styles = window.getComputedStyle(el);
        return styles.transform;
      });
      console.log(`    📤 Upload card hover transform: ${hoverTransform}`);
    }
    
  } catch (error) {
    console.log(`❌ ERROR: ${error.message}`);
  }
  
  await browser.close();
  console.log('\n✅ Visual hierarchy test completed!');
}

testVisualHierarchy().catch(console.error);