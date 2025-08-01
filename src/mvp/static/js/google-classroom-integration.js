/**
 * Google Classroom Integration JavaScript
 * 
 * Provides comprehensive frontend integration for Google Classroom features
 * including OAuth2 flow, course management, student analytics, and cross-platform insights.
 * 
 * Features:
 * - Google Classroom OAuth2 authentication
 * - Real-time course and student data sync
 * - Enhanced engagement analytics dashboard
 * - Cross-platform comparison visualizations
 * - Risk assessment with Google-specific insights
 */

class GoogleClassroomIntegration {
    constructor() {
        this.apiBase = '/api/google';
        this.isAuthenticated = false;
        this.courses = [];
        this.currentCourse = null;
        this.students = [];
        this.syncInProgress = false;
        
        this.initializeEventListeners();
        this.checkAuthenticationStatus();
        
        console.log('🎓 Google Classroom Integration initialized');
    }
    
    initializeEventListeners() {
        // Authentication buttons
        document.getElementById('google-auth-btn')?.addEventListener('click', () => this.startAuthentication());
        document.getElementById('google-disconnect-btn')?.addEventListener('click', () => this.disconnect());
        
        // Course management
        document.getElementById('google-sync-courses-btn')?.addEventListener('click', () => this.syncCourses());
        document.getElementById('google-course-select')?.addEventListener('change', (e) => this.selectCourse(e.target.value));
        
        // Student analysis
        document.getElementById('google-analyze-students-btn')?.addEventListener('click', () => this.analyzeStudents());
        document.getElementById('google-enhanced-predictions-btn')?.addEventListener('click', () => this.generateEnhancedPredictions());
        
        // Cross-platform analytics
        document.getElementById('google-cross-platform-btn')?.addEventListener('click', () => this.showCrossPlatformAnalytics());
        
        // Refresh buttons
        document.querySelector('.google-refresh-btn')?.addEventListener('click', () => this.refreshData());
    }
    
