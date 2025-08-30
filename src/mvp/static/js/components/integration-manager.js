/**
 * Integration Manager - Canvas LMS Connection
 * Handles LMS integration UI, connection testing, and data import workflow
 */

class IntegrationManager {
    constructor() {
        this.currentModal = null;
        this.mockCanvasData = this.generateMockCanvasData();
        this.init();
    }

    init() {
        this.bindIntegrationCards();
    }

    bindIntegrationCards() {
        const integrationCards = document.querySelectorAll('.integration-card');
        integrationCards.forEach(card => {
            card.addEventListener('click', (e) => {
                const integration = card.dataset.integration;
                this.handleIntegrationClick(integration, card);
            });
        });
    }

    handleIntegrationClick(integration, card) {
        switch(integration) {
            case 'canvas':
                this.showCanvasConnectionModal(card);
                break;
            case 'powerschool':
                this.showComingSoonModal('PowerSchool SIS');
                break;
            case 'google':
                this.showComingSoonModal('Google Classroom');
                break;
        }
    }

    showCanvasConnectionModal(card) {
        const statusBadge = card.querySelector('#canvas-status');
        const isConnected = statusBadge.textContent === 'Connected';

        if (isConnected) {
            this.showCanvasManagementModal(card);
            return;
        }

        const modalHtml = `
            <div class="modal-overlay" id="canvas-connection-modal">
                <div class="modal-container">
                    <div class="modal-header">
                        <h3>Connect to Canvas LMS</h3>
                        <button class="modal-close" onclick="integrationManager.closeModal()">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    
                    <div class="modal-content">
                        <div class="connection-form">
                            <div class="form-group">
                                <label for="canvas-url">Canvas URL</label>
                                <input type="url" 
                                       id="canvas-url" 
                                       placeholder="https://your-school.instructure.com"
                                       value="https://demo.instructure.com">
                                <small>Your school's Canvas URL</small>
                            </div>
                            
                            <div class="form-group">
                                <label for="canvas-token">API Access Token</label>
                                <input type="password" 
                                       id="canvas-token" 
                                       placeholder="1234~abc..."
                                       value="demo_token_12345">
                                <small>Generate this from Account → Settings → Approved Integrations</small>
                            </div>

                            <div class="connection-status" id="connection-status" style="display: none;">
                                <!-- Status messages appear here -->
                            </div>
                            
                            <div class="modal-actions">
                                <button class="btn btn-secondary" onclick="integrationManager.closeModal()">
                                    Cancel
                                </button>
                                <button class="btn btn-primary" id="test-connection-btn" onclick="integrationManager.testCanvasConnection()">
                                    <i class="fas fa-plug"></i>
                                    Test Connection
                                </button>
                                <button class="btn btn-success" id="connect-btn" style="display: none;" onclick="integrationManager.connectToCanvas()">
                                    <i class="fas fa-check"></i>
                                    Connect & Import Courses
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHtml);
        this.currentModal = document.getElementById('canvas-connection-modal');
    }

    async testCanvasConnection() {
        const testBtn = document.getElementById('test-connection-btn');
        const connectBtn = document.getElementById('connect-btn');
        const statusDiv = document.getElementById('connection-status');

        // Show loading state
        testBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Testing...';
        testBtn.disabled = true;
        statusDiv.style.display = 'block';
        statusDiv.innerHTML = '<div class="status-loading">Testing connection...</div>';

        // Simulate API call delay
        await new Promise(resolve => setTimeout(resolve, 1500));

        // Mock successful connection
        statusDiv.innerHTML = `
            <div class="status-success">
                <i class="fas fa-check-circle"></i>
                <strong>Connection Successful!</strong>
                <br>Found ${this.mockCanvasData.courses.length} courses
            </div>
        `;

        testBtn.style.display = 'none';
        connectBtn.style.display = 'inline-flex';
    }

    async connectToCanvas() {
        const connectBtn = document.getElementById('connect-btn');
        const statusDiv = document.getElementById('connection-status');

        // Show loading
        connectBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Connecting...';
        connectBtn.disabled = true;

        // Simulate connection process
        await new Promise(resolve => setTimeout(resolve, 1000));

        this.showCourseSelectionModal();
    }

    showCourseSelectionModal() {
        this.closeModal();

        const courseOptions = this.mockCanvasData.courses.map(course => `
            <div class="course-option">
                <label class="checkbox-container">
                    <input type="checkbox" value="${course.id}" checked>
                    <span class="checkmark"></span>
                    <div class="course-info">
                        <h4>${course.name}</h4>
                        <p>${course.students} students • ${course.assignments} assignments</p>
                        <span class="course-code">${course.code}</span>
                    </div>
                </label>
            </div>
        `).join('');

        const modalHtml = `
            <div class="modal-overlay" id="course-selection-modal">
                <div class="modal-container large">
                    <div class="modal-header">
                        <h3>Select Courses to Import</h3>
                        <button class="modal-close" onclick="integrationManager.closeModal()">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    
                    <div class="modal-content">
                        <p>Select which Canvas courses you'd like to import student data from:</p>
                        
                        <div class="course-selection">
                            ${courseOptions}
                        </div>
                        
                        <div class="import-options">
                            <h4>Import Options</h4>
                            <label class="checkbox-container">
                                <input type="checkbox" checked>
                                <span class="checkmark"></span>
                                Include gradebook data
                            </label>
                            <label class="checkbox-container">
                                <input type="checkbox" checked>
                                <span class="checkmark"></span>
                                Include assignment submissions
                            </label>
                            <label class="checkbox-container">
                                <input type="checkbox">
                                <span class="checkmark"></span>
                                Include discussion participation
                            </label>
                        </div>
                        
                        <div class="modal-actions">
                            <button class="btn btn-secondary" onclick="integrationManager.closeModal()">
                                Cancel
                            </button>
                            <button class="btn btn-primary" onclick="integrationManager.importSelectedCourses()">
                                <i class="fas fa-download"></i>
                                Import Selected Courses
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHtml);
        this.currentModal = document.getElementById('course-selection-modal');
    }

    async importSelectedCourses() {
        const selectedCourses = Array.from(document.querySelectorAll('.course-option input[type="checkbox"]:checked'))
            .map(checkbox => checkbox.value);

        if (selectedCourses.length === 0) {
            alert('Please select at least one course to import.');
            return;
        }

        this.closeModal();
        this.showImportProgress(selectedCourses);
    }

    showImportProgress(selectedCourses) {
        const modalHtml = `
            <div class="modal-overlay" id="import-progress-modal">
                <div class="modal-container">
                    <div class="modal-header">
                        <h3>Importing Canvas Data</h3>
                    </div>
                    
                    <div class="modal-content">
                        <div class="import-progress">
                            <div class="progress-step active">
                                <i class="fas fa-download"></i>
                                <span>Fetching course data...</span>
                            </div>
                            <div class="progress-step">
                                <i class="fas fa-users"></i>
                                <span>Processing student records...</span>
                            </div>
                            <div class="progress-step">
                                <i class="fas fa-chart-line"></i>
                                <span>Generating predictions...</span>
                            </div>
                            <div class="progress-step">
                                <i class="fas fa-check"></i>
                                <span>Import complete!</span>
                            </div>
                        </div>
                        
                        <div class="progress-bar">
                            <div class="progress-fill" id="progress-fill"></div>
                        </div>
                        
                        <div class="progress-details" id="progress-details">
                            Connecting to Canvas...
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHtml);
        this.currentModal = document.getElementById('import-progress-modal');
        
        this.simulateImportProcess(selectedCourses);
    }

    async simulateImportProcess(selectedCourses) {
        const steps = [
            { text: 'Fetching course data...', progress: 25 },
            { text: 'Processing student records...', progress: 50 },
            { text: 'Generating predictions...', progress: 75 },
            { text: 'Import complete!', progress: 100 }
        ];

        const progressFill = document.getElementById('progress-fill');
        const progressDetails = document.getElementById('progress-details');
        const progressSteps = document.querySelectorAll('.progress-step');

        try {
            for (let i = 0; i < steps.length - 1; i++) { // Don't do the last step yet
                const step = steps[i];
                
                // Update progress bar
                progressFill.style.width = `${step.progress}%`;
                progressDetails.textContent = step.text;
                
                // Update step indicators
                progressSteps.forEach((stepEl, index) => {
                    if (index <= i) {
                        stepEl.classList.add('active');
                    }
                });
                
                // Wait before next step
                await new Promise(resolve => setTimeout(resolve, 1200));
            }
            
            // Now do the actual data import
            await this.processCanvasData(selectedCourses);
            
            // Complete the final step
            const finalStep = steps[steps.length - 1];
            progressFill.style.width = `${finalStep.progress}%`;
            progressDetails.textContent = finalStep.text;
            progressSteps.forEach((stepEl, index) => {
                if (index <= steps.length - 1) {
                    stepEl.classList.add('active');
                }
            });
            
            // Wait a moment to show completion, then close
            await new Promise(resolve => setTimeout(resolve, 1500));
            
            this.completeCanvasConnection();
            
        } catch (error) {
            console.error('Import process failed:', error);
            progressDetails.textContent = 'Import failed. Please try again.';
            
            // Close modal after error display
            setTimeout(() => {
                this.closeModal();
            }, 3000);
        }
    }

    async processCanvasData(selectedCourses) {
        try {
            // Call the real Canvas import endpoint
            const response = await fetch('/api/canvas-import/import-courses', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('api_key') || '0dUHi4QroC1GfgnbibLbqowUnv2YFWIe'}`
                },
                body: JSON.stringify({
                    course_ids: selectedCourses,
                    options: {
                        generate_predictions: true,
                        include_gradebook: true,
                        include_submissions: true
                    }
                })
            });
            
            if (response.ok) {
                const result = await response.json();
                console.log('Canvas data imported successfully:', result);
                
                // Store import summary for display
                this.lastImportSummary = result.summary;
                
                return result;
            } else {
                const error = await response.json();
                throw new Error(error.detail || 'Canvas import failed');
            }
        } catch (error) {
            console.error('Error importing Canvas data:', error);
            throw error;
        }
    }

    completeCanvasConnection() {
        this.closeModal();
        
        // Update Canvas integration card status
        const canvasCard = document.querySelector('.integration-card[data-integration="canvas"]');
        const statusBadge = canvasCard.querySelector('#canvas-status');
        
        statusBadge.textContent = 'Connected';
        statusBadge.className = 'status-badge connected';
        
        // Show success notification with import details
        if (window.notificationSystem && this.lastImportSummary) {
            const summary = this.lastImportSummary;
            notificationSystem.showNotification(
                `Canvas LMS connected! Imported ${summary.students_imported} students from ${summary.courses_imported} courses.`, 
                'success'
            );
        } else if (window.notificationSystem) {
            notificationSystem.showNotification('Canvas LMS connected successfully!', 'success');
        }

        // Auto-navigate to AI Analysis tab after successful import
        if (window.modernApp && window.modernApp.appState) {
            // Small delay to ensure notifications are visible before navigation
            setTimeout(() => {
                window.modernApp.appState.setState({ currentTab: 'analyze' });
            }, 1000);
        }

        // Refresh the dashboard if we're on the dashboard tab
        const dashboardTab = document.getElementById('tab-dashboard');
        if (dashboardTab && !dashboardTab.classList.contains('hidden')) {
            if (window.dashboardComponent) {
                dashboardComponent.refreshData();
            }
        }
    }

    showCanvasManagementModal(card) {
        const modalHtml = `
            <div class="modal-overlay" id="canvas-management-modal">
                <div class="modal-container">
                    <div class="modal-header">
                        <h3>Manage Canvas Connection</h3>
                        <button class="modal-close" onclick="integrationManager.closeModal()">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    
                    <div class="modal-content">
                        <div class="connection-info">
                            <div class="status-indicator connected">
                                <i class="fas fa-check-circle"></i>
                                <span>Connected to Canvas</span>
                            </div>
                            
                            <div class="connection-stats">
                                <div class="stat">
                                    <strong>${this.mockCanvasData.courses.length}</strong>
                                    <span>Courses</span>
                                </div>
                                <div class="stat">
                                    <strong id="canvas-student-count">0</strong>
                                    <span>Students</span>
                                </div>
                                <div class="stat">
                                    <strong>Just now</strong>
                                    <span>Last Sync</span>
                                </div>
                            </div>
                        </div>
                        
                        <div class="management-actions">
                            <button class="btn btn-primary" onclick="integrationManager.syncCanvasData()">
                                <i class="fas fa-sync"></i>
                                Sync Now
                            </button>
                            <button class="btn btn-secondary" onclick="integrationManager.showCourseManagement()">
                                <i class="fas fa-cogs"></i>
                                Manage Courses
                            </button>
                            <button class="btn btn-danger" onclick="integrationManager.disconnectCanvas()">
                                <i class="fas fa-unlink"></i>
                                Disconnect
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHtml);
        this.currentModal = document.getElementById('canvas-management-modal');
        
        // Update student count with real data
        this.updateCanvasStudentCount();
    }

    async updateCanvasStudentCount() {
        try {
            const response = await fetch('/api/canvas-import/import-status', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('api_key') || '0dUHi4QroC1GfgnbibLbqowUnv2YFWIe'}`
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                const countElement = document.getElementById('canvas-student-count');
                if (countElement) {
                    countElement.textContent = data.total_canvas_students || 0;
                }
            }
        } catch (error) {
            console.error('Error getting Canvas student count:', error);
        }
    }

    async syncCanvasData() {
        const syncBtn = document.querySelector('.management-actions .btn-primary');
        const originalText = syncBtn.innerHTML;
        
        syncBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Syncing...';
        syncBtn.disabled = true;
        
        // Simulate sync
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        syncBtn.innerHTML = '<i class="fas fa-check"></i> Synced!';
        
        setTimeout(() => {
            syncBtn.innerHTML = originalText;
            syncBtn.disabled = false;
        }, 1000);

        if (window.notificationSystem) {
            notificationSystem.showNotification('Canvas data synced successfully!', 'success');
        }
    }

    disconnectCanvas() {
        if (confirm('Are you sure you want to disconnect from Canvas? This will not delete existing student data.')) {
            const canvasCard = document.querySelector('.integration-card[data-integration="canvas"]');
            const statusBadge = canvasCard.querySelector('#canvas-status');
            
            statusBadge.textContent = 'Not Connected';
            statusBadge.className = 'status-badge';
            
            this.closeModal();
            
            if (window.notificationSystem) {
                notificationSystem.showNotification('Canvas disconnected successfully.', 'info');
            }
        }
    }

    showComingSoonModal(platform) {
        const modalHtml = `
            <div class="modal-overlay" id="coming-soon-modal">
                <div class="modal-container">
                    <div class="modal-header">
                        <h3>${platform} Integration</h3>
                        <button class="modal-close" onclick="integrationManager.closeModal()">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    
                    <div class="modal-content">
                        <div class="coming-soon-content">
                            <i class="fas fa-clock"></i>
                            <h4>Coming Soon</h4>
                            <p>${platform} integration is currently in development.</p>
                            <p>For now, you can use Canvas LMS or upload CSV files directly.</p>
                        </div>
                        
                        <div class="modal-actions">
                            <button class="btn btn-primary" onclick="integrationManager.closeModal()">
                                Got it
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHtml);
        this.currentModal = document.getElementById('coming-soon-modal');
    }

    closeModal() {
        if (this.currentModal) {
            this.currentModal.remove();
            this.currentModal = null;
        }
    }

    generateMockCanvasData() {
        return {
            courses: [
                {
                    id: '12345',
                    name: 'Algebra I - Period 1',
                    code: 'MATH-ALG1-P1',
                    students: 28,
                    assignments: 15
                },
                {
                    id: '12346', 
                    name: 'English 9 - Period 3',
                    code: 'ENG-9-P3',
                    students: 24,
                    assignments: 22
                },
                {
                    id: '12347',
                    name: 'Biology - Period 5',
                    code: 'SCI-BIO-P5',
                    students: 26,
                    assignments: 18
                },
                {
                    id: '12348',
                    name: 'World History - Period 2',
                    code: 'HIST-WH-P2', 
                    students: 30,
                    assignments: 12
                }
            ]
        };
    }
}

// Initialize integration manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.integrationManager = new IntegrationManager();
});