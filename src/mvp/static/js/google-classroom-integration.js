/**
 * Google Classroom Integration JavaScript
 * Handles Google Classroom API connection, course selection, and data synchronization
 * Follows the same pattern as Canvas and PowerSchool integrations for consistency
 */

class GoogleClassroomIntegration {
    constructor() {
        this.selectedCourse = null;
        this.connectionStatus = false;
        this.courses = [];
        this.init();
    }

    init() {
        this.bindEvents();
        this.checkConnectionStatus();
    }

    bindEvents() {
        // Connection events
        document.getElementById('connect-google-classroom')?.addEventListener('click', () => this.connectToGoogleClassroom());
        document.getElementById('show-google-help')?.addEventListener('click', () => this.showGoogleHelp());
        document.getElementById('close-google-help')?.addEventListener('click', () => this.hideGoogleHelp());
        
        // Course selection events
        document.getElementById('refresh-google-courses')?.addEventListener('click', () => this.loadCourses());
        document.getElementById('select-different-google-course')?.addEventListener('click', () => this.showCourseSelection());
        
        // Analysis events
        document.getElementById('sync-google-course')?.addEventListener('click', () => this.syncCourse());
        document.getElementById('google-enhanced-analysis')?.addEventListener('click', () => this.enhancedAnalysis());
        document.getElementById('cross-platform-analysis')?.addEventListener('click', () => this.crossPlatformAnalysis());
        
        // Course selection change
        document.getElementById('google-course-select')?.addEventListener('change', (e) => this.selectCourse(e.target.value));
    }

