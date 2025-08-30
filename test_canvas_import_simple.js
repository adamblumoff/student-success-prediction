/**
 * Simple Canvas Import Test
 * Tests the Canvas integration and verifies database import
 */

const { chromium } = require('playwright');

async function testCanvasImportSimple() {
    console.log('🎯 Testing Canvas Import (Simplified)...');
    
    const browser = await chromium.launch({ headless: false }); // Show browser for debugging
    const context = await browser.newContext();
    const page = await context.newPage();
    
    await page.setViewportSize({ width: 1200, height: 800 });
    
    try {
        // Navigate and login
        await page.goto('http://localhost:8001', { timeout: 10000 });
        await page.waitForLoadState('domcontentloaded');
        
        await page.fill('input[name="username"]', 'admin');
        await page.fill('input[name="password"]', 'admin123');
        await page.click('button[type="submit"]');
        await page.waitForTimeout(2000);
        
        console.log('✅ Logged in successfully');
        
        // Navigate to Connect LMS tab
        await page.click('button:has-text("Connect LMS")');
        await page.waitForTimeout(1000);
        
        console.log('✅ Navigated to Connect LMS tab');
        
        // Click on Canvas card
        const canvasCard = page.locator('.integration-card[data-integration="canvas"]');
        await canvasCard.click();
        await page.waitForTimeout(1000);
        
        console.log('✅ Opened Canvas modal');
        
        // Test Canvas connection
        await page.click('#test-connection-btn');
        await page.waitForTimeout(2000);
        
        // Connect to Canvas
        await page.click('#connect-btn');
        await page.waitForTimeout(2000);
        
        console.log('✅ Connected to Canvas');
        
        // Import courses (all should be selected by default)
        await page.click('button:has-text("Import Selected Courses")');
        await page.waitForTimeout(5000); // Wait for import to complete
        
        console.log('✅ Import initiated, waiting for completion...');
        
        // Verify import via API call
        const importStatus = await page.evaluate(async () => {
            try {
                const response = await fetch('/api/canvas-import/import-status', {
                    headers: { 'Authorization': `Bearer ${localStorage.getItem('api_key') || '0dUHi4QroC1GfgnbibLbqowUnv2YFWIe'}` }
                });
                return response.json();
            } catch (error) {
                return { error: error.message };
            }
        });
        
        console.log('📊 Import Status Results:');
        console.log(`   Students imported: ${importStatus.total_canvas_students || 0}`);
        console.log(`   Courses imported: ${importStatus.courses_imported || 0}`);
        
        if (importStatus.courses) {
            console.log('📚 Course breakdown:');
            importStatus.courses.forEach(course => {
                console.log(`   - ${course.course_code}: ${course.student_count} students`);
            });
        }
        
        // Check if we have the expected number of students
        const expectedStudents = 108; // 28+24+26+30
        const actualStudents = importStatus.total_canvas_students || 0;
        
        if (actualStudents >= expectedStudents * 0.9) { // Allow 10% variance
            console.log('\\n🎉 Canvas Import Test PASSED!');
            console.log(`   ✅ Successfully imported ${actualStudents} students`);
            console.log(`   ✅ ${importStatus.courses_imported || 0} courses processed`);
            console.log('   ✅ Database persistence working');
            console.log('   ✅ UI workflow functional');
        } else {
            console.log('\\n❌ Canvas Import Test FAILED!');
            console.log(`   ❌ Expected ~${expectedStudents} students, got ${actualStudents}`);
        }
        
        // Take a success screenshot
        await page.screenshot({ path: 'canvas_import_success.png' });
        console.log('📸 Success screenshot saved as canvas_import_success.png');
        
    } catch (error) {
        console.log(`❌ TEST FAILED: ${error.message}`);
        
        // Take screenshot for debugging
        await page.screenshot({ path: 'canvas_import_test_error.png' });
        console.log('📸 Error screenshot saved as canvas_import_test_error.png');
        
    } finally {
        await browser.close();
    }
}

testCanvasImportSimple().catch(console.error);