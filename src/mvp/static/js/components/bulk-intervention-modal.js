/**
 * Bulk Intervention Modal
 * Handles creation of interventions for multiple students with progress tracking
 */

class BulkInterventionModal {
    constructor() {
        this.isProcessing = false;
        this.results = [];
        this.bindEvents();
    }

    bindEvents() {
        // Listen for bulk intervention creation requests
        if (window.selectionManager) {
            window.selectionManager.on('bulkCreateIntervention', (studentIds) => {
                this.showModal(studentIds);
            });
        }
    }

    showModal(studentIds) {
        if (!studentIds || studentIds.length === 0) {
            this.showNotification('No students selected for intervention creation', 'warning');
            return;
        }

        console.log('🎯 Opening bulk intervention modal for students:', studentIds);

        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.id = 'bulk-intervention-modal';

        modal.innerHTML = `
            <div class="modal bulk-intervention-modal">
                <div class="modal-header">
                    <h3>
                        <i class="fas fa-users"></i>
                        Create Intervention for ${studentIds.length} Students
                    </h3>
                    <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">&times;</button>
                </div>
                
                <div class="modal-body">
                    <div class="bulk-form-section" id="bulk-form-section">
                        <div class="selected-students-preview">
                            <h4>Selected Students (${studentIds.length})</h4>
                            <div class="students-grid" id="selected-students-grid">
                                <div class="loading-students">
                                    <i class="fas fa-spinner fa-spin"></i>
                                    Loading student information...
                                </div>
                            </div>
                        </div>

                        <form id="bulk-intervention-form" class="intervention-form">
                            <div class="form-group">
                                <label for="bulk-intervention-type">Intervention Type</label>
                                <select id="bulk-intervention-type" name="intervention_type" required>
                                    <option value="">Select intervention type...</option>
                                    <option value="academic_support">Academic Support</option>
                                    <option value="attendance_support">Attendance Support</option>
                                    <option value="behavioral_support">Behavioral Support</option>
                                    <option value="engagement_support">Engagement Support</option>
                                    <option value="family_engagement">Family Engagement</option>
                                    <option value="college_career">College & Career</option>
                                    <option value="health_wellness">Health & Wellness</option>
                                    <option value="technology_support">Technology Support</option>
                                </select>
                            </div>

                            <div class="form-group">
                                <label for="bulk-title">Intervention Title</label>
                                <input type="text" id="bulk-title" name="title" required 
                                       placeholder="e.g., Math Tutoring Program" maxlength="200">
                            </div>

                            <div class="form-group">
                                <label for="bulk-description">Description</label>
                                <textarea id="bulk-description" name="description" rows="3" 
                                          placeholder="Describe the intervention details..." maxlength="1000"></textarea>
                            </div>

                            <div class="form-row">
                                <div class="form-group">
                                    <label for="bulk-priority">Priority</label>
                                    <select id="bulk-priority" name="priority">
                                        <option value="low">Low</option>
                                        <option value="medium" selected>Medium</option>
                                        <option value="high">High</option>
                                        <option value="critical">Critical</option>
                                    </select>
                                </div>

                                <div class="form-group">
                                    <label for="bulk-assigned-to">Assigned To</label>
                                    <input type="text" id="bulk-assigned-to" name="assigned_to" 
                                           placeholder="Teacher or staff name" maxlength="100">
                                </div>
                            </div>

                            <div class="form-group">
                                <label for="bulk-due-date">Due Date</label>
                                <input type="datetime-local" id="bulk-due-date" name="due_date">
                            </div>
                        </form>
                    </div>

                    <!-- Progress Section (hidden initially) -->
                    <div class="bulk-progress-section hidden" id="bulk-progress-section">
                        <div class="progress-header">
                            <h4>Creating Interventions...</h4>
                            <div class="progress-stats">
                                <span class="progress-current">0</span> / <span class="progress-total">${studentIds.length}</span>
                            </div>
                        </div>
                        
                        <div class="progress-bar">
                            <div class="progress-fill" id="bulk-progress-fill"></div>
                        </div>
                        
                        <div class="progress-details" id="bulk-progress-details">
                            <div class="progress-message">Preparing to create interventions...</div>
                        </div>
                    </div>

                    <!-- Results Section (hidden initially) -->
                    <div class="bulk-results-section hidden" id="bulk-results-section">
                        <div class="results-header">
                            <h4>Creation Results</h4>
                            <div class="results-summary" id="bulk-results-summary">
                                <!-- Summary will be populated -->
                            </div>
                        </div>
                        
                        <div class="results-details" id="bulk-results-details">
                            <!-- Detailed results will be populated -->
                        </div>
                    </div>
                </div>

                <div class="modal-footer">
                    <div class="form-actions" id="bulk-form-actions">
                        <button type="button" class="btn btn-secondary" onclick="this.closest('.modal-overlay').remove()">
                            Cancel
                        </button>
                        <button type="button" class="btn btn-primary" id="create-bulk-interventions">
                            <i class="fas fa-plus"></i>
                            Create Interventions
                        </button>
                    </div>
                    
                    <div class="progress-actions hidden" id="bulk-progress-actions">
                        <button type="button" class="btn btn-secondary" id="cancel-bulk-creation" disabled>
                            <i class="fas fa-stop"></i>
                            Cancel
                        </button>
                    </div>
                    
                    <div class="results-actions hidden" id="bulk-results-actions">
                        <button type="button" class="btn btn-secondary" onclick="this.closest('.modal-overlay').remove()">
                            Close
                        </button>
                        <button type="button" class="btn btn-success" id="view-created-interventions">
                            <i class="fas fa-eye"></i>
                            View Interventions
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Load student information
        this.loadStudentPreviews(studentIds);

        // Bind form events
        this.bindFormEvents(studentIds);
        
        // Bind view interventions button
        this.bindViewInterventionsButton();
    }

    async loadStudentPreviews(studentIds) {
        const grid = document.getElementById('selected-students-grid');
        
        try {
            // For now, create simple previews based on IDs
            // In a real implementation, you'd fetch student details from the API
            const previews = studentIds.map(id => `
                <div class="student-preview" data-student-id="${id}">
                    <div class="student-preview-info">
                        <div class="student-preview-name">Student ${id}</div>
                        <div class="student-preview-id">ID: ${id}</div>
                    </div>
                    <div class="student-preview-status">
                        <i class="fas fa-clock text-muted"></i>
                    </div>
                </div>
            `).join('');

            grid.innerHTML = previews;
        } catch (error) {
            console.error('Error loading student previews:', error);
            grid.innerHTML = `
                <div class="error-message">
                    <i class="fas fa-exclamation-triangle"></i>
                    Could not load student information
                </div>
            `;
        }
    }

    bindFormEvents(studentIds) {
        const form = document.getElementById('bulk-intervention-form');
        const createBtn = document.getElementById('create-bulk-interventions');

        createBtn.addEventListener('click', async () => {
            if (this.isProcessing) return;

            const formData = new FormData(form);
            const interventionData = Object.fromEntries(formData);

            // Validate required fields
            if (!interventionData.intervention_type || !interventionData.title) {
                this.showNotification('Please fill in all required fields', 'error');
                return;
            }

            await this.createBulkInterventions(studentIds, interventionData);
        });
    }

    async createBulkInterventions(studentIds, interventionData) {
        this.isProcessing = true;
        
        // Show progress section
        this.showSection('bulk-progress-section');
        this.hideSection('bulk-form-section');
        this.showFooterActions('bulk-progress-actions');

        const progressFill = document.getElementById('bulk-progress-fill');
        const progressDetails = document.getElementById('bulk-progress-details');
        const progressCurrent = document.querySelector('.progress-current');

        try {
            // Prepare bulk data
            const bulkData = {
                student_ids: studentIds,
                intervention_type: interventionData.intervention_type,
                title: interventionData.title,
                description: interventionData.description || null,
                priority: interventionData.priority || 'medium',
                assigned_to: interventionData.assigned_to || null,
                due_date: interventionData.due_date || null
            };

            console.log('🚀 Creating bulk interventions:', bulkData);

            // Update progress
            progressDetails.innerHTML = '<div class="progress-message">Sending request to server...</div>';

            // Make API call
            const response = await fetch('/api/interventions/bulk/create', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('auth_token') || 'test-key'}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(bulkData)
            });

            if (!response.ok) {
                throw new Error(`Server error: ${response.status}`);
            }

            const result = await response.json();
            console.log('✅ Bulk creation result:', result);

            // Validate result structure
            if (!result || typeof result.successful === 'undefined') {
                throw new Error('Invalid API response structure');
            }

            // Update progress to completion
            progressFill.style.width = '100%';
            progressCurrent.textContent = result.successful;

            // Show results
            this.showResults(result);

        } catch (error) {
            console.error('❌ Error creating bulk interventions:', error);
            this.showError('Failed to create interventions: ' + error.message);
        } finally {
            this.isProcessing = false;
        }
    }

    showResults(result) {
        console.log('📊 showResults called with:', result);
        
        try {
            // Hide progress, show results
            this.hideSection('bulk-progress-section');
            this.showSection('bulk-results-section');
            this.showFooterActions('bulk-results-actions');

            const summaryDiv = document.getElementById('bulk-results-summary');
            const detailsDiv = document.getElementById('bulk-results-details');
            
            console.log('📋 Summary div:', summaryDiv);
            console.log('📋 Details div:', detailsDiv);

        // Summary
        const successRate = Math.round((result.successful / result.total_requested) * 100);
        summaryDiv.innerHTML = `
            <div class="results-stats">
                <div class="stat-item success">
                    <div class="stat-number">${result.successful}</div>
                    <div class="stat-label">Successful</div>
                </div>
                <div class="stat-item ${result.failed > 0 ? 'error' : 'muted'}">
                    <div class="stat-number">${result.failed}</div>
                    <div class="stat-label">Failed</div>
                </div>
                <div class="stat-item info">
                    <div class="stat-number">${successRate}%</div>
                    <div class="stat-label">Success Rate</div>
                </div>
                <div class="stat-item info">
                    <div class="stat-number">${result.execution_time}s</div>
                    <div class="stat-label">Time</div>
                </div>
            </div>
        `;

        // Detailed results
        if (result.results && result.results.length > 0) {
            const detailsHtml = result.results.map(item => `
                <div class="result-item ${item.success ? 'success' : 'error'}">
                    <div class="result-icon">
                        <i class="fas ${item.success ? 'fa-check' : 'fa-times'}"></i>
                    </div>
                    <div class="result-content">
                        <div class="result-title">
                            Student ID: ${item.id}
                            ${item.item_data?.student_name ? `(${item.item_data.student_name})` : ''}
                        </div>
                        ${item.success ? 
                            `<div class="result-message success">Intervention created successfully</div>` :
                            `<div class="result-message error">${item.error_message || 'Unknown error'}</div>`
                        }
                    </div>
                </div>
            `).join('');

            detailsDiv.innerHTML = `
                <div class="results-list">
                    ${detailsHtml}
                </div>
            `;
        }

        // Show success notification
        if (result.successful > 0) {
            this.showNotification(
                `Successfully created ${result.successful} intervention${result.successful !== 1 ? 's' : ''}!`,
                'success'
            );
        }

            // Update student previews with results
            console.log('📝 About to update student previews with:', result.results);
            this.updateStudentPreviews(result.results);
            
        } catch (error) {
            console.error('❌ Error in showResults:', error);
            this.showError('Failed to display results: ' + error.message);
        }
    }

    updateStudentPreviews(results) {
        if (!results || !Array.isArray(results)) {
            console.warn('Invalid results provided to updateStudentPreviews');
            return;
        }

        results.forEach(result => {
            // Look for student preview within the modal
            const modal = document.getElementById('bulk-intervention-modal');
            if (!modal) return;
            
            const preview = modal.querySelector(`[data-student-id="${result.id}"]`);
            if (preview) {
                const statusDiv = preview.querySelector('.student-preview-status');
                if (statusDiv) {
                    if (result.success) {
                        statusDiv.innerHTML = '<i class="fas fa-check text-success"></i>';
                        preview.classList.add('success');
                    } else {
                        statusDiv.innerHTML = '<i class="fas fa-times text-error"></i>';
                        preview.classList.add('error');
                    }
                } else {
                    console.warn(`Status div not found for student ${result.id}`);
                }
            } else {
                console.warn(`Preview not found for student ${result.id}`);
            }
        });
    }

    showError(message) {
        this.hideSection('bulk-progress-section');
        this.showSection('bulk-results-section');
        this.showFooterActions('bulk-results-actions');

        const summaryDiv = document.getElementById('bulk-results-summary');
        const detailsDiv = document.getElementById('bulk-results-details');

        summaryDiv.innerHTML = `
            <div class="error-summary">
                <i class="fas fa-exclamation-triangle"></i>
                <span>Operation Failed</span>
            </div>
        `;

        detailsDiv.innerHTML = `
            <div class="error-details">
                <div class="error-message">${message}</div>
                <div class="error-suggestion">
                    Please check your connection and try again. If the problem persists, contact support.
                </div>
            </div>
        `;
    }

    // Utility methods
    showSection(sectionId) {
        const section = document.getElementById(sectionId);
        if (section) {
            section.classList.remove('hidden');
        }
    }

    hideSection(sectionId) {
        const section = document.getElementById(sectionId);
        if (section) {
            section.classList.add('hidden');
        }
    }

    showFooterActions(actionsId) {
        // Hide all footer action groups
        document.querySelectorAll('.modal-footer > div').forEach(div => {
            div.classList.add('hidden');
        });
        
        // Show the specified actions
        const actions = document.getElementById(actionsId);
        if (actions) {
            actions.classList.remove('hidden');
        }
    }

    bindViewInterventionsButton() {
        // Store reference to current results for later use
        const viewBtn = document.getElementById('view-created-interventions');
        if (viewBtn) {
            viewBtn.addEventListener('click', () => {
                this.viewCreatedInterventions();
            });
        }
    }

    viewCreatedInterventions() {
        // Close the modal first
        const modal = document.getElementById('bulk-intervention-modal');
        if (modal) {
            modal.remove();
        }

        // Switch to the analyze tab to show interventions
        const analyzeTab = document.querySelector('[data-tab="analyze"]');
        if (analyzeTab && !analyzeTab.disabled) {
            analyzeTab.click();
            
            // Show a notification to guide the user
            this.showNotification(
                'Switched to AI Analysis tab where you can view individual student interventions by selecting students.',
                'info'
            );
        } else {
            // If analyze tab is not available, show guidance
            this.showNotification(
                'To view interventions, go to the AI Analysis tab and select individual students to see their intervention details.',
                'info'
            );
        }

        // If there's a way to highlight recent interventions, we could add that here
        // For now, guide the user to the appropriate section
    }

    showNotification(message, type = 'info') {
        // Use existing notification system if available
        if (window.notificationSystem) {
            window.notificationSystem.addNotification({
                title: type === 'success' ? 'Success' : type === 'error' ? 'Error' : 'Info',
                message: message,
                type: type,
                duration: 5000
            });
        } else {
            // Fallback alert
            alert(message);
        }
    }
}

// Global instance
window.bulkInterventionModal = new BulkInterventionModal();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = BulkInterventionModal;
}