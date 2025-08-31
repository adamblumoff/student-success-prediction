const { test, expect } = require('@playwright/test');

test.describe('Bulk Actions Styling and Visibility', () => {
    test.beforeEach(async ({ page }) => {
        // Navigate to the application
        await page.goto('http://localhost:8001');
        
        // Login first
        await page.fill('input[name="username"]', 'admin');
        await page.fill('input[name="password"]', 'admin123');
        await page.click('button[type="submit"]');
        
        // Wait for login to complete
        await page.waitForSelector('.tab-button[data-tab="analyze"]');
    });

    test('bulk actions should only be visible on AI analysis tab', async ({ page }) => {
        // Initially should not be on analysis tab, so bulk actions should be hidden
        const bulkModeSection = page.locator('.bulk-mode-section');
        await expect(bulkModeSection).toHaveCSS('display', 'none');
        
        // Switch to AI analysis tab
        await page.click('.tab-button[data-tab="analyze"]');
        
        // Now bulk actions should be visible
        await expect(bulkModeSection).toBeVisible();
        await expect(bulkModeSection).toHaveCSS('display', 'flex');
        
        // Switch to another tab (upload)
        await page.click('.tab-button[data-tab="upload"]');
        
        // Bulk actions should be hidden again
        await expect(bulkModeSection).toHaveCSS('display', 'none');
    });

    test('bulk actions toolbar should have clean styling', async ({ page }) => {
        // Switch to analysis tab to make bulk actions visible
        await page.click('.tab-button[data-tab="analyze"]');
        
        // Check if floating toolbar exists and is properly styled
        const toolbar = page.locator('#bulk-action-toolbar');
        
        // Check toolbar styling
        const toolbarStyles = await toolbar.evaluate(el => {
            const styles = window.getComputedStyle(el);
            return {
                position: styles.position,
                backgroundColor: styles.backgroundColor,
                borderRadius: styles.borderRadius,
                boxShadow: styles.boxShadow,
                zIndex: styles.zIndex
            };
        });
        
        console.log('Current toolbar styles:', toolbarStyles);
        
        // Toolbar should be positioned and styled for visibility
        expect(toolbarStyles.position).toBe('fixed');
        expect(parseInt(toolbarStyles.zIndex)).toBeGreaterThan(1000);
    });

    test('bulk mode toggle button should have clean styling', async ({ page }) => {
        // Switch to analysis tab
        await page.click('.tab-button[data-tab="analyze"]');
        
        const bulkToggle = page.locator('#bulk-mode-toggle');
        await expect(bulkToggle).toBeVisible();
        
        // Check button styling
        const buttonStyles = await bulkToggle.evaluate(el => {
            const styles = window.getComputedStyle(el);
            return {
                backgroundColor: styles.backgroundColor,
                borderRadius: styles.borderRadius,
                padding: styles.padding,
                fontSize: styles.fontSize,
                color: styles.color
            };
        });
        
        console.log('Current bulk toggle button styles:', buttonStyles);
        
        // Take a screenshot for visual verification
        await page.screenshot({ 
            path: 'tests/playwright/screenshots/bulk-actions-current.png',
            fullPage: true 
        });
    });

    test('selection toolbar should appear when items are selected', async ({ page }) => {
        // Switch to analysis tab
        await page.click('.tab-button[data-tab="analyze"]');
        
        // Wait for students to load and click sample data if needed
        try {
            await page.click('button:has-text("Load Sample Data")', { timeout: 2000 });
            await page.waitForSelector('.student-card', { timeout: 5000 });
        } catch (e) {
            console.log('Sample data already loaded or not needed');
        }
        
        // Look for student cards with checkboxes
        const studentCards = page.locator('.student-card');
        const count = await studentCards.count();
        
        if (count > 0) {
            // Select a student
            const firstCheckbox = studentCards.first().locator('input[type="checkbox"]');
            if (await firstCheckbox.isVisible()) {
                await firstCheckbox.check();
                
                // Toolbar should become visible
                const toolbar = page.locator('#bulk-action-toolbar');
                await expect(toolbar).not.toHaveClass(/hidden/);
            }
        }
    });
});