    async checkConnectionStatus() {
        try {
            const response = await fetch('/api/google/health', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('api_key') || 'dev-key-change-me'}`
                }
            });
            
            const health = await response.json();
            this.updateConnectionStatus(health);
            
        } catch (error) {
            console.error('Failed to check Google Classroom status:', error);
            this.updateConnectionStatus({ status: 'error', warning: 'Connection check failed' });
        }
    }

    updateConnectionStatus(health) {
        const statusElement = document.getElementById('google-connection-status');
        const indicatorElement = document.getElementById('google-status-indicator');
        
        if (!statusElement || !indicatorElement) return;
        
        // Update status text and styling based on health check
        if (health.status === 'setup_required') {
            statusElement.textContent = '⚠️ Google API credentials required';
            indicatorElement.className = 'status-indicator warning';
        } else if (health.status === 'limited') {
            statusElement.textContent = '⚠️ Demo mode - Google API libraries not installed';
            indicatorElement.className = 'status-indicator warning';
        } else if (health.authentication) {
            statusElement.textContent = '✅ Connected to Google Classroom';
            indicatorElement.className = 'status-indicator connected';
            this.connectionStatus = true;
            this.showConnectedInterface();
        } else {
            statusElement.textContent = '❌ Not connected to Google Classroom';
            indicatorElement.className = 'status-indicator disconnected';
        }
    }

    async connectToGoogleClassroom() {
        try {
            this.showMessage('🔄 Connecting to Google Classroom...', 'info');
            
            // Start OAuth flow
            const authResponse = await fetch('/api/google/auth/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('api_key') || 'dev-key-change-me'}`
                },
                body: JSON.stringify({
                    redirect_uri: window.location.origin + '/google-auth-callback'
                })
            });
            
            const authData = await authResponse.json();
            
            if (authResponse.ok) {
                // For demo/development, simulate successful auth
                const completeResponse = await fetch('/api/google/auth/complete', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${localStorage.getItem('api_key') || 'dev-key-change-me'}`
                    },
                    body: JSON.stringify({
                        authorization_code: 'demo_auth_code_12345'
                    })
                });
                
                const completeData = await completeResponse.json();
                
                if (completeResponse.ok) {
                    this.showMessage('✅ Successfully connected to Google Classroom!', 'success');
                    this.connectionStatus = true;
                    this.showConnectedInterface();
                    this.loadCourses();
                } else {
                    throw new Error(completeData.detail || 'Authentication failed');
                }
            } else {
                throw new Error(authData.detail || 'Connection failed');
            }
            
        } catch (error) {
            console.error('Google Classroom connection failed:', error);
            this.showMessage(`❌ Connection failed: ${error.message}`, 'error');
        }
    }

    showConnectedInterface() {
        document.getElementById('google-connection')?.classList.add('hidden');
        document.getElementById('google-connected')?.classList.remove('hidden');
    }

    showCourseSelection() {
        document.getElementById('google-course-info')?.classList.add('hidden');
        document.getElementById('google-results')?.classList.add('hidden');
    }

    async loadCourses() {
        if (!this.connectionStatus) {
            this.showMessage('Please connect to Google Classroom first', 'error');
            return;
        }
        
        try {
            this.showMessage('🔄 Loading Google Classroom courses...', 'info');
            
            const response = await fetch('/api/google/courses', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('api_key') || 'dev-key-change-me'}`
                }
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.courses = data.courses;
                this.updateCoursesDropdown();
                this.showMessage(`✅ Loaded ${data.courses.length} courses`, 'success');
            } else {
                throw new Error(data.detail || 'Failed to load courses');
            }
            
        } catch (error) {
            console.error('Failed to load courses:', error);
            this.showMessage(`❌ Failed to load courses: ${error.message}`, 'error');
        }
    }

    updateCoursesDropdown() {
        const select = document.getElementById('google-course-select');
        if (!select) return;
        
        select.innerHTML = '<option value="">Choose a Google Classroom course...</option>';
        
        this.courses.forEach(course => {
            const option = document.createElement('option');
            option.value = course.course_id;
            option.textContent = `${course.name} (${course.enrollment_count} students)`;
            select.appendChild(option);
        });
    }

    selectCourse(courseId) {
        if (!courseId) {
            this.selectedCourse = null;
            document.getElementById('google-course-info')?.classList.add('hidden');
            return;
        }
        
        this.selectedCourse = this.courses.find(c => c.course_id === courseId);
        if (this.selectedCourse) {
            this.showCourseInfo();
            this.showMessage(`Selected: ${this.selectedCourse.name}`, 'info');
        }
    }

    showCourseInfo() {
        const courseInfoDiv = document.getElementById('google-course-info');
        const courseDetailsDiv = document.getElementById('google-course-details');
        
        if (!courseInfoDiv || !courseDetailsDiv || !this.selectedCourse) return;
        
        courseDetailsDiv.innerHTML = `
            <div class="course-summary">
                <h5>${this.selectedCourse.name}</h5>
                <p>${this.selectedCourse.description}</p>
                <div class="course-stats">
                    <span class="stat">👥 ${this.selectedCourse.enrollment_count} students</span>
                    <span class="stat">📊 ${(this.selectedCourse.avg_engagement_rate * 100).toFixed(1)}% engagement</span>
                    <span class="stat">📝 ${this.selectedCourse.assignment_frequency}/week assignments</span>
                </div>
            </div>
        `;
        
        courseInfoDiv.classList.remove('hidden');
    }

    async syncCourse() {
        if (!this.selectedCourse) {
            this.showMessage('Please select a course first', 'error');
            return;
        }
        
        try {
            this.showMessage('🔄 Analyzing Google Classroom course...', 'info');
            
            const response = await fetch('/api/google/students/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('api_key') || 'dev-key-change-me'}`
                },
                body: JSON.stringify({
                    course_id: this.selectedCourse.course_id,
                    ml_features: true
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.showAnalysisResults(data);
                this.showMessage('✅ Course analysis completed!', 'success');
            } else {
                throw new Error(data.detail || 'Analysis failed');
            }
            
        } catch (error) {
            console.error('Course sync failed:', error);
            this.showMessage(`❌ Analysis failed: ${error.message}`, 'error');
        }
    }

    showAnalysisResults(data) {
        const resultsDiv = document.getElementById('google-results');
        const summaryDiv = document.getElementById('google-results-summary');
        
        if (!resultsDiv || !summaryDiv) return;
        
        summaryDiv.innerHTML = `
            <div class="analysis-overview">
                <h4>📊 Google Classroom Analysis Results</h4>
                <div class="results-stats">
                    <div class="stat-card">
                        <div class="stat-value">${data.summary.total_students_analyzed}</div>
                        <div class="stat-label">Students Analyzed</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${(data.summary.avg_participation_rate * 100).toFixed(1)}%</div>
                        <div class="stat-label">Avg Participation</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${data.summary.risk_distribution.high_risk}</div>
                        <div class="stat-label">High Risk Students</div>
                    </div>
                </div>
                
                <div class="google-insights">
                    <h5>🎓 Google Classroom Insights:</h5>
                    <ul>
                        <li>📁 ${data.summary.engagement_insights.high_google_drive_usage} students with high Google Drive usage</li>
                        <li>🎥 ${data.summary.engagement_insights.consistent_meet_attendance} students with consistent Meet attendance</li>
                        <li>📱 ${data.summary.engagement_insights.active_weekend_learners} active weekend learners</li>
                    </ul>
                </div>
            </div>
        `;
        
        resultsDiv.classList.remove('hidden');
    }

    async enhancedAnalysis() {
        if (!this.selectedCourse) {
            this.showMessage('Please select a course first', 'error');
            return;
        }
        
        try {
            this.showMessage('🤖 Generating enhanced predictions...', 'info');
            
            const response = await fetch(`/api/google/predict/enhanced?course_id=${this.selectedCourse.course_id}&include_ml_features=true`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('api_key') || 'dev-key-change-me'}`
                }
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.showMessage(`✅ Enhanced analysis complete! ${data.model_performance.improvement} improvement with Google data`, 'success');
            } else {
                throw new Error(data.detail || 'Enhanced analysis failed');
            }
            
        } catch (error) {
            console.error('Enhanced analysis failed:', error);
            this.showMessage(`❌ Enhanced analysis failed: ${error.message}`, 'error');
        }
    }

    async crossPlatformAnalysis() {
        try {
            this.showMessage('📊 Loading cross-platform analytics...', 'info');
            
            const response = await fetch('/api/google/analytics/cross-platform?include_canvas=true&include_powerschool=true&include_google=true', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('api_key') || 'dev-key-change-me'}`
                }
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.showMessage(`✅ Cross-platform analysis: ${data.unified_insights.predictive_power.improvement} accuracy improvement`, 'success');
            } else {
                throw new Error(data.detail || 'Cross-platform analysis failed');
            }
            
        } catch (error) {
            console.error('Cross-platform analysis failed:', error);
            this.showMessage(`❌ Cross-platform analysis failed: ${error.message}`, 'error');
        }
    }

    showGoogleHelp() {
        document.getElementById('google-help-modal')?.classList.remove('hidden');
    }

    hideGoogleHelp() {
        document.getElementById('google-help-modal')?.classList.add('hidden');
    }

    showMessage(message, type = 'info') {
        const statusDiv = document.getElementById('google-status');
        if (!statusDiv) return;
        
        statusDiv.className = `status-message ${type}`;
        statusDiv.textContent = message;
        statusDiv.classList.remove('hidden');
        
        if (type === 'success' || type === 'error') {
            setTimeout(() => {
                statusDiv.classList.add('hidden');
            }, 5000);
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    if (typeof window !== 'undefined') {
        window.googleClassroom = new GoogleClassroomIntegration();
    }
});

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = GoogleClassroomIntegration;
}