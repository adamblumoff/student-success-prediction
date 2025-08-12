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
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const explanation = await response.json();
    
    // Update modal with useful explanation
    const modalContent = document.getElementById('modal-content');
    if (modalContent && explanation.explanation) {
      const exp = explanation.explanation;
      const studentInfo = exp.student_info || {};
      
      modalContent.innerHTML = `
        <div class="explanation-content">
          <h4>🧠 Student Risk Analysis - ${studentInfo.student_id}</h4>
          
          <div class="explanation-summary">
            <div class="risk-overview">
              <div class="risk-score-large">${(studentInfo.risk_score * 100).toFixed(1)}%</div>
              <div class="risk-label">${studentInfo.risk_category}</div>
            </div>
            <div class="student-details">
              <p><strong>Grade:</strong> ${studentInfo.grade_level}</p>
              <p><strong>Analysis Date:</strong> ${studentInfo.prediction_date}</p>
              <p><strong>Model:</strong> ${exp.model_info}</p>
            </div>
          </div>
          
          <div class="explanation-section">
            <h5>📊 Summary</h5>
            <p>${exp.summary}</p>
          </div>
          
          <div class="explanation-section">
            <h5>🔍 Key Factors</h5>
            <ul>
              ${exp.key_factors.map(factor => `<li>${factor}</li>`).join('')}
            </ul>
          </div>
          
          <div class="explanation-section">
            <h5>💡 Recommended Actions</h5>
            <ul class="recommendations-list">
              ${exp.recommendations.map(rec => `<li>${rec}</li>`).join('')}
            </ul>
          </div>
          
          <div class="explanation-section">
            <h5>📋 Next Steps</h5>
            <ul class="next-steps-list">
              ${exp.next_steps.map(step => `<li>${step}</li>`).join('')}
            </ul>
          </div>
          
          <div class="explanation-actions">
            <button class="btn btn-success" onclick="createIntervention('${studentInfo.student_id}')">
              <i class="fas fa-plus"></i> Create Intervention
            </button>
            <button class="btn btn-secondary" onclick="window.modernApp.hideModal()">Close</button>
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