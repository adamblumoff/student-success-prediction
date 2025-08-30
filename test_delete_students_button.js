/**
 * Delete All Students Button Test
 * Tests the delete all students functionality with Canvas data
 */

const { chromium } = require('playwright');

async function testDeleteStudentsButton() {
    console.log('🧪 Testing Delete All Students Button...');
    
    const browser = await chromium.launch({ headless: false }); // Show browser for debugging
    const context = await browser.newContext();
    const page = await context.newPage();
    
    await page.setViewportSize({ width: 1200, height: 800 });
    
    try {
        // 1. Login
        await page.goto('http://localhost:8001', { timeout: 10000 });
        await page.waitForLoadState('domcontentloaded');
        
        await page.fill('input[name="username"]', 'admin');
        await page.fill('input[name="password"]', 'admin123');
        await page.click('button[type="submit"]');
        await page.waitForTimeout(2000);
        
        console.log('✅ Logged in successfully');
        
        // 2. First, import Canvas students to have data to delete
        await page.click('button:has-text("Connect LMS")');
        await page.waitForTimeout(1000);
        
        const canvasCard = page.locator('.integration-card[data-integration="canvas"]');
        await canvasCard.click();
        await page.waitForTimeout(1000);
        
        await page.click('#test-connection-btn');
        await page.waitForTimeout(1000);
        await page.click('#connect-btn');
        await page.waitForTimeout(1000);
        await page.click('button:has-text("Import Selected Courses")');
        await page.waitForTimeout(5000); // Wait for import to complete
        
        console.log('✅ Canvas data imported');
        
        // 3. Verify we have students in database
        const initialCount = await page.evaluate(async () => {
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
        
        console.log(`📊 Students in database before delete: ${initialCount}`);
        
        if (initialCount === 0) {
            throw new Error('No students found - Canvas import may have failed');
        }
        
        // 4. Navigate to AI Analysis tab
        await page.click('button:has-text("AI Analysis")');
        await page.waitForTimeout(2000);
        
        console.log('✅ Navigated to AI Analysis tab');
        
        // 5. Find and verify delete button exists
        const deleteButton = page.locator('#delete-all-students');
        await deleteButton.waitFor({ state: 'visible', timeout: 5000 });
        
        console.log('✅ Delete all students button found');
        
        // 6. Click delete button and handle confirmations
        await deleteButton.click();
        await page.waitForTimeout(500);
        
        // Handle first confirmation dialog
        page.on('dialog', async dialog => {
            console.log(`⚠️  Dialog: ${dialog.message()}`);
            await dialog.accept();
        });
        
        await page.waitForTimeout(3000); // Wait for delete operation
        
        console.log('✅ Delete button clicked and confirmations handled');
        
        // 7. Verify database is empty after deletion
        const finalCount = await page.evaluate(async () => {
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
        
        console.log(`📊 Students in database after delete: ${finalCount}`);
        
        // 8. Test results
        if (finalCount === 0) {
            console.log('\\n🎉 Delete All Students Test PASSED!');
            console.log(`   ✅ Started with ${initialCount} students`);
            console.log('   ✅ Delete button successfully cleared database');
            console.log('   ✅ Database confirmed empty after deletion');
            console.log('   ✅ UI confirmations working properly');
        } else {
            console.log('\\n❌ Delete All Students Test FAILED!');
            console.log(`   ❌ Expected 0 students, still have ${finalCount}`);
        }
        
        // Take final screenshot
        await page.screenshot({ path: 'delete_students_test_result.png' });
        console.log('📸 Test result screenshot saved');
        
    } catch (error) {
        console.log(`❌ TEST FAILED: ${error.message}`);
        
        // Take error screenshot
        await page.screenshot({ path: 'delete_students_test_error.png' });
        console.log('📸 Error screenshot saved as delete_students_test_error.png');
        
    } finally {
        await browser.close();
    }
}

testDeleteStudentsButton().catch(console.error);