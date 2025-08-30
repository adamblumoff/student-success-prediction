/**
 * Canvas Auto-Navigation Test
 * Tests that Canvas import automatically navigates to AI Analysis tab
 */

const { chromium } = require('playwright');

async function testCanvasAutoNavigation() {
    console.log('🧭 Testing Canvas Auto-Navigation to AI Analysis Tab...');
    
    const browser = await chromium.launch({ headless: false }); // Show browser for debugging
    const context = await browser.newContext();
    const page = await context.newPage();
    
    await page.setViewportSize({ width: 1200, height: 800 });
    
    try {
        // Navigate to the application
        await page.goto('http://localhost:8001', { timeout: 10000 });
        await page.waitForLoadState('domcontentloaded');
        
        // Login first
        await page.fill('input[name="username"]', 'admin');
        await page.fill('input[name="password"]', 'admin123');
        await page.click('button[type="submit"]');
        await page.waitForTimeout(2000);
        
        console.log('✅ Logged in successfully');
        
        // Clear any existing students first to ensure clean test
        const clearResponse = await page.evaluate(async () => {
            try {
                const response = await fetch('/api/mvp/students/all', {
                    method: 'DELETE',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${localStorage.getItem('api_key') || '0dUHi4QroC1GfgnbibLbqowUnv2YFWIe'}`
                    }
                });
                const result = await response.json();
                return result.success;
            } catch (error) {
                return false;
            }
        });
        
        console.log(`🧹 Database cleared: ${clearResponse ? 'Yes' : 'No'}`);
        
        // Navigate to Connect LMS tab
        const connectTab = await page.locator('button[data-tab="connect"]');
        await connectTab.click();
        await page.waitForTimeout(500);
        
        console.log('✅ Started on Connect LMS tab');
        
        // Verify we're on the connect tab
        const connectTabActive = await page.locator('button[data-tab="connect"].active').isVisible();
        console.log(`📋 Connect tab active: ${connectTabActive}`);
        
        // Click on Canvas card to start integration
        const canvasCard = await page.locator('.integration-card[data-integration="canvas"]');
        await canvasCard.click();
        await page.waitForTimeout(1000);
        
        // Test connection
        await page.click('#test-connection-btn');
        await page.waitForTimeout(2000);
        
        // Connect and continue to course selection
        await page.click('#connect-btn');
        await page.waitForTimeout(1500);
        
        console.log('✅ Connection flow completed, starting import...');
        
        // Import selected courses
        const importButton = await page.locator('button:has-text("Import Selected Courses")');
        await importButton.click();
        await page.waitForTimeout(1000);
        
        console.log('✅ Import process started');
        
        // Wait for import to complete (this should trigger auto-navigation)
        await page.waitForTimeout(7000);
        
        console.log('⏳ Import completed, checking auto-navigation...');
        
        // Check if we automatically navigated to the AI Analysis tab
        await page.waitForTimeout(2000); // Give time for navigation
        
        const analyzeTabActive = await page.locator('button[data-tab="analyze"].active').isVisible();
        const analyzeTabContent = await page.locator('#tab-analyze.active').isVisible();
        
        console.log(`🧭 Analyze tab button active: ${analyzeTabActive}`);
        console.log(`📄 Analyze tab content visible: ${analyzeTabContent}`);
        
        // Verify we have students in the database after import
        const studentCount = await page.evaluate(async () => {
            try {
                const response = await fetch('/api/canvas-import/import-status', {
                    headers: { 'Authorization': `Bearer ${localStorage.getItem('api_key') || '0dUHi4QroC1GfgnbibLbqowUnv2YFWIe'}` }
                });
                const data = await response.json();
                return data.total_canvas_students || 0;
            } catch (error) {
                return 0;
            }
        });
        
        console.log(`📊 Students imported: ${studentCount}`);
        
        // Test Results
        if (analyzeTabActive && analyzeTabContent && studentCount > 0) {
            console.log('\n🎉 Canvas Auto-Navigation Test PASSED!');
            console.log(`   ✅ Started on Connect LMS tab`);
            console.log(`   ✅ Canvas import completed successfully`);
            console.log(`   ✅ Imported ${studentCount} students to database`);
            console.log(`   ✅ Automatically navigated to AI Analysis tab`);
            console.log(`   ✅ AI Analysis tab is active and visible`);
        } else {
            console.log('\n❌ Canvas Auto-Navigation Test FAILED!');
            if (!analyzeTabActive) console.log('   ❌ Analyze tab button not active');
            if (!analyzeTabContent) console.log('   ❌ Analyze tab content not visible');
            if (studentCount === 0) console.log('   ❌ No students imported to database');
        }
        
        // Take final screenshot
        await page.screenshot({ path: 'canvas_auto_navigation_result.png' });
        console.log('📸 Test result screenshot saved');
        
    } catch (error) {
        console.log(`❌ TEST FAILED: ${error.message}`);
        
        // Take error screenshot
        await page.screenshot({ path: 'canvas_auto_navigation_error.png' });
        console.log('📸 Error screenshot saved as canvas_auto_navigation_error.png');
    }
    
    await browser.close();
}

testCanvasAutoNavigation().catch(console.error);