    async checkAuthenticationStatus() {
        try {
            const response = await fetch(`${this.apiBase}/health`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('api_key') || 'dev-key-change-me'}`
                }
            });
            
            const health = await response.json();
            this.isAuthenticated = health.authentication && health.api_access;
            
            this.updateAuthenticationUI();
            
        } catch (error) {
            console.error('❌ Failed to check Google Classroom authentication:', error);
            this.showError('Failed to check authentication status');
        }
    }
    
    async startAuthentication() {
        try {
            this.showStatus('🔄 Starting Google Classroom authentication...', 'info');
            
            const response = await fetch(`${this.apiBase}/auth/start`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('api_key') || 'dev-key-change-me'}`
                },
                body: JSON.stringify({
                    redirect_uri: window.location.origin + '/google-auth-callback'
                })
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.showGoogleAuthModal(result);
            } else {
                throw new Error(result.detail || 'Authentication failed');
            }
            
        } catch (error) {
            console.error('❌ Google authentication failed:', error);
            this.showError(`Authentication failed: ${error.message}`);
        }
    }
    
    showGoogleAuthModal(authInfo) {
        const modal = document.createElement('div');
        modal.className = 'google-auth-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>🎓 Google Classroom Authentication</h3>
                    <button class="close-btn" onclick="this.closest('.google-auth-modal').remove()">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="auth-instructions">
                        <h4>Authentication Process:</h4>
                        <ol>
                            ${authInfo.instructions.map(instruction => `<li>${instruction}</li>`).join('')}
                        </ol>
                    </div>
                    
                    <div class="auth-scopes">
                        <h4>Required Permissions:</h4>
                        <ul>
                            ${authInfo.scopes.map(scope => `<li>${scope.replace('classroom.', '').replace(/([A-Z])/g, ' $1')}</li>`).join('')}
                        </ul>
                    </div>
                    
                    <div class="auth-actions">
                        <button class="btn btn-primary" onclick="googleClassroom.simulateAuthSuccess()">
                            Simulate Authentication Success
                        </button>
                        <button class="btn btn-secondary" onclick="this.closest('.google-auth-modal').remove()">
                            Cancel
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
    }
    
    async simulateAuthSuccess() {
        try {
            // Close modal
            document.querySelector('.google-auth-modal')?.remove();
            
            this.showStatus('🔄 Completing authentication...', 'info');
            
            const response = await fetch(`${this.apiBase}/auth/complete`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('api_key') || 'dev-key-change-me'}`
                },
                body: JSON.stringify({
                    authorization_code: 'demo_auth_code_12345'
                })
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.isAuthenticated = true;
                this.updateAuthenticationUI();
                this.showStatus('✅ Google Classroom authentication successful!', 'success');
                this.syncCourses(); // Auto-sync courses after authentication
            } else {
                throw new Error(result.detail || 'Authentication completion failed');
            }
            
        } catch (error) {
            console.error('❌ Authentication completion failed:', error);
            this.showError(`Authentication completion failed: ${error.message}`);
        }
    }
    
    updateAuthenticationUI() {
        const authSection = document.getElementById('google-auth-section');
        const mainSection = document.getElementById('google-main-section');
        const statusIndicator = document.getElementById('google-auth-status');
        
        if (!authSection || !mainSection) return;
        
        if (this.isAuthenticated) {
            authSection.style.display = 'none';
            mainSection.style.display = 'block';
            if (statusIndicator) {
                statusIndicator.className = 'status-indicator connected';
                statusIndicator.textContent = '✅ Connected to Google Classroom';
            }
        } else {
            authSection.style.display = 'block';
            mainSection.style.display = 'none';
            if (statusIndicator) {
                statusIndicator.className = 'status-indicator disconnected';
                statusIndicator.textContent = '❌ Not connected to Google Classroom';
            }
        }
    }
    
    async syncCourses() {
        if (!this.isAuthenticated) {
            this.showError('Please authenticate with Google Classroom first');
            return;
        }
        
        try {
            this.showStatus('🔄 Syncing Google Classroom courses...', 'info');
            
            const response = await fetch(`${this.apiBase}/courses`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('api_key') || 'dev-key-change-me'}`
                }
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.courses = data.courses;
                this.updateCoursesUI(data);
                this.showStatus(`✅ Synced ${data.courses.length} Google Classroom courses`, 'success');
            } else {
                throw new Error(data.detail || 'Failed to sync courses');
            }
            
        } catch (error) {
            console.error('❌ Course sync failed:', error);
            this.showError(`Course sync failed: ${error.message}`);
        }
    }
    
    updateCoursesUI(courseData) {
        const courseSelect = document.getElementById('google-course-select');
        const courseStats = document.getElementById('google-course-stats');
        
        if (courseSelect) {
            courseSelect.innerHTML = '<option value="">Select a Google Classroom course...</option>';
            this.courses.forEach(course => {
                const option = document.createElement('option');
                option.value = course.course_id;
                option.textContent = `${course.name} (${course.enrollment_count} students)`;
                courseSelect.appendChild(option);
            });
        }
        
        if (courseStats) {
            courseStats.innerHTML = `
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-value">${courseData.total_courses}</div>
                        <div class="stat-label">Total Courses</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${courseData.active_courses}</div>
                        <div class="stat-label">Active Courses</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${courseData.total_students}</div>
                        <div class="stat-label">Total Students</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${(courseData.avg_engagement * 100).toFixed(1)}%</div>
                        <div class="stat-label">Avg Engagement</div>
                    </div>
                </div>
            `;
        }
    }
    
    selectCourse(courseId) {
        if (!courseId) {
            this.currentCourse = null;
            return;
        }
        
        this.currentCourse = this.courses.find(c => c.course_id === courseId);
        if (this.currentCourse) {
            this.showStatus(`Selected: ${this.currentCourse.name}`, 'info');
            this.updateCourseDetailsUI();
        }
    }
    
    updateCourseDetailsUI() {
        const courseDetails = document.getElementById('google-course-details');
        if (!courseDetails || !this.currentCourse) return;
        
        courseDetails.innerHTML = `
            <div class="course-info-card">
                <h4>${this.currentCourse.name}</h4>
                <p>${this.currentCourse.description}</p>
                
                <div class="course-metrics">
                    <div class="metric">
                        <span class="metric-label">Enrollment:</span>
                        <span class="metric-value">${this.currentCourse.enrollment_count} students</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Engagement Rate:</span>
                        <span class="metric-value">${(this.currentCourse.avg_engagement_rate * 100).toFixed(1)}%</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Assignment Frequency:</span>
                        <span class="metric-value">${this.currentCourse.assignment_frequency}/week</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Resources:</span>
                        <span class="metric-value">${this.currentCourse.resource_count} items</span>
                    </div>
                </div>
                
                <div class="course-actions">
                    <button class="btn btn-primary" onclick="googleClassroom.syncCourseData()">
                        Sync Course Data
                    </button>
                    <button class="btn btn-secondary" onclick="googleClassroom.analyzeStudents()">
                        Analyze Students
                    </button>
                </div>
            </div>
        `;
    }
    
    async syncCourseData() {
        if (!this.currentCourse) {
            this.showError('Please select a course first');
            return;
        }
        
        try {
            this.syncInProgress = true;
            this.showStatus('🔄 Syncing course data...', 'info');
            
            const response = await fetch(`${this.apiBase}/courses/sync`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('api_key') || 'dev-key-change-me'}`
                },
                body: JSON.stringify({
                    course_id: this.currentCourse.course_id,
                    include_assignments: true,
                    include_engagement: true
                })
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.updateSyncProgressUI(result);
                this.showStatus('✅ Course data sync initiated', 'success');
            } else {
                throw new Error(result.detail || 'Course sync failed');
            }
            
        } catch (error) {
            console.error('❌ Course data sync failed:', error);
            this.showError(`Course sync failed: ${error.message}`);
        } finally {
            this.syncInProgress = false;
        }
    }
    
    updateSyncProgressUI(syncResult) {
        const progressSection = document.getElementById('google-sync-progress');
        if (!progressSection) return;
        
        progressSection.innerHTML = `
            <div class="sync-progress-card">
                <h4>📊 Sync Progress: ${syncResult.sync_result.course_name}</h4>
                
                <div class="progress-stats">
                    <div class="progress-stat">
                        <span class="stat-label">Students Processed:</span>
                        <span class="stat-value">${syncResult.sync_result.students_processed}/${syncResult.sync_result.total_students}</span>
                    </div>
                    <div class="progress-stat">
                        <span class="stat-label">Assignments Processed:</span>
                        <span class="stat-value">${syncResult.sync_result.assignments_processed}/${syncResult.sync_result.total_assignments}</span>
                    </div>
                    <div class="progress-stat">
                        <span class="stat-label">Data Quality Score:</span>
                        <span class="stat-value">${(syncResult.sync_result.data_quality.data_quality_score * 100).toFixed(1)}%</span>
                    </div>
                </div>
                
                <div class="engagement-distribution">
                    <h5>Student Engagement Distribution:</h5>
                    <div class="distribution-bars">
                        <div class="bar-item">
                            <span class="bar-label">High Engagement:</span>
                            <div class="bar">
                                <div class="bar-fill" style="width: ${(syncResult.sync_result.sync_statistics.high_engagement_students / syncResult.sync_result.total_students * 100)}%"></div>
                                <span class="bar-value">${syncResult.sync_result.sync_statistics.high_engagement_students}</span>
                            </div>
                        </div>
                        <div class="bar-item">
                            <span class="bar-label">Medium Engagement:</span>
                            <div class="bar">
                                <div class="bar-fill" style="width: ${(syncResult.sync_result.sync_statistics.medium_engagement_students / syncResult.sync_result.total_students * 100)}%"></div>
                                <span class="bar-value">${syncResult.sync_result.sync_statistics.medium_engagement_students}</span>
                            </div>
                        </div>
                        <div class="bar-item">
                            <span class="bar-label">At Risk:</span>
                            <div class="bar">
                                <div class="bar-fill at-risk" style="width: ${(syncResult.sync_result.sync_statistics.at_risk_students / syncResult.sync_result.total_students * 100)}%"></div>
                                <span class="bar-value">${syncResult.sync_result.sync_statistics.at_risk_students}</span>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="sync-metadata">
                    <small>Sync completed: ${new Date(syncResult.sync_result.sync_timestamp).toLocaleString()}</small>
                    <small>Estimated completion: ${new Date(syncResult.estimated_completion).toLocaleString()}</small>
                </div>
            </div>
        `;
    }
    
    async analyzeStudents() {
        if (!this.currentCourse) {
            this.showError('Please select a course first');
            return;
        }
        
        try {
            this.showStatus('🔄 Analyzing Google Classroom students...', 'info');
            
            const response = await fetch(`${this.apiBase}/students/analyze`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('api_key') || 'dev-key-change-me'}`
                },
                body: JSON.stringify({
                    course_id: this.currentCourse.course_id,
                    ml_features: true
                })
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.students = result.students;
                this.updateStudentAnalysisUI(result);
                this.showStatus(`✅ Analyzed ${result.students.length} students`, 'success');
            } else {
                throw new Error(result.detail || 'Student analysis failed');
            }
            
        } catch (error) {
            console.error('❌ Student analysis failed:', error);
            this.showError(`Student analysis failed: ${error.message}`);
        }
    }
    
    updateStudentAnalysisUI(analysisResult) {
        const analysisSection = document.getElementById('google-student-analysis');
        if (!analysisSection) return;
        
        analysisSection.innerHTML = `
            <div class="analysis-summary">
                <h4>📊 Google Classroom Student Analysis</h4>
                
                <div class="summary-stats">
                    <div class="summary-stat">
                        <div class="stat-value">${analysisResult.summary.total_students_analyzed}</div>
                        <div class="stat-label">Students Analyzed</div>
                    </div>
                    <div class="summary-stat">
                        <div class="stat-value">${(analysisResult.summary.avg_participation_rate * 100).toFixed(1)}%</div>
                        <div class="stat-label">Avg Participation</div>
                    </div>
                    <div class="summary-stat">
                        <div class="stat-value">${(analysisResult.summary.avg_completion_rate * 100).toFixed(1)}%</div>
                        <div class="stat-label">Avg Completion</div>
                    </div>
                </div>
                
                <div class="risk-distribution">
                    <h5>Risk Distribution:</h5>
                    <div class="risk-cards">
                        <div class="risk-card low-risk">
                            <div class="risk-count">${analysisResult.summary.risk_distribution.low_risk}</div>
                            <div class="risk-label">Low Risk</div>
                        </div>
                        <div class="risk-card medium-risk">
                            <div class="risk-count">${analysisResult.summary.risk_distribution.medium_risk}</div>
                            <div class="risk-label">Medium Risk</div>
                        </div>
                        <div class="risk-card high-risk">
                            <div class="risk-count">${analysisResult.summary.risk_distribution.high_risk}</div>
                            <div class="risk-label">High Risk</div>
                        </div>
                    </div>
                </div>
                
                <div class="google-insights">
                    <h5>🎓 Google Classroom Insights:</h5>
                    <div class="insights-grid">
                        <div class="insight-card">
                            <div class="insight-value">${analysisResult.summary.engagement_insights.high_google_drive_usage}</div>
                            <div class="insight-label">High Google Drive Usage</div>
                        </div>
                        <div class="insight-card">
                            <div class="insight-value">${analysisResult.summary.engagement_insights.consistent_meet_attendance}</div>
                            <div class="insight-label">Consistent Meet Attendance</div>
                        </div>
                        <div class="insight-card">
                            <div class="insight-value">${analysisResult.summary.engagement_insights.active_weekend_learners}</div>
                            <div class="insight-label">Weekend Learners</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="student-list">
                <h5>Individual Student Analysis:</h5>
                <div class="students-table">
                    ${this.generateStudentTable(analysisResult.students)}
                </div>
            </div>
        `;
    }
    
    generateStudentTable(students) {
        const tableRows = students.map(student => `
            <div class="student-row" data-risk="${student.risk_assessment.risk_level.toLowerCase().replace(' ', '-')}">
                <div class="student-info">
                    <div class="student-name">${student.name}</div>
                    <div class="student-email">${student.email}</div>
                </div>
                <div class="student-metrics">
                    <div class="metric">
                        <span class="metric-label">Participation:</span>
                        <span class="metric-value">${(student.classroom_participation_rate * 100).toFixed(1)}%</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Completion:</span>
                        <span class="metric-value">${(student.assignment_completion_rate * 100).toFixed(1)}%</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Drive Activity:</span>
                        <span class="metric-value">${(student.google_drive_activity * 100).toFixed(1)}%</span>
                    </div>
                </div>
                <div class="student-risk">
                    <div class="risk-badge ${student.risk_assessment.risk_level.toLowerCase().replace(' ', '-')}">${student.risk_assessment.risk_level}</div>
                    <div class="risk-score">${(student.risk_assessment.risk_score * 100).toFixed(1)}%</div>
                </div>
                <div class="student-actions">
                    <button class="btn btn-sm" onclick="googleClassroom.viewStudentDetails('${student.student_id}')">
                        View Details
                    </button>
                </div>
            </div>
        `).join('');
        
        return `
            <div class="table-header">
                <div class="header-cell">Student</div>
                <div class="header-cell">Google Classroom Metrics</div>
                <div class="header-cell">Risk Assessment</div>
                <div class="header-cell">Actions</div>
            </div>
            ${tableRows}
        `;
    }
    
    async generateEnhancedPredictions() {
        if (!this.currentCourse) {
            this.showError('Please select a course first');
            return;
        }
        
        try {
            this.showStatus('🤖 Generating enhanced predictions...', 'info');
            
            const response = await fetch(`${this.apiBase}/predict/enhanced?course_id=${this.currentCourse.course_id}&include_ml_features=true`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('api_key') || 'dev-key-change-me'}`
                }
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.updateEnhancedPredictionsUI(result);
                this.showStatus('✅ Enhanced predictions generated', 'success');
            } else {
                throw new Error(result.detail || 'Prediction generation failed');
            }
            
        } catch (error) {
            console.error('❌ Enhanced predictions failed:', error);
            this.showError(`Prediction generation failed: ${error.message}`);
        }
    }
    
    updateEnhancedPredictionsUI(predictionsResult) {
        const predictionsSection = document.getElementById('google-enhanced-predictions');
        if (!predictionsSection) return;
        
        predictionsSection.innerHTML = `
            <div class="predictions-header">
                <h4>🤖 Enhanced Predictions with Google Classroom Data</h4>
                <div class="model-performance">
                    <div class="performance-metric">
                        <span class="metric-label">Enhanced AUC:</span>
                        <span class="metric-value">${predictionsResult.model_performance.enhanced_auc}</span>
                    </div>
                    <div class="performance-metric">
                        <span class="metric-label">Improvement:</span>
                        <span class="metric-value success">${predictionsResult.model_performance.improvement}</span>
                    </div>
                    <div class="performance-metric">
                        <span class="metric-label">Confidence Boost:</span>
                        <span class="metric-value">${predictionsResult.model_performance.confidence_boost}</span>
                    </div>
                </div>
            </div>
            
            <div class="predictions-insights">
                <h5>🎓 Google Classroom Enhancement Insights:</h5>
                <div class="insights-text">
                    <p><strong>Accuracy Improvement:</strong> ${predictionsResult.enhancement_summary.prediction_accuracy_improvement}</p>
                    <p><strong>Average Confidence:</strong> ${(predictionsResult.enhancement_summary.avg_confidence * 100).toFixed(1)}%</p>
                </div>
                <div class="unique-insights">
                    <h6>Unique Google Classroom Insights:</h6>
                    <ul>
                        ${predictionsResult.enhancement_summary.unique_insights.map(insight => `<li>${insight}</li>`).join('')}
                    </ul>
                </div>
            </div>
            
            <div class="predictions-list">
                <h5>Individual Predictions:</h5>
                ${this.generatePredictionsTable(predictionsResult.predictions)}
            </div>
        `;
    }
    
    generatePredictionsTable(predictions) {
        const tableRows = predictions.map(prediction => `
            <div class="prediction-row" data-risk="${prediction.risk_category.toLowerCase().replace(' ', '-')}">
                <div class="student-id">${prediction.student_id}</div>
                <div class="prediction-score">
                    <div class="risk-badge ${prediction.risk_category.toLowerCase().replace(' ', '-')}">${prediction.risk_category}</div>
                    <div class="score-value">${(prediction.enhanced_risk_score * 100).toFixed(1)}%</div>
                    <div class="confidence">Confidence: ${(prediction.confidence * 100).toFixed(1)}%</div>
                </div>
                <div class="prediction-components">
                    <div class="component">
                        <span class="component-label">Academic:</span>
                        <span class="component-value">${(prediction.prediction_components.traditional_academic * 100).toFixed(0)}%</span>
                    </div>
                    <div class="component">
                        <span class="component-label">GC Participation:</span>
                        <span class="component-value">${(prediction.prediction_components.google_classroom_participation * 100).toFixed(0)}%</span>
                    </div>
                    <div class="component">
                        <span class="component-label">Drive Activity:</span>
                        <span class="component-value">${(prediction.prediction_components.google_drive_engagement * 100).toFixed(0)}%</span>
                    </div>
                    <div class="component">
                        <span class="component-label">Meet Attendance:</span>
                        <span class="component-value">${(prediction.prediction_components.google_meet_attendance * 100).toFixed(0)}%</span>
                    </div>
                </div>
                <div class="prediction-recommendations">
                    <button class="btn btn-sm" onclick="googleClassroom.showPredictionDetails('${prediction.student_id}')">
                        View Recommendations
                    </button>
                </div>
            </div>
        `).join('');
        
        return `
            <div class="predictions-table">
                <div class="table-header">
                    <div class="header-cell">Student</div>
                    <div class="header-cell">Enhanced Prediction</div>
                    <div class="header-cell">Component Scores</div>
                    <div class="header-cell">Actions</div>
                </div>
                ${tableRows}
            </div>
        `;
    }
    
    async showCrossPlatformAnalytics() {
        try {
            this.showStatus('📊 Loading cross-platform analytics...', 'info');
            
            const response = await fetch(`${this.apiBase}/analytics/cross-platform?include_canvas=true&include_powerschool=true&include_google=true`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('api_key') || 'dev-key-change-me'}`
                }
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.showCrossPlatformModal(result);
                this.showStatus('✅ Cross-platform analytics loaded', 'success');
            } else {
                throw new Error(result.detail || 'Cross-platform analytics failed');
            }
            
        } catch (error) {
            console.error('❌ Cross-platform analytics failed:', error);
            this.showError(`Cross-platform analytics failed: ${error.message}`);
        }
    }
    
    showCrossPlatformModal(analyticsData) {
        const modal = document.createElement('div');
        modal.className = 'cross-platform-modal';
        modal.innerHTML = `
            <div class="modal-content large-modal">
                <div class="modal-header">
                    <h3>📊 Cross-Platform Analytics</h3>
                    <button class="close-btn" onclick="this.closest('.cross-platform-modal').remove()">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="platform-comparison">
                        <h4>Platform Comparison:</h4>
                        <div class="platforms-grid">
                            ${Object.entries(analyticsData.platform_comparison).map(([platform, data]) => `
                                <div class="platform-card">
                                    <h5>${platform.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}</h5>
                                    <div class="platform-metrics">
                                        ${Object.entries(data).filter(([key]) => typeof data[key] === 'number').map(([key, value]) => `
                                            <div class="platform-metric">
                                                <span class="metric-label">${key.replace(/_/g, ' ')}:</span>
                                                <span class="metric-value">${typeof value === 'number' && value <= 1 ? (value * 100).toFixed(1) + '%' : value}</span>
                                            </div>
                                        `).join('')}
                                    </div>
                                    <div class="platform-strengths">
                                        <strong>Strengths:</strong>
                                        <ul>
                                            ${data.unique_strengths?.map(strength => `<li>${strength}</li>`).join('') || ''}
                                        </ul>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                    
                    <div class="unified-insights">
                        <h4>Unified Insights:</h4>
                        <div class="insights-grid">
                            <div class="insight-card">
                                <h5>Engagement Patterns</h5>
                                <p>Most Engaging: ${analyticsData.unified_insights.engagement_patterns.most_engaging_platform}</p>
                                <p>Consistency: ${(analyticsData.unified_insights.engagement_patterns.consistency_across_platforms * 100).toFixed(1)}%</p>
                            </div>
                            <div class="insight-card">
                                <h5>Performance Consistency</h5>
                                <p>Academic Alignment: ${(analyticsData.unified_insights.performance_consistency.academic_alignment * 100).toFixed(1)}%</p>
                                <p>Risk Signal Agreement: ${(analyticsData.unified_insights.performance_consistency.risk_signal_agreement * 100).toFixed(1)}%</p>
                            </div>
                            <div class="insight-card">
                                <h5>Predictive Power</h5>
                                <p>Single Platform: ${(analyticsData.unified_insights.predictive_power.single_platform_accuracy * 100).toFixed(1)}%</p>
                                <p>Cross-Platform: ${(analyticsData.unified_insights.predictive_power.cross_platform_accuracy * 100).toFixed(1)}%</p>
                                <p class="improvement">Improvement: ${analyticsData.unified_insights.predictive_power.improvement}</p>
                            </div>
                        </div>
                    </div>
                    
                    <div class="cross-platform-recommendations">
                        <h4>Recommendations:</h4>
                        <div class="recommendations-section">
                            <h5>Cross-Platform:</h5>
                            <ul>
                                ${analyticsData.recommendations.cross_platform.map(rec => `<li>${rec}</li>`).join('')}
                            </ul>
                            
                            <h5>Platform-Specific:</h5>
                            ${Object.entries(analyticsData.recommendations.platform_specific).map(([platform, recs]) => `
                                <div class="platform-recommendations">
                                    <h6>${platform.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}:</h6>
                                    <ul>
                                        ${recs.map(rec => `<li>${rec}</li>`).join('')}
                                    </ul>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
    }
    
    // Utility methods
    showStatus(message, type = 'info') {
        const statusDiv = document.getElementById('google-status') || document.getElementById('status-message');
        if (!statusDiv) return;
        
        statusDiv.className = `status-message ${type}`;
        statusDiv.textContent = message;
        statusDiv.style.display = 'block';
        
        if (type === 'success' || type === 'error') {
            setTimeout(() => {
                statusDiv.style.display = 'none';
            }, 5000);
        }
    }
    
    showError(message) {
        this.showStatus(`❌ ${message}`, 'error');
    }
    
    refreshData() {
        if (this.isAuthenticated) {
            this.syncCourses();
        }
    }
    
    disconnect() {
        this.isAuthenticated = false;
        this.courses = [];
        this.currentCourse = null;
        this.students = [];
        
        this.updateAuthenticationUI();
        this.showStatus('Disconnected from Google Classroom', 'info');
    }
    
    viewStudentDetails(studentId) {
        const student = this.students.find(s => s.student_id === studentId);
        if (!student) return;
        
        // Implementation for detailed student view
        console.log('Viewing details for student:', student);
    }
    
    showPredictionDetails(studentId) {
        // Implementation for prediction details
        console.log('Showing prediction details for student:', studentId);
    }
}

// Initialize Google Classroom integration when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    if (typeof window !== 'undefined') {
        window.googleClassroom = new GoogleClassroomIntegration();
    }
});

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = GoogleClassroomIntegration;
}