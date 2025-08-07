/**
 * Explainable AI UI Components
 * 
 * Provides interactive visualization of prediction explanations,
 * feature importance, and risk factor analysis for educators.
 */

class ExplainableUI {
    constructor() {
        this.currentExplanation = null;
        this.globalInsights = null;
        this.init();
    }

    init() {
        this.loadGlobalInsights();
    }

    async loadGlobalInsights() {
        try {
            const response = await fetch('/api/mvp/insights');

            if (response.ok) {
                const result = await response.json();
                console.log('Global insights loaded:', result);
                this.globalInsights = result.insights;
                this.renderGlobalInsights();
            } else {
                console.error('Failed to load global insights:', response.status);
            }
        } catch (error) {
            console.error('Error loading global insights:', error);
        }
    }

    renderGlobalInsights() {
        if (!this.globalInsights) return;

        // Create insights panel if it doesn't exist
        let insightsPanel = document.getElementById('insights-panel');
        if (!insightsPanel) {
            insightsPanel = this.createInsightsPanel();
            document.querySelector('.container').appendChild(insightsPanel);
        }

        const insightsContent = document.getElementById('insights-content');
        
        // Render feature importance
        const featureImportanceHTML = this.renderFeatureImportance(
            this.globalInsights.feature_importance || {}
        );
        
        // Render category importance
        const categoryImportanceHTML = this.renderCategoryImportance(
            this.globalInsights.category_importance || {}
        );

        // Render top risk factors
        const riskFactorsHTML = this.renderTopRiskFactors(
            this.globalInsights.top_risk_factors || []
        );

        insightsContent.innerHTML = `
            <div class="insights-grid">
                <div class="insight-card">
                    <h4>🔍 Top Predictive Features</h4>
                    ${featureImportanceHTML}
                </div>
                <div class="insight-card">
                    <h4>📊 Feature Categories</h4>
                    ${categoryImportanceHTML}
                </div>
                <div class="insight-card">
                    <h4>⚠️ Key Risk Indicators</h4>
                    ${riskFactorsHTML}
                </div>
            </div>
        `;
    }

    createInsightsPanel() {
        const panel = document.createElement('section');
        panel.id = 'insights-panel';
        panel.className = 'insights-section';
        panel.innerHTML = `
            <div class="card">
                <div class="step-header">
                    <span class="step-number">🧠</span>
                    <h2>Model Insights</h2>
                    <p>Understand what factors most influence student success predictions</p>
                </div>
                <div id="insights-content">
                    <div class="loading-spinner">
                        <div class="spinner"></div>
                        <p>Loading model insights...</p>
                    </div>
                </div>
            </div>
        `;
        return panel;
    }

    renderFeatureImportance(features) {
        if (Object.keys(features).length === 0) {
            return '<p>No feature importance data available</p>';
        }

        const maxImportance = Math.max(...Object.values(features));
        
        return Object.entries(features)
            .slice(0, 5)
            .map(([feature, importance]) => {
                const percentage = (importance / maxImportance) * 100;
                const displayName = this.getFeatureDisplayName(feature);
                
                return `
                    <div class="feature-bar">
                        <div class="feature-name">${displayName}</div>
                        <div class="feature-bar-container">
                            <div class="feature-bar-fill" style="width: ${percentage}%"></div>
                            <span class="feature-importance">${(importance * 100).toFixed(1)}%</span>
                        </div>
                    </div>
                `;
            }).join('');
    }

    renderCategoryImportance(categories) {
        if (Object.keys(categories).length === 0) {
            return '<p>No category data available</p>';
        }

        return Object.entries(categories)
            .sort(([,a], [,b]) => b - a)
            .map(([category, importance]) => {
                const displayName = this.getCategoryDisplayName(category);
                const color = this.getCategoryColor(category);
                
                return `
                    <div class="category-item">
                        <div class="category-indicator" style="background-color: ${color}"></div>
                        <div class="category-info">
                            <div class="category-name">${displayName}</div>
                            <div class="category-importance">${(importance * 100).toFixed(1)}% importance</div>
                        </div>
                    </div>
                `;
            }).join('');
    }

    renderTopRiskFactors(riskFactors) {
        if (riskFactors.length === 0) {
            return '<p>No risk factor data available</p>';
        }

        return riskFactors.map(factor => `
            <div class="risk-factor-item">
                <div class="risk-factor-name">${this.getFeatureDisplayName(factor.feature || 'unknown')}</div>
                <div class="risk-factor-description">${factor.description || 'No description available'}</div>
                <div class="risk-factor-category">${this.getCategoryDisplayName(factor.category || 'general')}</div>
            </div>
        `).join('');
    }

