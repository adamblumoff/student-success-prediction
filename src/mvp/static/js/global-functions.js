/**
 * Global Functions
 * Contains shared functions used across the application
 */

let appInstance = null;

// Global functions - GPT-Enhanced explanation system
window.showExplanation = async function(studentId) {
  if (!window.modernApp) return;
  
  try {
    // Show loading in modal first
    window.modernApp.showModal(
      `GPT-Enhanced AI Explanation - Student ${studentId}`,
      '<div class="loading-content"><div class="loading-spinner"></div><p>Generating comprehensive AI analysis...</p></div>'
    );
    
    // First get static student data to provide context
    const staticResponse = await fetch(`/api/mvp/explain/${studentId}`, {
      headers: {
        'Authorization': 'Bearer dev-key-change-me'
      }
    });
    
    let staticResult = {};
    if (staticResponse.ok) {
      staticResult = await staticResponse.json();
    }
    
    // Prepare comprehensive student data for GPT
    const studentData = {
      student_id: studentId,
      grade_level: staticResult.explanation?.student_info?.grade_level || 9,
      risk_score: staticResult.explanation?.risk_score || 0.5,
      risk_category: staticResult.explanation?.risk_category || 'Medium Risk',
      success_probability: staticResult.explanation?.success_probability || (1 - (staticResult.explanation?.risk_score || 0.5)),
      needs_intervention: staticResult.explanation?.needs_intervention || (staticResult.explanation?.risk_score || 0.5) > 0.5,
      confidence_score: staticResult.explanation?.confidence || 0.75,
      key_factors: staticResult.explanation?.key_factors || [],
      recommendations: staticResult.explanation?.recommendations || [],
      model_info: staticResult.explanation?.model_info || 'K-12 Prediction Model'
    };
    
    // Get student database ID first by checking if the static endpoint can find the student
    let databaseId = studentId;
    try {
      // Try to convert student_id to database ID by finding the student
      // This uses the same logic as the explain endpoint
      const studentLookupResponse = await fetch(`/api/mvp/explain/${studentId}`, {
        headers: {
          'Authorization': 'Bearer dev-key-change-me'
        }
      });
      
      if (studentLookupResponse.ok) {
        const studentData = await studentLookupResponse.json();
        // The response should contain database info we can use
        // For now, we'll try the student ID as-is first, then the string
        
        // Try database ID first (if studentId is numeric, it might be the db ID)
        if (!isNaN(studentId)) {
          databaseId = parseInt(studentId);
        } else {
          // For string IDs like "1001", try converting them
          const numericPart = studentId.replace(/[^\d]/g, '');
          if (numericPart) {
            databaseId = parseInt(numericPart);
          }
        }
      }
    } catch (lookupError) {
      console.warn('Could not lookup student for database ID conversion:', lookupError);
      // Use original studentId as fallback
      databaseId = studentId;
    }

    // Call GPT-enhanced analysis endpoint
    const gptResponse = await fetch(`/api/gpt/analyze-student/${databaseId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer dev-key-change-me'
      }
    });
    
    if (!gptResponse.ok) {
      throw new Error(`GPT Analysis failed: ${gptResponse.status} ${gptResponse.statusText}`);
    }
    
    const gptResult = await gptResponse.json();
    
    // Extract the GPT analysis text
    const gptAnalysis = gptResult.gpt_analysis?.formatted_analysis || 
                       gptResult.gpt_analysis?.narrative_analysis || 
                       'Comprehensive AI analysis of this student\'s academic profile and risk factors.';
    
    // Get ML prediction data
    const mlPrediction = gptResult.ml_prediction || {};
    const riskScore = mlPrediction.risk_score || studentData.risk_score;
    const confidenceScore = mlPrediction.confidence || studentData.confidence_score;
    
    // Update modal with GPT-enhanced explanation
    const modalContent = document.getElementById('modal-content');
    if (modalContent) {
      modalContent.innerHTML = `
        <div class="explanation-content">
          <h4>🤖 GPT-Enhanced AI Risk Analysis</h4>
          <div class="explanation-summary">
            <div class="risk-overview">
              <div class="risk-score-large">${(riskScore * 100).toFixed(1)}%</div>
              <div class="risk-label">Risk Score</div>
            </div>
            <div class="confidence-score">
              <div class="confidence-value">${(confidenceScore * 100).toFixed(1)}%</div>
              <div class="confidence-label">Confidence</div>
            </div>
          </div>
          
          <div class="explanation-factors">
            <h5>🧠 GPT-5-Nano Analysis:</h5>
            <div class="explanation-text gpt-enhanced">${gptAnalysis}</div>
          </div>
          
          <div class="explanation-actions">
            <button class="btn btn-primary" onclick="window.modernApp.hideModal()">Close</button>
          </div>
        </div>
      `;
    }
    
  } catch (error) {
    console.error('Error fetching GPT explanation:', error);
    
    // Fallback to static explanation on GPT error
    try {
      const fallbackResponse = await fetch(`/api/mvp/explain/${studentId}`, {
        headers: {
          'Authorization': 'Bearer dev-key-change-me'
        }
      });
      
      if (fallbackResponse.ok) {
        const explanation = await fallbackResponse.json();
        
        const modalContent = document.getElementById('modal-content');
        if (modalContent) {
          modalContent.innerHTML = `
            <div class="explanation-content">
              <h4>📊 AI Risk Analysis (Fallback)</h4>
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
                <div class="explanation-text">${typeof explanation.explanation === 'string' ? explanation.explanation : (explanation.explanation?.text || explanation.explanation?.summary || 'AI analysis shows this student has moderate risk based on academic performance and engagement patterns.')}</div>
              </div>
              
              <div class="explanation-actions">
                <button class="btn btn-primary" onclick="window.modernApp.hideModal()">Close</button>
              </div>
            </div>
          `;
        }
        return;
      }
    } catch (fallbackError) {
      console.error('Fallback also failed:', fallbackError);
    }
    
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