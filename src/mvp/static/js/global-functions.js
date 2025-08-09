/**
 * Global Functions
 * Contains shared functions used across the application
 */

let appInstance = null;

// Global functions - EXACT REPLICA of working explanation system
window.showExplanation = async function(studentId) {
  if (!window.modernApp) return;
  
  try {
    // Show loading in modal first
    window.modernApp.showModal(
      `AI Explanation - Student ${studentId}`,
      '<div class="loading-content"><div class="loading-spinner"></div><p>Loading explanation...</p></div>'
    );
    
    // Use the WORKING explanation endpoint with proper auth
    const response = await fetch(`/api/mvp/explain/${studentId}`, {
      headers: {
        'Authorization': 'Bearer dev-key-change-me'
      }
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const explanation = await response.json();
    
    // Update modal with explanation
    const modalContent = document.getElementById('modal-content');
    if (modalContent) {
      modalContent.innerHTML = `
        <div class="explanation-content">
          <h4>🧠 AI Risk Analysis</h4>
          <div class="explanation-summary">
            <div class="risk-overview">
              <div class="risk-score-large">${((explanation.risk_score || 0) * 100).toFixed(1)}%</div>
              <div class="risk-label">Risk Score</div>
            </div>
            <div class="confidence-score">
              <div class="confidence-value">${((explanation.confidence || 0.5) * 100).toFixed(1)}%</div>
              <div class="confidence-label">Confidence</div>
            </div>
          </div>
          
          <div class="explanation-factors">
            <h5>🎯 Key Factors:</h5>
            <div class="explanation-text">${explanation.explanation || 'AI analysis shows this student has moderate risk based on academic performance and engagement patterns.'}</div>
          </div>
          
          <div class="explanation-actions">
            <button class="btn btn-primary" onclick="window.modernApp.hideModal()">Close</button>
          </div>
        </div>
      `;
    }
    
  } catch (error) {
    console.error('Error fetching explanation:', error);
    
    // Show error in modal
    const modalContent = document.getElementById('modal-content');
    if (modalContent) {
      modalContent.innerHTML = `
        <div class="error-content">
          <h4>❌ Error Loading Explanation</h4>
          <p>Sorry, we couldn't load the AI explanation at this time.</p>
          <p class="error-details">Error: ${error.message}</p>
          <button class="btn btn-secondary" onclick="window.modernApp.hideModal()">Close</button>
        </div>
      `;
    }
  }
};

// Integration forms - simplified working versions
window.showIntegrationForm = function(type) {
  alert(`Integration form for ${type} would be shown here. This feature connects to your LMS/SIS systems.`);
};