    async showStudentExplanation(studentId) {
        console.log(`Showing explanation for student ${studentId}`);
        try {
            // Ensure studentId is properly formatted (convert to integer if needed)
            const normalizedId = parseInt(studentId) || studentId;
            console.log(`Normalized student ID: ${normalizedId}`);
            
            const response = await fetch(`/api/mvp/explain/${normalizedId}`, {
                headers: {
                    'Authorization': 'Bearer dev-key-change-me'
                }
            });

            if (response.ok) {
                const result = await response.json();
                console.log('Explanation result:', result);
                this.currentExplanation = result.explanation;
                this.renderStudentExplanation(studentId);
            } else {
                console.error('Failed to load student explanation:', response.status, response.statusText);
                // Try to get the error message from the response
                try {
                    const errorData = await response.json();
                    alert(`Failed to load explanation: ${errorData.detail || 'Unknown error'} (${response.status})`);
                } catch {
                    alert(`Failed to load detailed explanation for this student (${response.status})`);
                }
            }
        } catch (error) {
            console.error('Error loading student explanation:', error);
            alert('Error loading student explanation: ' + error.message);
        }
    }

    renderStudentExplanation(studentId) {
        if (!this.currentExplanation) return;

        const modal = document.getElementById('student-modal');
        const modalBody = document.getElementById('modal-body');
        const modalTitle = document.getElementById('modal-student-name');

        modalTitle.textContent = `Detailed Analysis - Student ${studentId}`;

        const explanation = this.currentExplanation;
        
        modalBody.innerHTML = `
            <div class="explanation-content">
                <!-- Risk Overview -->
                <div class="explanation-section">
                    <h4>📊 Risk Assessment</h4>
                    <div class="risk-overview">
                        <div class="risk-score-display">
                            <div class="risk-score-value ${this.getRiskScoreClass(explanation.risk_score)}">
                                ${(explanation.risk_score * 100).toFixed(0)}%
                            </div>
                            <div class="risk-category">${explanation.risk_category}</div>
                        </div>
                        <div class="confidence-score">
                            <span>Confidence: ${(explanation.confidence * 100).toFixed(0)}%</span>
                        </div>
                    </div>
                </div>

                <!-- AI Explanation -->
                <div class="explanation-section">
                    <h4>🤖 AI Explanation</h4>
                    <div class="explanation-narrative">
                        ${explanation.explanation}
                    </div>
                </div>

                <!-- Risk Factors -->
                ${explanation.risk_factors && explanation.risk_factors.length > 0 ? `
                <div class="explanation-section">
                    <h4>⚠️ Key Risk Factors</h4>
                    <div class="risk-factors-list">
                        ${this.renderStudentRiskFactors(explanation.risk_factors)}
                    </div>
                </div>
                ` : ''}

                <!-- Protective Factors -->
                ${explanation.protective_factors && explanation.protective_factors.length > 0 ? `
                <div class="explanation-section">
                    <h4>✅ Strengths & Protective Factors</h4>
                    <div class="protective-factors-list">
                        ${this.renderProtectiveFactors(explanation.protective_factors)}
                    </div>
                </div>
                ` : ''}

                <!-- Recommendations -->
                ${explanation.recommendations && explanation.recommendations.length > 0 ? `
                <div class="explanation-section">
                    <h4>💡 Actionable Recommendations</h4>
                    <div class="recommendations-list">
                        ${explanation.recommendations.map(rec => `
                            <div class="recommendation-item">• ${rec}</div>
                        `).join('')}
                    </div>
                </div>
                ` : ''}
            </div>
        `;

        modal.classList.remove('hidden');
    }

    renderStudentRiskFactors(riskFactors) {
        return riskFactors.map(factor => `
            <div class="risk-factor-detail">
                <div class="factor-header">
                    <span class="factor-name">${this.getFeatureDisplayName(factor.feature)}</span>
                    <span class="factor-severity severity-${factor.severity}">${factor.severity}</span>
                </div>
                <div class="factor-description">${factor.description}</div>
                <div class="factor-details">
                    <span class="factor-category">${this.getCategoryDisplayName(factor.category)}</span>
                    <span class="factor-value">Value: ${factor.value}</span>
                </div>
            </div>
        `).join('');
    }

