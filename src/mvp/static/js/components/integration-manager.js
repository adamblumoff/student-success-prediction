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
                this.showPowerSchoolConnectionModal(card);
                break;
            case 'google':
                this.showGoogleClassroomConnectionModal(card);
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
                    'Authorization': `Bearer ${sessionStorage.getItem('auth_token') || ''}`
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
                    'Authorization': `Bearer ${sessionStorage.getItem('auth_token') || ''}`
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

    // ===== POWERSCHOOL INTEGRATION METHODS =====
    
    showPowerSchoolConnectionModal(card) {
        const statusBadge = card.querySelector('#powerschool-status');
        const isConnected = statusBadge.textContent === 'Connected';

        if (isConnected) {
            this.showPowerSchoolManagementModal(card);
            return;
        }

        const modalHtml = `
            <div class="modal-overlay" id="powerschool-connection-modal">
                <div class="modal-container">
                    <div class="modal-header">
                        <h3>Connect to PowerSchool SIS</h3>
                        <button class="modal-close" onclick="integrationManager.closeModal()">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    
                    <div class="modal-content">
                        <div class="connection-form">
                            <div class="form-group">
                                <label for="powerschool-server">PowerSchool Server URL</label>
                                <input type="url" 
                                       id="powerschool-server" 
                                       placeholder="https://powerschool.yourdistrict.com"
                                       value="https://demo-powerschool.school.edu">
                                <small>Your district's PowerSchool server URL</small>
                            </div>
                            
                            <div class="form-group">
                                <label for="powerschool-username">Username</label>
                                <input type="text" 
                                       id="powerschool-username" 
                                       placeholder="Enter username">
                                <small>PowerSchool administrator username</small>
                            </div>
                            
                            <div class="form-group">
                                <label for="powerschool-password">Password</label>
                                <input type="password" 
                                       id="powerschool-password" 
                                       placeholder="••••••••">
                                <small>PowerSchool administrator password</small>
                            </div>

                            <div class="connection-status" id="powerschool-connection-status" style="display: none;">
                                <!-- Status messages appear here -->
                            </div>
                            
                            <div class="modal-actions">
                                <button class="btn btn-secondary" onclick="integrationManager.closeModal()">
                                    Cancel
                                </button>
                                <button class="btn btn-primary" id="test-powerschool-connection-btn" onclick="integrationManager.testPowerSchoolConnection()">
                                    <i class="fas fa-plug"></i>
                                    Test Connection
                                </button>
                                <button class="btn btn-success" id="connect-powerschool-btn" style="display: none;" onclick="integrationManager.connectToPowerSchool()">
                                    <i class="fas fa-check"></i>
                                    Connect & Import Schools
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHtml);
        this.currentModal = document.getElementById('powerschool-connection-modal');
    }

    async testPowerSchoolConnection() {
        const testBtn = document.getElementById('test-powerschool-connection-btn');
        const connectBtn = document.getElementById('connect-powerschool-btn');
        const statusDiv = document.getElementById('powerschool-connection-status');

        // Show loading state
        testBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Testing...';
        testBtn.disabled = true;
        statusDiv.style.display = 'block';
        statusDiv.innerHTML = '<div class="status-loading">Testing PowerSchool connection...</div>';

        try {
            // Get form values
            const serverUrl = document.getElementById('powerschool-server').value;
            const username = document.getElementById('powerschool-username').value;
            const password = document.getElementById('powerschool-password').value;

            // Test connection
            const response = await fetch('/api/powerschool-import/test-connection', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${sessionStorage.getItem('auth_token') || ''}`
                },
                body: JSON.stringify({
                    server_url: serverUrl,
                    username: username,
                    password: password
                })
            });

            const result = await response.json();

            if (response.ok && result.success) {
                // Store connection info for later use
                this.powerSchoolConnectionData = result;

                statusDiv.innerHTML = `
                    <div class="status-success">
                        <i class="fas fa-check-circle"></i>
                        <strong>Connection Successful!</strong>
                        <br>Found ${result.schools_found} schools in ${result.server_info.district_name}
                    </div>
                `;

                testBtn.style.display = 'none';
                connectBtn.style.display = 'inline-flex';
            } else {
                throw new Error(result.detail || 'Connection failed');
            }

        } catch (error) {
            console.error('PowerSchool connection test failed:', error);
            statusDiv.innerHTML = `
                <div class="status-error">
                    <i class="fas fa-exclamation-circle"></i>
                    <strong>Connection Failed</strong>
                    <br>${error.message}
                </div>
            `;

            testBtn.innerHTML = '<i class="fas fa-plug"></i> Test Connection';
            testBtn.disabled = false;
        }
    }

    async connectToPowerSchool() {
        const connectBtn = document.getElementById('connect-powerschool-btn');
        const statusDiv = document.getElementById('powerschool-connection-status');

        // Show loading
        connectBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Connecting...';
        connectBtn.disabled = true;

        // Simulate connection process
        await new Promise(resolve => setTimeout(resolve, 1000));

        this.showPowerSchoolSelectionModal();
    }

    showPowerSchoolSelectionModal() {
        this.closeModal();

        // Use schools from connection test
        const schools = this.powerSchoolConnectionData?.schools || [
            { id: 'PS001', name: 'Lincoln Elementary School', type: 'Elementary', grades: ['K', '1', '2', '3', '4', '5'], expected_students: 132 },
            { id: 'PS002', name: 'Roosevelt Middle School', type: 'Middle', grades: ['6', '7', '8'], expected_students: 84 },
            { id: 'PS003', name: 'Washington High School', type: 'High', grades: ['9', '10', '11', '12'], expected_students: 128 },
            { id: 'PS004', name: 'Jefferson Elementary School', type: 'Elementary', grades: ['K', '1', '2', '3', '4', '5'], expected_students: 120 }
        ];

        const schoolOptions = schools.map(school => `
            <div class="school-option">
                <label class="checkbox-container">
                    <input type="checkbox" value="${school.id}" checked>
                    <span class="checkmark"></span>
                    <div class="school-info">
                        <h4>${school.name}</h4>
                        <p>${school.expected_students} students • ${school.type} School</p>
                        <span class="school-code">Grades: ${school.grade_range || school.grades?.join(', ') || 'K-12'}</span>
                    </div>
                </label>
            </div>
        `).join('');

        const modalHtml = `
            <div class="modal-overlay" id="powerschool-selection-modal">
                <div class="modal-container large">
                    <div class="modal-header">
                        <h3>Select Schools to Import</h3>
                        <button class="modal-close" onclick="integrationManager.closeModal()">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    
                    <div class="modal-content">
                        <p>Select which PowerSchool schools you'd like to import student data from:</p>
                        
                        <div class="school-selection">
                            ${schoolOptions}
                        </div>
                        
                        <div class="import-options">
                            <h4>Import Options</h4>
                            <label class="checkbox-container">
                                <input type="checkbox" checked>
                                <span class="checkmark"></span>
                                Include demographic data
                            </label>
                            <label class="checkbox-container">
                                <input type="checkbox" checked>
                                <span class="checkmark"></span>
                                Include attendance records
                            </label>
                            <label class="checkbox-container">
                                <input type="checkbox" checked>
                                <span class="checkmark"></span>
                                Include behavioral data
                            </label>
                            <label class="checkbox-container">
                                <input type="checkbox">
                                <span class="checkmark"></span>
                                Include special education data
                            </label>
                        </div>
                        
                        <div class="modal-actions">
                            <button class="btn btn-secondary" onclick="integrationManager.closeModal()">
                                Cancel
                            </button>
                            <button class="btn btn-primary" onclick="integrationManager.importSelectedPowerSchoolSchools()">
                                <i class="fas fa-download"></i>
                                Import Selected Schools
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHtml);
        this.currentModal = document.getElementById('powerschool-selection-modal');
    }

    async importSelectedPowerSchoolSchools() {
        const selectedSchools = Array.from(document.querySelectorAll('.school-option input[type="checkbox"]:checked'))
            .map(checkbox => checkbox.value);

        if (selectedSchools.length === 0) {
            alert('Please select at least one school to import.');
            return;
        }

        this.closeModal();
        this.showPowerSchoolImportProgress(selectedSchools);
    }

    showPowerSchoolImportProgress(selectedSchools) {
        const modalHtml = `
            <div class="modal-overlay" id="powerschool-import-progress-modal">
                <div class="modal-container">
                    <div class="modal-header">
                        <h3>Importing PowerSchool Data</h3>
                    </div>
                    
                    <div class="modal-content">
                        <div class="import-progress">
                            <div class="progress-step active">
                                <i class="fas fa-download"></i>
                                <span>Fetching school data...</span>
                            </div>
                            <div class="progress-step">
                                <i class="fas fa-users"></i>
                                <span>Processing student records...</span>
                            </div>
                            <div class="progress-step">
                                <i class="fas fa-chart-line"></i>
                                <span>Generating risk assessments...</span>
                            </div>
                            <div class="progress-step">
                                <i class="fas fa-check"></i>
                                <span>Import complete!</span>
                            </div>
                        </div>
                        
                        <div class="progress-bar">
                            <div class="progress-fill" id="powerschool-progress-fill"></div>
                        </div>
                        
                        <div class="progress-details" id="powerschool-progress-details">
                            Connecting to PowerSchool...
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHtml);
        this.currentModal = document.getElementById('powerschool-import-progress-modal');
        
        this.simulatePowerSchoolImportProcess(selectedSchools);
    }

    async simulatePowerSchoolImportProcess(selectedSchools) {
        const steps = [
            { text: 'Fetching school data...', progress: 25 },
            { text: 'Processing student records...', progress: 50 },
            { text: 'Generating risk assessments...', progress: 75 },
            { text: 'Import complete!', progress: 100 }
        ];

        const progressFill = document.getElementById('powerschool-progress-fill');
        const progressDetails = document.getElementById('powerschool-progress-details');
        const progressSteps = document.querySelectorAll('.progress-step');

        try {
            for (let i = 0; i < steps.length - 1; i++) {
                const step = steps[i];
                
                progressFill.style.width = `${step.progress}%`;
                progressDetails.textContent = step.text;
                
                progressSteps.forEach((stepEl, index) => {
                    if (index <= i) {
                        stepEl.classList.add('active');
                    }
                });
                
                await new Promise(resolve => setTimeout(resolve, 1200));
            }
            
            // Do the actual data import
            await this.processPowerSchoolData(selectedSchools);
            
            // Complete the final step
            const finalStep = steps[steps.length - 1];
            progressFill.style.width = `${finalStep.progress}%`;
            progressDetails.textContent = finalStep.text;
            progressSteps.forEach((stepEl, index) => {
                if (index <= steps.length - 1) {
                    stepEl.classList.add('active');
                }
            });
            
            await new Promise(resolve => setTimeout(resolve, 1500));
            
            this.completePowerSchoolConnection();
            
        } catch (error) {
            console.error('PowerSchool import process failed:', error);
            progressDetails.textContent = 'Import failed. Please try again.';
            
            setTimeout(() => {
                this.closeModal();
            }, 3000);
        }
    }

    async processPowerSchoolData(selectedSchools) {
        try {
            const response = await fetch('/api/powerschool-import/import-schools', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${sessionStorage.getItem('auth_token') || ''}`
                },
                body: JSON.stringify({
                    school_ids: selectedSchools,
                    options: {
                        generate_predictions: true,
                        include_demographics: true,
                        include_attendance: true,
                        include_behavioral: true
                    }
                })
            });
            
            if (response.ok) {
                const result = await response.json();
                console.log('PowerSchool data imported successfully:', result);
                
                this.lastPowerSchoolImportSummary = result.summary;
                
                return result;
            } else {
                const error = await response.json();
                throw new Error(error.detail || 'PowerSchool import failed');
            }
        } catch (error) {
            console.error('Error importing PowerSchool data:', error);
            throw error;
        }
    }

    completePowerSchoolConnection() {
        this.closeModal();
        
        // Update PowerSchool integration card status
        const powerSchoolCard = document.querySelector('.integration-card[data-integration="powerschool"]');
        const statusBadge = powerSchoolCard.querySelector('#powerschool-status');
        
        statusBadge.textContent = 'Connected';
        statusBadge.className = 'status-badge connected';
        
        // Show success notification with import details
        if (window.notificationSystem && this.lastPowerSchoolImportSummary) {
            const summary = this.lastPowerSchoolImportSummary;
            notificationSystem.showNotification(
                `PowerSchool SIS connected! Imported ${summary.students_imported} students from ${summary.schools_imported} schools.`, 
                'success'
            );
        } else if (window.notificationSystem) {
            notificationSystem.showNotification('PowerSchool SIS connected successfully!', 'success');
        }

        // Auto-navigate to AI Analysis tab after successful import
        if (window.modernApp && window.modernApp.appState) {
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

    showPowerSchoolManagementModal(card) {
        const modalHtml = `
            <div class="modal-overlay" id="powerschool-management-modal">
                <div class="modal-container">
                    <div class="modal-header">
                        <h3>Manage PowerSchool Connection</h3>
                        <button class="modal-close" onclick="integrationManager.closeModal()">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    
                    <div class="modal-content">
                        <div class="connection-info">
                            <div class="status-indicator connected">
                                <i class="fas fa-check-circle"></i>
                                <span>Connected to PowerSchool</span>
                            </div>
                            
                            <div class="connection-stats">
                                <div class="stat">
                                    <strong>4</strong>
                                    <span>Schools</span>
                                </div>
                                <div class="stat">
                                    <strong id="powerschool-student-count">0</strong>
                                    <span>Students</span>
                                </div>
                                <div class="stat">
                                    <strong>Just now</strong>
                                    <span>Last Sync</span>
                                </div>
                            </div>
                        </div>
                        
                        <div class="management-actions">
                            <button class="btn btn-primary" onclick="integrationManager.syncPowerSchoolData()">
                                <i class="fas fa-sync"></i>
                                Sync Now
                            </button>
                            <button class="btn btn-secondary" onclick="integrationManager.showPowerSchoolManagement()">
                                <i class="fas fa-cogs"></i>
                                Manage Schools
                            </button>
                            <button class="btn btn-danger" onclick="integrationManager.disconnectPowerSchool()">
                                <i class="fas fa-unlink"></i>
                                Disconnect
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHtml);
        this.currentModal = document.getElementById('powerschool-management-modal');
        
        this.updatePowerSchoolStudentCount();
    }

    async updatePowerSchoolStudentCount() {
        try {
            const response = await fetch('/api/powerschool-import/import-status', {
                headers: {
                    'Authorization': `Bearer ${sessionStorage.getItem('auth_token') || ''}`
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                const countElement = document.getElementById('powerschool-student-count');
                if (countElement) {
                    countElement.textContent = data.total_powerschool_students || 0;
                }
            }
        } catch (error) {
            console.error('Error getting PowerSchool student count:', error);
        }
    }

    async syncPowerSchoolData() {
        const syncBtn = document.querySelector('.management-actions .btn-primary');
        const originalText = syncBtn.innerHTML;
        
        syncBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Syncing...';
        syncBtn.disabled = true;
        
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        syncBtn.innerHTML = '<i class="fas fa-check"></i> Synced!';
        
        setTimeout(() => {
            syncBtn.innerHTML = originalText;
            syncBtn.disabled = false;
        }, 1000);

        if (window.notificationSystem) {
            notificationSystem.showNotification('PowerSchool data synced successfully!', 'success');
        }
    }

    disconnectPowerSchool() {
        if (confirm('Are you sure you want to disconnect from PowerSchool? This will not delete existing student data.')) {
            const powerSchoolCard = document.querySelector('.integration-card[data-integration="powerschool"]');
            const statusBadge = powerSchoolCard.querySelector('#powerschool-status');
            
            statusBadge.textContent = 'Not Connected';
            statusBadge.className = 'status-badge';
            
            this.closeModal();
            
            if (window.notificationSystem) {
                notificationSystem.showNotification('PowerSchool disconnected successfully.', 'info');
            }
        }
    }

    // ===== END POWERSCHOOL INTEGRATION METHODS =====

    // ===== GOOGLE CLASSROOM INTEGRATION METHODS =====
    
    showGoogleClassroomConnectionModal(card) {
        const statusBadge = card.querySelector('#google-status');
        const isConnected = statusBadge.textContent === 'Connected';

        if (isConnected) {
            this.showGoogleClassroomManagementModal(card);
            return;
        }

        const modalHtml = `
            <div class="modal-overlay" id="google-classroom-connection-modal">
                <div class="modal-container">
                    <div class="modal-header">
                        <h3>Connect to Google Classroom</h3>
                        <button class="modal-close" onclick="integrationManager.closeModal()">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    
                    <div class="modal-content">
                        <div class="connection-form">
                            <div class="form-group">
                                <label for="google-service-key">Service Account Key (JSON)</label>
                                <textarea id="google-service-key" 
                                         rows="6"
                                         placeholder="Paste your Google Service Account JSON key here...">{
  "type": "service_account",
  "project_id": "demo-classroom-project",
  "private_key_id": "demo123",
  "private_key": "-----BEGIN PRIVATE KEY-----\nDEMO_KEY_CONTENT\n-----END PRIVATE KEY-----",
  "client_email": "classroom-service@demo-project.iam.gserviceaccount.com",
  "client_id": "123456789",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token"
}</textarea>
                                <small>Generate from Google Cloud Console → IAM & Admin → Service Accounts</small>
                            </div>
                            
                            <div class="form-group">
                                <label for="google-domain">School Domain</label>
                                <input type="text" 
                                       id="google-domain" 
                                       placeholder="yourschool.edu"
                                       value="demo-school.edu">
                                <small>Your school's Google Workspace domain</small>
                            </div>
                            
                            <div class="form-group">
                                <label for="google-admin-email">Admin Email</label>
                                <input type="email" 
                                       id="google-admin-email" 
                                       placeholder="admin@yourschool.edu">
                                <small>Google Workspace admin email for delegation</small>
                            </div>

                            <div class="connection-status" id="google-connection-status" style="display: none;">
                                <!-- Status messages appear here -->
                            </div>
                            
                            <div class="modal-actions">
                                <button class="btn btn-secondary" onclick="integrationManager.closeModal()">
                                    Cancel
                                </button>
                                <button class="btn btn-primary" id="test-google-connection-btn" onclick="integrationManager.testGoogleClassroomConnection()">
                                    <i class="fas fa-plug"></i>
                                    Test Connection
                                </button>
                                <button class="btn btn-success" id="connect-google-btn" style="display: none;" onclick="integrationManager.connectToGoogleClassroom()">
                                    <i class="fas fa-check"></i>
                                    Connect & Import Classrooms
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHtml);
        this.currentModal = document.getElementById('google-classroom-connection-modal');
    }

    async testGoogleClassroomConnection() {
        const testBtn = document.getElementById('test-google-connection-btn');
        const connectBtn = document.getElementById('connect-google-btn');
        const statusDiv = document.getElementById('google-connection-status');

        // Show loading state
        testBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Testing...';
        testBtn.disabled = true;
        statusDiv.style.display = 'block';
        statusDiv.innerHTML = '<div class="status-loading">Testing Google Classroom connection...</div>';

        try {
            // Get form values
            const serviceAccountKey = document.getElementById('google-service-key').value;
            const domain = document.getElementById('google-domain').value;
            const adminEmail = document.getElementById('google-admin-email').value;

            // Test connection
            const response = await fetch('/api/google-classroom-import/test-connection', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${sessionStorage.getItem('auth_token') || ''}`
                },
                body: JSON.stringify({
                    service_account_key: serviceAccountKey,
                    domain: domain,
                    admin_email: adminEmail
                })
            });

            const result = await response.json();

            if (response.ok && result.success) {
                // Store connection info for later use
                this.googleClassroomConnectionData = result;

                statusDiv.innerHTML = `
                    <div class="status-success">
                        <i class="fas fa-check-circle"></i>
                        <strong>Connection Successful!</strong>
                        <br>Found ${result.classrooms_found} classrooms in ${result.service_info.district_name}
                    </div>
                `;

                testBtn.style.display = 'none';
                connectBtn.style.display = 'inline-flex';
            } else {
                throw new Error(result.detail || 'Connection failed');
            }

        } catch (error) {
            console.error('Google Classroom connection test failed:', error);
            statusDiv.innerHTML = `
                <div class="status-error">
                    <i class="fas fa-exclamation-circle"></i>
                    <strong>Connection Failed</strong>
                    <br>${error.message}
                </div>
            `;

            testBtn.innerHTML = '<i class="fas fa-plug"></i> Test Connection';
            testBtn.disabled = false;
        }
    }

    async connectToGoogleClassroom() {
        const connectBtn = document.getElementById('connect-google-btn');
        const statusDiv = document.getElementById('google-connection-status');

        // Show loading
        connectBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Connecting...';
        connectBtn.disabled = true;

        // Simulate connection process
        await new Promise(resolve => setTimeout(resolve, 1000));

        this.showGoogleClassroomSelectionModal();
    }

    showGoogleClassroomSelectionModal() {
        this.closeModal();

        // Use classrooms from connection test
        const classrooms = this.googleClassroomConnectionData?.classrooms || [
            { id: 'GC001', name: 'Mrs. Johnson\'s 3rd Grade', subject: 'Elementary', grade_level: '3', teacher: 'Mrs. Sarah Johnson', expected_students: 24 },
            { id: 'GC002', name: 'Mr. Davis\'s 5th Grade Math', subject: 'Mathematics', grade_level: '5', teacher: 'Mr. Michael Davis', expected_students: 26 },
            { id: 'GC003', name: 'Ms. Rodriguez\'s 7th Grade Science', subject: 'Science', grade_level: '7', teacher: 'Ms. Maria Rodriguez', expected_students: 28 },
            { id: 'GC004', name: 'Mr. Thompson\'s High School English', subject: 'English', grade_level: '10', teacher: 'Mr. Robert Thompson', expected_students: 32 },
            { id: 'GC005', name: 'Mrs. Wilson\'s AP Biology', subject: 'Biology', grade_level: '11', teacher: 'Mrs. Jennifer Wilson', expected_students: 22 }
        ];

        const classroomOptions = classrooms.map(classroom => `
            <div class="classroom-option">
                <label class="checkbox-container">
                    <input type="checkbox" value="${classroom.id}" checked>
                    <span class="checkmark"></span>
                    <div class="classroom-info">
                        <h4>${classroom.name}</h4>
                        <p>${classroom.expected_students} students • ${classroom.subject}</p>
                        <span class="classroom-code">Teacher: ${classroom.teacher}</span>
                    </div>
                </label>
            </div>
        `).join('');

        const modalHtml = `
            <div class="modal-overlay" id="google-classroom-selection-modal">
                <div class="modal-container large">
                    <div class="modal-header">
                        <h3>Select Classrooms to Import</h3>
                        <button class="modal-close" onclick="integrationManager.closeModal()">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    
                    <div class="modal-content">
                        <p>Select which Google Classrooms you'd like to import student data from:</p>
                        
                        <div class="classroom-selection">
                            ${classroomOptions}
                        </div>
                        
                        <div class="import-options">
                            <h4>Import Options</h4>
                            <label class="checkbox-container">
                                <input type="checkbox" checked>
                                <span class="checkmark"></span>
                                Include assignment grades
                            </label>
                            <label class="checkbox-container">
                                <input type="checkbox" checked>
                                <span class="checkmark"></span>
                                Include participation data
                            </label>
                            <label class="checkbox-container">
                                <input type="checkbox" checked>
                                <span class="checkmark"></span>
                                Include submission patterns
                            </label>
                            <label class="checkbox-container">
                                <input type="checkbox">
                                <span class="checkmark"></span>
                                Include guardian contacts
                            </label>
                        </div>
                        
                        <div class="modal-actions">
                            <button class="btn btn-secondary" onclick="integrationManager.closeModal()">
                                Cancel
                            </button>
                            <button class="btn btn-primary" onclick="integrationManager.importSelectedGoogleClassrooms()">
                                <i class="fas fa-download"></i>
                                Import Selected Classrooms
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHtml);
        this.currentModal = document.getElementById('google-classroom-selection-modal');
    }

    async importSelectedGoogleClassrooms() {
        const selectedClassrooms = Array.from(document.querySelectorAll('.classroom-option input[type="checkbox"]:checked'))
            .map(checkbox => checkbox.value);

        if (selectedClassrooms.length === 0) {
            alert('Please select at least one classroom to import.');
            return;
        }

        this.closeModal();
        this.showGoogleClassroomImportProgress(selectedClassrooms);
    }

    showGoogleClassroomImportProgress(selectedClassrooms) {
        const modalHtml = `
            <div class="modal-overlay" id="google-classroom-import-progress-modal">
                <div class="modal-container">
                    <div class="modal-header">
                        <h3>Importing Google Classroom Data</h3>
                    </div>
                    
                    <div class="modal-content">
                        <div class="import-progress">
                            <div class="progress-step active">
                                <i class="fas fa-download"></i>
                                <span>Fetching classroom data...</span>
                            </div>
                            <div class="progress-step">
                                <i class="fas fa-users"></i>
                                <span>Processing student records...</span>
                            </div>
                            <div class="progress-step">
                                <i class="fas fa-chart-line"></i>
                                <span>Analyzing participation patterns...</span>
                            </div>
                            <div class="progress-step">
                                <i class="fas fa-check"></i>
                                <span>Import complete!</span>
                            </div>
                        </div>
                        
                        <div class="progress-bar">
                            <div class="progress-fill" id="google-classroom-progress-fill"></div>
                        </div>
                        
                        <div class="progress-details" id="google-classroom-progress-details">
                            Connecting to Google Classroom...
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHtml);
        this.currentModal = document.getElementById('google-classroom-import-progress-modal');
        
        this.simulateGoogleClassroomImportProcess(selectedClassrooms);
    }

    async simulateGoogleClassroomImportProcess(selectedClassrooms) {
        const steps = [
            { text: 'Fetching classroom data...', progress: 25 },
            { text: 'Processing student records...', progress: 50 },
            { text: 'Analyzing participation patterns...', progress: 75 },
            { text: 'Import complete!', progress: 100 }
        ];

        const progressFill = document.getElementById('google-classroom-progress-fill');
        const progressDetails = document.getElementById('google-classroom-progress-details');
        const progressSteps = document.querySelectorAll('.progress-step');

        try {
            for (let i = 0; i < steps.length - 1; i++) {
                const step = steps[i];
                
                progressFill.style.width = `${step.progress}%`;
                progressDetails.textContent = step.text;
                
                progressSteps.forEach((stepEl, index) => {
                    if (index <= i) {
                        stepEl.classList.add('active');
                    }
                });
                
                await new Promise(resolve => setTimeout(resolve, 1200));
            }
            
            // Do the actual data import
            await this.processGoogleClassroomData(selectedClassrooms);
            
            // Complete the final step
            const finalStep = steps[steps.length - 1];
            progressFill.style.width = `${finalStep.progress}%`;
            progressDetails.textContent = finalStep.text;
            progressSteps.forEach((stepEl, index) => {
                if (index <= steps.length - 1) {
                    stepEl.classList.add('active');
                }
            });
            
            await new Promise(resolve => setTimeout(resolve, 1500));
            
            this.completeGoogleClassroomConnection();
            
        } catch (error) {
            console.error('Google Classroom import process failed:', error);
            progressDetails.textContent = 'Import failed. Please try again.';
            
            setTimeout(() => {
                this.closeModal();
            }, 3000);
        }
    }

    async processGoogleClassroomData(selectedClassrooms) {
        try {
            const response = await fetch('/api/google-classroom-import/import-classrooms', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${sessionStorage.getItem('auth_token') || ''}`
                },
                body: JSON.stringify({
                    classroom_ids: selectedClassrooms,
                    options: {
                        generate_predictions: true,
                        include_assignments: true,
                        include_participation: true,
                        include_submissions: true
                    }
                })
            });
            
            if (response.ok) {
                const result = await response.json();
                console.log('Google Classroom data imported successfully:', result);
                
                this.lastGoogleClassroomImportSummary = result.summary;
                
                return result;
            } else {
                const error = await response.json();
                throw new Error(error.detail || 'Google Classroom import failed');
            }
        } catch (error) {
            console.error('Error importing Google Classroom data:', error);
            throw error;
        }
    }

    completeGoogleClassroomConnection() {
        this.closeModal();
        
        // Update Google Classroom integration card status
        const googleClassroomCard = document.querySelector('.integration-card[data-integration="google"]');
        const statusBadge = googleClassroomCard.querySelector('#google-status');
        
        statusBadge.textContent = 'Connected';
        statusBadge.className = 'status-badge connected';
        
        // Show success notification with import details
        if (window.notificationSystem && this.lastGoogleClassroomImportSummary) {
            const summary = this.lastGoogleClassroomImportSummary;
            notificationSystem.showNotification(
                `Google Classroom connected! Imported ${summary.students_imported} students from ${summary.classrooms_imported} classrooms.`, 
                'success'
            );
        } else if (window.notificationSystem) {
            notificationSystem.showNotification('Google Classroom connected successfully!', 'success');
        }

        // Auto-navigate to AI Analysis tab after successful import
        if (window.modernApp && window.modernApp.appState) {
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

    showGoogleClassroomManagementModal(card) {
        const modalHtml = `
            <div class="modal-overlay" id="google-classroom-management-modal">
                <div class="modal-container">
                    <div class="modal-header">
                        <h3>Manage Google Classroom Connection</h3>
                        <button class="modal-close" onclick="integrationManager.closeModal()">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    
                    <div class="modal-content">
                        <div class="connection-info">
                            <div class="status-indicator connected">
                                <i class="fas fa-check-circle"></i>
                                <span>Connected to Google Classroom</span>
                            </div>
                            
                            <div class="connection-stats">
                                <div class="stat">
                                    <strong>5</strong>
                                    <span>Classrooms</span>
                                </div>
                                <div class="stat">
                                    <strong id="google-classroom-student-count">0</strong>
                                    <span>Students</span>
                                </div>
                                <div class="stat">
                                    <strong>Just now</strong>
                                    <span>Last Sync</span>
                                </div>
                            </div>
                        </div>
                        
                        <div class="management-actions">
                            <button class="btn btn-primary" onclick="integrationManager.syncGoogleClassroomData()">
                                <i class="fas fa-sync"></i>
                                Sync Now
                            </button>
                            <button class="btn btn-secondary" onclick="integrationManager.showGoogleClassroomManagement()">
                                <i class="fas fa-cogs"></i>
                                Manage Classrooms
                            </button>
                            <button class="btn btn-danger" onclick="integrationManager.disconnectGoogleClassroom()">
                                <i class="fas fa-unlink"></i>
                                Disconnect
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHtml);
        this.currentModal = document.getElementById('google-classroom-management-modal');
        
        this.updateGoogleClassroomStudentCount();
    }

    async updateGoogleClassroomStudentCount() {
        try {
            const response = await fetch('/api/google-classroom-import/import-status', {
                headers: {
                    'Authorization': `Bearer ${sessionStorage.getItem('auth_token') || ''}`
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                const countElement = document.getElementById('google-classroom-student-count');
                if (countElement) {
                    countElement.textContent = data.total_students || 0;
                }
            }
        } catch (error) {
            console.error('Error getting Google Classroom student count:', error);
        }
    }

    async syncGoogleClassroomData() {
        const syncBtn = document.querySelector('.management-actions .btn-primary');
        const originalText = syncBtn.innerHTML;
        
        syncBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Syncing...';
        syncBtn.disabled = true;
        
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        syncBtn.innerHTML = '<i class="fas fa-check"></i> Synced!';
        
        setTimeout(() => {
            syncBtn.innerHTML = originalText;
            syncBtn.disabled = false;
        }, 1000);

        if (window.notificationSystem) {
            notificationSystem.showNotification('Google Classroom data synced successfully!', 'success');
        }
    }

    disconnectGoogleClassroom() {
        if (confirm('Are you sure you want to disconnect from Google Classroom? This will not delete existing student data.')) {
            const googleClassroomCard = document.querySelector('.integration-card[data-integration="google"]');
            const statusBadge = googleClassroomCard.querySelector('#google-status');
            
            statusBadge.textContent = 'Not Connected';
            statusBadge.className = 'status-badge';
            
            this.closeModal();
            
            if (window.notificationSystem) {
                notificationSystem.showNotification('Google Classroom disconnected successfully.', 'info');
            }
        }
    }

    // ===== END GOOGLE CLASSROOM INTEGRATION METHODS =====

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