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

    showLoadingModal(studentId, message = 'Loading...') {
        const modal = document.getElementById('student-modal');
        const modalBody = document.getElementById('modal-body');
        const modalTitle = document.getElementById('modal-student-name');

        modalTitle.textContent = `Student ${studentId}`;
        modalBody.innerHTML = `
            <div class="loading-container" style="text-align: center; padding: 40px;">
                <div class="loading-spinner" style="margin-bottom: 20px;">
                    <div class="spinner" style="
                        border: 4px solid #f3f3f3;
                        border-top: 4px solid #3498db;
                        border-radius: 50%;
                        width: 40px;
                        height: 40px;
                        animation: spin 2s linear infinite;
                        margin: 0 auto;
                    "></div>
                </div>
                <div class="loading-message" style="color: #666; font-size: 16px;">
                    🧠 ${message}
                </div>
            </div>
            <style>
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
            </style>
        `;
        
        // Show the modal
        modal.style.display = 'block';
    }

    async showStudentExplanation(studentId) {
        console.log(`🧠 Showing GPT-enhanced explanation for student ${studentId}`);
        try {
            // Ensure studentId is properly formatted (convert to integer if needed)
            const normalizedId = parseInt(studentId) || studentId;
            console.log(`Normalized student ID: ${normalizedId}`);
            
            // Show loading indicator
            this.showLoadingModal(studentId, 'Generating AI-powered analysis...');
            
            // First, get basic student data for GPT analysis
            const staticResponse = await fetch(`/api/mvp/explain/${normalizedId}`, {
                headers: {
                    'Authorization': 'Bearer 0dUHi4QroC1GfgnbibLbqowUnv2YFWIe'
                }
            });

            let studentData = {};
            let staticExplanation = null;
            
            if (staticResponse.ok) {
                const staticResult = await staticResponse.json();
                staticExplanation = staticResult.explanation;
                
                // Extract comprehensive student data for GPT
                studentData = {
                    student_id: normalizedId,
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
            } else {
                console.warn('Static explanation not available, using basic student data');
                studentData = {
                    student_id: normalizedId,
                    grade_level: 9,
                    gpa: 2.5,
                    attendance_rate: 0.8,
                    risk_category: 'Medium Risk',
                    risk_score: 0.5,
                    needs_intervention: true
                };
            }

            // Now get GPT-enhanced analysis
            console.log('🤖 Calling GPT-5-nano for enhanced analysis...');
            const gptResponse = await fetch('/api/gpt/quick-insight', {
                method: 'POST',
                headers: {
                    'Authorization': 'Bearer 0dUHi4QroC1GfgnbibLbqowUnv2YFWIe',
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    student_data: studentData,
                    question: `Analyze this ${studentData.risk_category.toLowerCase()} student comprehensively:

STUDENT PROFILE:
- ID: ${studentData.student_id}
- Grade: ${studentData.grade_level}
- Risk Score: ${Math.round(studentData.risk_score * 100)}%
- Success Probability: ${Math.round(studentData.success_probability * 100)}%
- Needs Intervention: ${studentData.needs_intervention ? 'Yes' : 'No'}
- Model Confidence: ${Math.round(studentData.confidence_score * 100)}%
- Existing Risk Factors: ${studentData.key_factors.length > 0 ? studentData.key_factors.join(', ') : 'To be determined through assessment'}
- Current Recommendations: ${studentData.recommendations.length > 0 ? studentData.recommendations.join('; ') : 'Need updated guidance'}

ANALYSIS REQUEST:
Provide a comprehensive educational analysis including:
1. Detailed risk factor assessment with specific indicators
2. Evidence-based intervention strategies with implementation timelines
3. Multi-tiered support approach (Tier 1, 2, 3 interventions)
4. Family engagement recommendations
5. Progress monitoring metrics
6. Early warning signs to watch for
7. Success indicators to celebrate

Focus on actionable, research-backed strategies that teachers and school teams can implement within the next 2 weeks.`
                })
            });

            if (gptResponse.ok) {
                const gptResult = await gptResponse.json();
                console.log('✅ GPT analysis completed:', gptResult);
                
                // Combine static data with GPT insights
                this.currentExplanation = {
                    ...staticExplanation,
                    gpt_analysis: gptResult.insight,
                    gpt_enhanced: true,
                    processing_time: gptResult.processing_time_seconds
                };
                
                this.renderStudentExplanation(studentId);
            } else {
                console.error('❌ GPT analysis failed, falling back to static explanation');
                // Fallback to static explanation
                this.currentExplanation = staticExplanation;
                this.renderStudentExplanation(studentId);
            }
            
        } catch (error) {
            console.error('Error loading student explanation:', error);
            // Fallback to basic explanation
            this.currentExplanation = {
                summary: 'Analysis temporarily unavailable',
                key_factors: ['Please try again in a moment'],
                recommendations: ['Contact your administrator if this persists'],
                student_info: { student_id: studentId }
            };
            this.renderStudentExplanation(studentId);
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

                <!-- GPT-Enhanced AI Analysis -->
                ${explanation.gpt_enhanced && explanation.gpt_analysis ? `
                <div class="explanation-section gpt-enhanced">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                        <h4>🧠 GPT-5-nano Analysis</h4>
                        <div class="gpt-badge" style="background: #10b981; color: white; padding: 4px 8px; border-radius: 12px; font-size: 12px;">
                            ⚡ ${explanation.processing_time ? `${explanation.processing_time.toFixed(1)}s` : 'AI-Powered'}
                        </div>
                    </div>
                    <div class="gpt-analysis-content" style="
                        background: linear-gradient(135deg, #f0fdf4 0%, #ecfdf5 100%);
                        border-left: 4px solid #10b981;
                        padding: 20px;
                        border-radius: 8px;
                        font-size: 14px;
                        line-height: 1.6;
                        white-space: pre-wrap;
                        max-height: 400px;
                        overflow-y: auto;
                    ">
                        ${explanation.gpt_analysis}
                    </div>
                </div>
                ` : `
                <!-- Traditional AI Explanation -->
                <div class="explanation-section">
                    <h4>🤖 AI Explanation</h4>
                    <div class="explanation-narrative">
                        ${explanation.explanation || explanation.summary || 'Analysis not available'}
                    </div>
                </div>
                `}

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