    renderProtectiveFactors(protectiveFactors) {
        return protectiveFactors.map(factor => `
            <div class="protective-factor-detail">
                <div class="factor-header">
                    <span class="factor-name">${this.getFeatureDisplayName(factor.feature)}</span>
                    <span class="protective-strength">+${(factor.protective_effect * 100).toFixed(0)}%</span>
                </div>
                <div class="factor-description">${factor.description}</div>
                <div class="factor-category">${this.getCategoryDisplayName(factor.category)}</div>
            </div>
        `).join('');
    }

    getFeatureDisplayName(feature) {
        const displayNames = {
            'early_avg_score': 'Average Assignment Score',
            'early_total_clicks': 'Learning Platform Engagement',
            'early_active_days': 'Active Study Days',
            'early_missing_submissions': 'Missing Assignments',
            'early_submission_rate': 'Assignment Submission Rate',
            'num_of_prev_attempts': 'Previous Course Attempts',
            'registration_delay': 'Registration Timing',
            'early_last_access': 'Recent Platform Access',
            'early_engagement_consistency': 'Engagement Consistency',
            'early_min_score': 'Lowest Assignment Score',
            'early_max_score': 'Highest Assignment Score',
            'early_clicks_per_active_day': 'Daily Engagement Level',
            'studied_credits': 'Course Credit Load',
            'has_disability': 'Disability Support Needs',
            'age_band_encoded': 'Age Group',
            'education_encoded': 'Educational Background',
            'current_gpa': 'Current GPA',
            'attendance_rate': 'Attendance Rate',
            'assignment_completion': 'Assignment Completion',
            'family_communication_quality': 'Family Communication'
        };
        
        return displayNames[feature] || (feature ? feature.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) : 'Unknown Feature');
    }

    getCategoryDisplayName(category) {
        const displayNames = {
            'demographics': 'Demographics',
            'academic_history': 'Academic History',
            'engagement': 'Course Engagement',
            'assessment_performance': 'Assignment Performance',
            'academic': 'Academic Performance',
            'family': 'Family Factors'
        };
        
        return displayNames[category] || (category ? category.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) : 'General');
    }

    getCategoryColor(category) {
        const colors = {
            'demographics': '#6366f1',
            'academic_history': '#8b5cf6',
            'engagement': '#06b6d4',
            'assessment_performance': '#10b981'
        };
        
        return colors[category] || '#6b7280';
    }

    getRiskScoreClass(riskScore) {
        if (riskScore >= 0.7) return 'risk-high';
        if (riskScore >= 0.4) return 'risk-medium';
        return 'risk-low';
    }

    // Method to enhance existing student display with explainable AI buttons
    enhanceStudentCards() {
        console.log('EnhanceStudentCards called');
        const studentCards = document.querySelectorAll('.student-card');
        console.log(`Found ${studentCards.length} student cards`);
        
        studentCards.forEach((card, index) => {
            console.log(`Processing card ${index + 1}`);
            
            // Check if we already added the explain button
            if (card.querySelector('.explain-button')) {
                console.log(`Card ${index + 1} already has explain button`);
                return;
            }
            
            // Extract student ID from the card
            const studentNameElement = card.querySelector('.student-name');
            if (!studentNameElement) {
                console.log(`Card ${index + 1}: No student name element found`);
                return;
            }
            
            console.log(`Card ${index + 1}: Student name text = "${studentNameElement.textContent}"`);
            const studentIdMatch = studentNameElement.textContent.match(/Student #(\d+)/);
            if (!studentIdMatch) {
                console.log(`Card ${index + 1}: No student ID match found`);
                return;
            }
            
            const studentId = studentIdMatch[1];
            console.log(`Card ${index + 1}: Extracted student ID = ${studentId}`);
            
            // Add explain button to the existing interventions preview
            const interventionsPreview = card.querySelector('.interventions-preview');
            if (interventionsPreview) {
                console.log(`Card ${index + 1}: Adding explain button`);
                const explainButton = document.createElement('div');
                explainButton.className = 'intervention-item explain-button';
                explainButton.innerHTML = `
                    <span class="intervention-text" onclick="explainableUI.showStudentExplanation(${studentId})" style="cursor: pointer; color: #2563eb; text-decoration: underline;">
                        🔍 Explain AI Prediction
                    </span>
                    <span class="intervention-status available">Available</span>
                `;
                interventionsPreview.appendChild(explainButton);
                console.log(`Card ${index + 1}: Explain button added successfully`);
            } else {
                console.log(`Card ${index + 1}: No interventions preview found`);
            }
        });
    }
}

// Initialize explainable UI and make it globally available
window.explainableUI = new ExplainableUI();