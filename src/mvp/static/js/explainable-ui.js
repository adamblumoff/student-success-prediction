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
            const response = await fetch('/api/mvp/insights', {
                headers: {
                    'Authorization': 'Bearer dev-key-change-me'
                }
            });

            if (response.ok) {
                const result = await response.json();
                this.globalInsights = result.insights;
                this.renderGlobalInsights();
            } else {
                console.error('Failed to load global insights');
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
                <div class="risk-factor-name">${this.getFeatureDisplayName(factor.feature)}</div>
                <div class="risk-factor-description">${factor.description}</div>
                <div class="risk-factor-category">${this.getCategoryDisplayName(factor.category)}</div>
            </div>
        `).join('');
    }

    async showStudentExplanation(studentId) {
        try {
            const response = await fetch(`/api/mvp/explain/${studentId}`, {
                headers: {
                    'Authorization': 'Bearer dev-key-change-me'
                }
            });

            if (response.ok) {
                const result = await response.json();
                this.currentExplanation = result.explanation;
                this.renderStudentExplanation(studentId);
            } else {
                console.error('Failed to load student explanation');
                alert('Failed to load detailed explanation for this student');
            }
        } catch (error) {
            console.error('Error loading student explanation:', error);
            alert('Error loading student explanation');
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
            'education_encoded': 'Educational Background'
        };
        
        return displayNames[feature] || feature.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }

    getCategoryDisplayName(category) {
        const displayNames = {
            'demographics': 'Demographics',
            'academic_history': 'Academic History',
            'engagement': 'Course Engagement',
            'assessment_performance': 'Assignment Performance'
        };
        
        return displayNames[category] || category.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
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
}

// Enhanced student list rendering with explanation buttons
window.renderStudentsWithExplanations = function(students) {
    const studentsList = document.getElementById('students-list');
    
    if (students.length === 0) {
        studentsList.innerHTML = '<p>No students analyzed yet.</p>';
        return;
    }

    const studentsHTML = students.map(student => {
        const riskClass = student.risk_category.toLowerCase().replace(' ', '-');
        
        return `
            <div class="student-card ${riskClass}">
                <div class="student-info">
                    <div class="student-header">
                        <h4>Student ${student.id_student}</h4>
                        <span class="risk-badge ${riskClass}">${student.risk_category}</span>
                    </div>
                    <div class="student-metrics">
                        <div class="metric">
                            <span class="metric-label">Risk Score:</span>
                            <span class="metric-value">${(student.risk_score * 100).toFixed(0)}%</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Success Probability:</span>
                            <span class="metric-value">${(student.success_probability * 100).toFixed(0)}%</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Avg Score:</span>
                            <span class="metric-value">${student.early_avg_score?.toFixed(1) || 'N/A'}</span>
                        </div>
                    </div>
                </div>
                <div class="student-actions">
                    <button class="btn btn-secondary btn-sm" onclick="explainableUI.showStudentExplanation(${student.id_student})">
                        🔍 Explain Prediction
                    </button>
                    ${student.needs_intervention ? `
                        <button class="btn btn-warning btn-sm" onclick="showInterventionModal(${student.id_student})">
                            💡 View Interventions
                        </button>
                    ` : ''}
                </div>
            </div>
        `;
    }).join('');

    studentsList.innerHTML = studentsHTML;
}

// Initialize explainable UI
const explainableUI = new ExplainableUI();