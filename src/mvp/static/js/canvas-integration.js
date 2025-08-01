/**
 * Canvas LMS Integration JavaScript
 * Handles Canvas API connection, course selection, and data synchronization
 */

class CanvasIntegration {
    constructor() {
        this.canvasUrl = '';
        this.canvasToken = '';
        this.selectedCourse = null;
        this.connectionStatus = false;
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadSavedCredentials();
    }

    bindEvents() {
        // Connection events
        document.getElementById('connect-canvas')?.addEventListener('click', () => this.connectToCanvas());
        document.getElementById('show-token-help')?.addEventListener('click', () => this.showTokenHelp());
        document.getElementById('close-token-help')?.addEventListener('click', () => this.hideTokenHelp());
        
        // Course selection events
        document.getElementById('refresh-courses')?.addEventListener('click', () => this.loadCourses());
        document.getElementById('select-different-course')?.addEventListener('click', () => this.showCourseSelection());
        
        // Analysis events
        document.getElementById('sync-course')?.addEventListener('click', () => this.syncCourse());
        
        // Auto-save credentials
        document.getElementById('canvas-url')?.addEventListener('blur', () => this.saveCredentials());
        document.getElementById('canvas-token')?.addEventListener('blur', () => this.saveCredentials());
    }

    loadSavedCredentials() {
        // Load from localStorage (for demo purposes - use secure storage in production)
        const savedUrl = localStorage.getItem('canvas-url');
        const savedToken = localStorage.getItem('canvas-token');
        
        if (savedUrl) {
            document.getElementById('canvas-url').value = savedUrl;
        }
        if (savedToken) {
            document.getElementById('canvas-token').value = savedToken;
        }
    }

    saveCredentials() {
        const url = document.getElementById('canvas-url').value;
        const token = document.getElementById('canvas-token').value;
        
        if (url) localStorage.setItem('canvas-url', url);
        if (token) localStorage.setItem('canvas-token', token);
    }

    showTokenHelp() {
        document.getElementById('token-help').classList.remove('hidden');
    }

    hideTokenHelp() {
        document.getElementById('token-help').classList.add('hidden');
    }

