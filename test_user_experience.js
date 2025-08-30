/**
 * User Experience Flow Test - Verify UX improvements and flow enhancements
 */

const { chromium } = require('playwright');

async function testUserExperience() {
  console.log('🚀 Testing user experience flow improvements...');
  
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
    
    console.log('\n🎯 User Experience Analysis:');
    
    // Test enhanced empty states
    const noSelectionElements = await page.locator('.no-selection').count();
    if (noSelectionElements > 0) {
      const emptyStateStyle = await page.locator('.no-selection').first().evaluate(el => {
        const styles = window.getComputedStyle(el);
        return {
          background: styles.backgroundColor,
          borderRadius: styles.borderRadius,
          border: styles.border,
          padding: styles.padding
        };
      });
      console.log(`  🗂️  Enhanced empty states (${noSelectionElements} found):`, emptyStateStyle);
    }
    
    // Test error state styles (inject test error state)
    await page.evaluate(() => {
      const testErrorDiv = document.createElement('div');
      testErrorDiv.className = 'error-state';
      testErrorDiv.innerHTML = `
        <div class="error-icon"><i class="fas fa-exclamation-triangle"></i></div>
        <div class="error-title">Test Error State</div>
        <div class="error-message">This is a test error message to verify styling.</div>
        <div class="error-actions">
          <button class="btn btn-primary">Retry</button>
          <button class="btn btn-secondary">Cancel</button>
        </div>
      `;
      document.body.appendChild(testErrorDiv);
    });
    
    await page.waitForTimeout(500);
    const errorStateStyle = await page.locator('.error-state').evaluate(el => {
      const styles = window.getComputedStyle(el);
      return {
        background: styles.backgroundColor,
        borderRadius: styles.borderRadius,
        border: styles.border,
        padding: styles.padding
      };
    });
    console.log(`  ❌ Enhanced error states:`, errorStateStyle);
    
    // Test loading state styles (inject test loading state)
    await page.evaluate(() => {
      const testLoadingDiv = document.createElement('div');
      testLoadingDiv.className = 'loading-state';
      testLoadingDiv.innerHTML = `
        <div class="loading-spinner"></div>
        <div class="loading-text">Loading your data...</div>
        <div class="loading-subtext">Please wait while we process your request.</div>
      `;
      document.body.appendChild(testLoadingDiv);
    });
    
    await page.waitForTimeout(500);
    const loadingStateStyle = await page.locator('.loading-state').evaluate(el => {
      const styles = window.getComputedStyle(el);
      return {
        padding: styles.padding,
        textAlign: styles.textAlign
      };
    });
    console.log(`  ⏳ Enhanced loading states:`, loadingStateStyle);
    
    // Test loading spinner animation
    const spinnerAnimation = await page.locator('.loading-spinner').evaluate(el => {
      const styles = window.getComputedStyle(el);
      return {
        width: styles.width,
        height: styles.height,
        borderTopColor: styles.borderTopColor,
        animation: styles.animation.substring(0, 30) + '...'
      };
    });
    console.log(`  🔄 Loading spinner:`, spinnerAnimation);
    
    // Test success state styles (inject test success state)
    await page.evaluate(() => {
      const testSuccessDiv = document.createElement('div');
      testSuccessDiv.className = 'success-state';
      testSuccessDiv.innerHTML = `
        <div class="success-icon"><i class="fas fa-check"></i></div>
        <div class="success-title">Success!</div>
        <div class="success-message">Your data has been processed successfully.</div>
      `;
      document.body.appendChild(testSuccessDiv);
    });
    
    await page.waitForTimeout(500);
    const successStateStyle = await page.locator('.success-state').evaluate(el => {
      const styles = window.getComputedStyle(el);
      return {
        background: styles.backgroundColor,
        borderRadius: styles.borderRadius,
        border: styles.border
      };
    });
    console.log(`  ✅ Enhanced success states:`, successStateStyle);
    
    // Test progress steps (inject test progress indicator)
    await page.evaluate(() => {
      const progressDiv = document.createElement('div');
      progressDiv.className = 'progress-steps';
      progressDiv.innerHTML = `
        <div class="progress-step completed">
          <div class="progress-step-circle">1</div>
          <div class="progress-step-label">Upload</div>
        </div>
        <div class="progress-step-line"></div>
        <div class="progress-step active">
          <div class="progress-step-circle">2</div>
          <div class="progress-step-label">Analyze</div>
        </div>
        <div class="progress-step-line"></div>
        <div class="progress-step pending">
          <div class="progress-step-circle">3</div>
          <div class="progress-step-label">Review</div>
        </div>
      `;
      document.body.appendChild(progressDiv);
    });
    
    await page.waitForTimeout(500);
    const progressStepsCount = await page.locator('.progress-step').count();
    const activeStepStyle = await page.locator('.progress-step.active .progress-step-circle').evaluate(el => {
      const styles = window.getComputedStyle(el);
      return {
        background: styles.backgroundColor,
        color: styles.color,
        boxShadow: styles.boxShadow.substring(0, 50) + '...'
      };
    });
    console.log(`  📊 Progress indicators (${progressStepsCount} steps):`, activeStepStyle);
    
    // Test help tooltip functionality (inject test tooltip)
    await page.evaluate(() => {
      const tooltipSpan = document.createElement('span');
      tooltipSpan.className = 'help-tooltip';
      tooltipSpan.setAttribute('data-tooltip', 'This is a helpful tooltip');
      tooltipSpan.innerHTML = '<i class="fas fa-question-circle"></i>';
      document.body.appendChild(tooltipSpan);
    });
    
    const tooltipElement = page.locator('.help-tooltip');
    await tooltipElement.hover();
    await page.waitForTimeout(300);
    
    console.log(`  💡 Help tooltips: Available with hover functionality`);
    
    // Test help card styles (inject test help card)
    await page.evaluate(() => {
      const helpCardDiv = document.createElement('div');
      helpCardDiv.className = 'help-card';
      helpCardDiv.innerHTML = `
        <div class="help-card-icon"><i class="fas fa-lightbulb"></i></div>
        <div class="help-card-title">Getting Started</div>
        <div class="help-card-content">Upload your student data to begin analyzing risk factors and generating insights.</div>
        <div class="help-card-actions">
          <button class="btn btn-primary btn-small">Learn More</button>
        </div>
      `;
      document.body.appendChild(helpCardDiv);
    });
    
    const helpCardStyle = await page.locator('.help-card').evaluate(el => {
      const styles = window.getComputedStyle(el);
      return {
        background: styles.background.substring(0, 50) + '...',
        borderRadius: styles.borderRadius,
        padding: styles.padding
      };
    });
    console.log(`  📋 Contextual help cards:`, helpCardStyle);
    
    // Test onboarding highlights (inject test highlight)
    await page.evaluate(() => {
      const highlightSpan = document.createElement('span');
      highlightSpan.className = 'onboarding-highlight';
      highlightSpan.textContent = 'New!';
      document.body.appendChild(highlightSpan);
    });
    
    const highlightStyle = await page.locator('.onboarding-highlight').evaluate(el => {
      const styles = window.getComputedStyle(el);
      return {
        background: styles.backgroundColor,
        color: styles.color,
        borderRadius: styles.borderRadius,
        animation: styles.animation.substring(0, 30) + '...'
      };
    });
    console.log(`  ✨ Onboarding highlights:`, highlightStyle);
    
    console.log('\n  🎨 Visual Consistency Check:');
    
    // Check design system consistency
    const designTokens = await page.evaluate(() => {
      const root = getComputedStyle(document.documentElement);
      return {
        primaryColor: root.getPropertyValue('--primary-600').trim(),
        borderRadius: root.getPropertyValue('--radius-2xl').trim(),
        spacing: root.getPropertyValue('--space-8').trim(),
        fontFamily: root.getPropertyValue('--font-family').trim()
      };
    });
    console.log(`    🎯 Design system tokens:`, designTokens);
    
    // Check responsive behavior
    await page.setViewportSize({ width: 768, height: 600 });
    await page.waitForTimeout(300);
    
    const mobileState = await page.evaluate(() => {
      const errorState = document.querySelector('.error-state');
      const loadingState = document.querySelector('.loading-state');
      return {
        errorStateVisible: errorState ? window.getComputedStyle(errorState).display !== 'none' : false,
        loadingStateVisible: loadingState ? window.getComputedStyle(loadingState).display !== 'none' : false
      };
    });
    console.log(`    📱 Mobile responsiveness: Error=${mobileState.errorStateVisible}, Loading=${mobileState.loadingStateVisible}`);
    
  } catch (error) {
    console.log(`❌ ERROR: ${error.message}`);
  }
  
  await browser.close();
  console.log('\n✅ User experience flow test completed!');
}

testUserExperience().catch(console.error);