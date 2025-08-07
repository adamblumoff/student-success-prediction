const { test, expect } = require('@playwright/test');

test.describe('Debug Student Success Interface', () => {
  test('debug interface functionality', async ({ page }) => {
    console.log('🔍 Starting interface debugging...');
    
    // Go to the application
    await page.goto('/');
    
    // Wait for page to load
    await page.waitForLoadState('networkidle');
    
    // Check for JavaScript errors
    const errors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
        console.log('❌ Console error:', msg.text());
      } else if (msg.type() === 'log' && msg.text().includes('✅')) {
        console.log('✅', msg.text());
      }
    });
    
    // Check that main elements load
    console.log('🔍 Checking main page elements...');
    await expect(page.locator('header h1')).toContainText('Student Success Predictor');
    console.log('✅ Header found');
    
    await expect(page.locator('.tab-button[data-tab="upload"]')).toBeVisible();
    console.log('✅ Upload tab found');
    
    await expect(page.locator('#load-sample')).toBeVisible(); 
    console.log('✅ Load sample button found');
    
    // Test loading sample data
    console.log('🔍 Testing sample data loading...');
    await page.click('#load-sample');
    
    // Wait for API call to complete
    await page.waitForResponse(response => 
      response.url().includes('/api/mvp/sample') && response.status() === 200
    );
    console.log('✅ Sample data API call completed');
    
    // Check if analyze tab gets enabled
    await page.waitForTimeout(2000);
    const analyzeTab = page.locator('.tab-button[data-tab="analyze"]');
    const isDisabled = await analyzeTab.getAttribute('disabled');
    if (isDisabled === null) {
      console.log('✅ Analyze tab is enabled');
      
      // Switch to analyze tab
      await analyzeTab.click();
      
      // Look for student containers
      const containers = [
        '#student-list',
        '#student-list-compact', 
        '#students-list'
      ];
      
      let studentsFound = false;
      for (const containerSelector of containers) {
        const container = page.locator(containerSelector);
        if (await container.isVisible()) {
          const content = await container.innerHTML();
          if (content.includes('Student #')) {
            console.log(`✅ Students found in container: ${containerSelector}`);
            console.log(`📊 Container content preview: ${content.substring(0, 200)}...`);
            studentsFound = true;
            break;
          }
        }
      }
      
      if (!studentsFound) {
        console.log('❌ No students found in any container');
        
        // Debug: Check all possible containers
        for (const containerSelector of containers) {
          const container = page.locator(containerSelector);
          const exists = await container.count() > 0;
          const visible = exists ? await container.isVisible() : false;
          const content = exists && visible ? await container.innerHTML() : 'N/A';
          
          console.log(`🔍 Container ${containerSelector}:`, {
            exists,
            visible,
            content: content.length > 0 ? `${content.length} chars` : 'empty'
          });
        }
      }
      
      // Test AI explanation if students are found
      if (studentsFound) {
        const explainButton = page.locator('button:has-text("Explain")').first();
        if (await explainButton.isVisible()) {
          console.log('🔍 Testing AI explanation...');
          await explainButton.click();
          
          // Wait for API call
          try {
            await page.waitForResponse(response => 
              response.url().includes('/api/mvp/explain/') && response.status() === 200, 
              { timeout: 5000 }
            );
            console.log('✅ AI explanation API works');
          } catch (e) {
            console.log('❌ AI explanation API timeout or error');
          }
        }
      }
      
    } else {
      console.log('❌ Analyze tab is still disabled');
    }
    
    // Report any JavaScript errors
    if (errors.length > 0) {
      console.log('\n❌ JavaScript Errors Found:');
      errors.forEach((error, i) => console.log(`${i + 1}. ${error}`));
    } else {
      console.log('\n✅ No JavaScript errors detected');
    }
    
    // Keep browser open for manual inspection
    console.log('\n🔍 Keeping browser open for manual inspection...');
    await page.waitForTimeout(5000);
  });
});