    async connectToCanvas() {
        const urlInput = document.getElementById('canvas-url');
        const tokenInput = document.getElementById('canvas-token');
        
        this.canvasUrl = urlInput.value.trim();
        this.canvasToken = tokenInput.value.trim();
        
        if (!this.canvasUrl || !this.canvasToken) {
            this.showError('Please enter both Canvas URL and access token');
            return;
        }
        
        // Normalize URL
        if (!this.canvasUrl.startsWith('http')) {
            this.canvasUrl = 'https://' + this.canvasUrl;
        }
        this.canvasUrl = this.canvasUrl.replace(/\/$/, ''); // Remove trailing slash
        
        const connectBtn = document.getElementById('connect-canvas');
        const originalText = connectBtn.textContent;
        
        try {
            connectBtn.textContent = '🔗 Connecting...';
            connectBtn.disabled = true;
            
            const response = await fetch('/api/lms/canvas/connect', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getApiKey()}`
                },
                body: JSON.stringify({
                    base_url: this.canvasUrl,
                    access_token: this.canvasToken
                })
            });
            
            const result = await response.json();
            
            if (result.status === 'success') {
                this.connectionStatus = true;
                this.showConnectionSuccess(result.account_info);
                await this.loadCourses();
                this.saveCredentials();
            } else {
                throw new Error(result.error || 'Connection failed');
            }
            
        } catch (error) {
            console.error('Canvas connection error:', error);
            this.showError(`Connection failed: ${error.message}`);
        } finally {
            connectBtn.textContent = originalText;
            connectBtn.disabled = false;
        }
    }

    showConnectionSuccess(accountInfo) {
        // Hide connection form
        document.getElementById('lms-connection').style.display = 'none';
        
        // Show connection status
        const statusDiv = document.getElementById('connection-status');
        statusDiv.classList.remove('hidden');
        
        // Update connection info
        document.getElementById('account-name').textContent = accountInfo.name || 'Unknown';
        document.getElementById('course-count').textContent = accountInfo.accessible_courses || 0;
        document.getElementById('rate-limit').textContent = accountInfo.rate_limit_remaining || 0;
        
        this.showSuccess('Successfully connected to Canvas LMS!');
    }

    async loadCourses() {
        if (!this.connectionStatus) {
            this.showError('Please connect to Canvas first');
            return;
        }

        try {
            const response = await fetch('/api/lms/canvas/courses', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getApiKey()}`
                },
                body: JSON.stringify({
                    base_url: this.canvasUrl,
                    access_token: this.canvasToken
                })
            });
            
            const result = await response.json();
            
            if (result.status === 'success') {
                this.displayCourses(result.courses);
                this.showCourseSelection();
            } else {
                throw new Error(result.error || 'Failed to load courses');
            }
            
        } catch (error) {
            console.error('Error loading courses:', error);
            this.showError(`Failed to load courses: ${error.message}`);
        }
    }

    displayCourses(courses) {
        const courseList = document.getElementById('course-list');
        courseList.innerHTML = '';
        
        if (courses.length === 0) {
            courseList.innerHTML = '<p class="no-courses">No active courses found. Make sure you have teacher access to courses.</p>';
            return;
        }
        
        courses.forEach(course => {
            const courseCard = document.createElement('div');
            courseCard.className = 'course-card';
            courseCard.innerHTML = `
                <div class="course-info">
                    <h5>${course.name}</h5>
                    <p class="course-code">${course.course_code}</p>
                    <div class="course-meta">
                        <span>📚 ${course.term}</span>
                        <span>👥 ${course.student_count} students</span>
                    </div>
                </div>
                <button class="btn btn-primary select-course-btn" data-course-id="${course.id}">
                    Select Course
                </button>
            `;
            
            courseCard.querySelector('.select-course-btn').addEventListener('click', () => {
                this.selectCourse(course);
            });
            
            courseList.appendChild(courseCard);
        });
    }

    selectCourse(course) {
        this.selectedCourse = course;
        
        // Update UI
        document.getElementById('selected-course-name').textContent = course.name;
        document.getElementById('selected-course-students').textContent = course.student_count;
        
        // Show analysis section
        this.showCourseAnalysis();
    }

    showCourseSelection() {
        document.getElementById('course-selection').classList.remove('hidden');
        document.getElementById('course-analysis').classList.add('hidden');
    }

    showCourseAnalysis() {
        document.getElementById('course-selection').classList.add('hidden');
        document.getElementById('course-analysis').classList.remove('hidden');
    }

    async syncCourse() {
        if (!this.selectedCourse) {
            this.showError('Please select a course first');
            return;
        }

        const syncBtn = document.getElementById('sync-course');
        const originalText = syncBtn.textContent;
        const progressDiv = document.getElementById('sync-progress');
        const progressFill = document.getElementById('progress-fill');
        const progressText = document.getElementById('progress-text');
        
        try {
            syncBtn.disabled = true;
            syncBtn.textContent = '📊 Syncing...';
            progressDiv.classList.remove('hidden');
            
            // Animate progress
            this.animateProgress(progressFill, progressText, [
                { progress: 20, text: 'Connecting to Canvas...' },
                { progress: 40, text: 'Fetching student data...' },
                { progress: 60, text: 'Processing gradebook...' },
                { progress: 80, text: 'Generating predictions...' },
                { progress: 100, text: 'Analysis complete!' }
            ]);
            
            const response = await fetch('/api/lms/canvas/sync', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getApiKey()}`
                },
                body: JSON.stringify({
                    base_url: this.canvasUrl,
                    access_token: this.canvasToken,
                    course_id: this.selectedCourse.id
                })
            });
            
            const result = await response.json();
            
            if (result.status === 'success') {
                // Hide Canvas interface and show results
                document.getElementById('lms-section').style.display = 'none';
                
                // Display results in the main results section
                this.displayCanvasResults(result);
                
                this.showSuccess(`✅ Successfully analyzed ${result.students_processed} students from ${this.selectedCourse.name}`);
            } else {
                throw new Error(result.error || 'Sync failed');
            }
            
        } catch (error) {
            console.error('Canvas sync error:', error);
            this.showError(`Sync failed: ${error.message}`);
            progressFill.style.width = '0%';
            progressText.textContent = 'Sync failed';
        } finally {
            syncBtn.disabled = false;
            syncBtn.textContent = originalText;
            setTimeout(() => {
                progressDiv.classList.add('hidden');
            }, 2000);
        }
    }

    displayCanvasResults(result) {
        // Show results section
        const resultsSection = document.getElementById('results-section');
        const summarySection = document.getElementById('summary-section');
        
        if (resultsSection) {
            resultsSection.classList.remove('hidden');
            resultsSection.scrollIntoView({ behavior: 'smooth' });
        }
        
        // Update summary with Canvas data
        if (result.summary && summarySection) {
            this.updateSummarySection(result.summary, result.course_id);
        }
        
        // Display predictions
        if (result.predictions && window.displayResults) {
            window.displayResults(result.predictions);
        }
        
        // Add Canvas-specific information
        this.addCanvasMetadata(result);
    }

    updateSummarySection(summary, courseId) {
        const summarySection = document.getElementById('summary-section');
        if (!summarySection) return;
        
        summarySection.innerHTML = `
            <div class="card">
                <div class="step-header">
                    <span class="step-number">📊</span>
                    <h2>Canvas Analysis Summary</h2>
                    <p>Real-time analysis from ${this.selectedCourse.name}</p>
                </div>
                
                <div class="summary-grid">
                    <div class="summary-card">
                        <div class="summary-icon">👥</div>
                        <div class="summary-content">
                            <h3>${summary.total_students}</h3>
                            <p>Total Students</p>
                        </div>
                    </div>
                    
                    <div class="summary-card risk-high">
                        <div class="summary-icon">⚠️</div>
                        <div class="summary-content">
                            <h3>${summary.risk_distribution.high_risk}</h3>
                            <p>High Risk</p>
                        </div>
                    </div>
                    
                    <div class="summary-card risk-moderate">
                        <div class="summary-icon">⚡</div>
                        <div class="summary-content">
                            <h3>${summary.risk_distribution.moderate_risk}</h3>
                            <p>Moderate Risk</p>
                        </div>
                    </div>
                    
                    <div class="summary-card risk-low">
                        <div class="summary-icon">✅</div>
                        <div class="summary-content">
                            <h3>${summary.risk_distribution.low_risk}</h3>
                            <p>Low Risk</p>
                        </div>
                    </div>
                </div>
                
                <div class="canvas-info">
                    <p><strong>Course:</strong> ${this.selectedCourse.name}</p>
                    <p><strong>Data Source:</strong> Canvas LMS (Real-time)</p>
                    <p><strong>Last Sync:</strong> ${new Date().toLocaleString()}</p>
                </div>
            </div>
        `;
        
        summarySection.classList.remove('hidden');
    }

    addCanvasMetadata(result) {
        // Add a note about Canvas data source
        const metadataDiv = document.createElement('div');
        metadataDiv.className = 'canvas-metadata';
        metadataDiv.innerHTML = `
            <div class="card">
                <h4>🎨 Canvas LMS Integration</h4>
                <p>This analysis was generated from real-time Canvas gradebook data:</p>
                <ul>
                    <li><strong>Course:</strong> ${this.selectedCourse.name} (${this.selectedCourse.course_code})</li>
                    <li><strong>Students Analyzed:</strong> ${result.students_processed}</li>
                    <li><strong>Data Source:</strong> Canvas Assignments & Grades</li>
                    <li><strong>Sync Time:</strong> ${new Date().toLocaleString()}</li>
                </ul>
                <p class="note">💡 <strong>Next Steps:</strong> Use the individual student predictions below to implement targeted interventions.</p>
            </div>
        `;
        
        const resultsSection = document.getElementById('results-section');
        if (resultsSection) {
            resultsSection.appendChild(metadataDiv);
        }
    }

    animateProgress(progressFill, progressText, steps) {
        let currentStep = 0;
        
        const animate = () => {
            if (currentStep < steps.length) {
                const step = steps[currentStep];
                progressFill.style.width = step.progress + '%';
                progressText.textContent = step.text;
                currentStep++;
                setTimeout(animate, 800);
            }
        };
        
        animate();
    }

    getApiKey() {
        // Get API key from localStorage or use default
        return localStorage.getItem('api-key') || 'dev-key-change-me';
    }

    showError(message) {
        // Create or update error message
        let errorDiv = document.getElementById('canvas-error');
        if (!errorDiv) {
            errorDiv = document.createElement('div');
            errorDiv.id = 'canvas-error';
            errorDiv.className = 'error-message';
            document.getElementById('lms-section').appendChild(errorDiv);
        }
        
        errorDiv.innerHTML = `
            <div class="error-content">
                <span class="error-icon">❌</span>
                <span class="error-text">${message}</span>
                <button class="error-close" onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
        `;
        
        errorDiv.style.display = 'block';
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.remove();
            }
        }, 5000);
    }

    showSuccess(message) {
        // Create or update success message
        let successDiv = document.getElementById('canvas-success');
        if (!successDiv) {
            successDiv = document.createElement('div');
            successDiv.id = 'canvas-success';
            successDiv.className = 'success-message';
            document.getElementById('lms-section').appendChild(successDiv);
        }
        
        successDiv.innerHTML = `
            <div class="success-content">
                <span class="success-icon">✅</span>
                <span class="success-text">${message}</span>
                <button class="success-close" onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
        `;
        
        successDiv.style.display = 'block';
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            if (successDiv.parentNode) {
                successDiv.remove();
            }
        }, 5000);
    }
}

// Initialize Canvas integration when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.canvasIntegration = new CanvasIntegration();
});