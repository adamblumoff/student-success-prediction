/**
 * Bulk Assignment Modal Component
 * Handles bulk assignment of interventions to staff members
 */

class BulkAssignmentModal {
    constructor() {
        this.modal = null;
        this.selectedInterventions = [];
        this.isProcessing = false;
    }

    show(interventionIds) {
        if (this.isProcessing) return;
        
        this.selectedInterventions = interventionIds;
        console.log('👥 Opening bulk assignment modal for', interventionIds.length, 'interventions');
        
        this.createModal();
        this.bindEvents();
        this.loadInterventionDetails();
        this.loadStaffSuggestions();
    }

    createModal() {
        // Remove existing modal if any
        if (this.modal) {
            this.modal.remove();
        }

        this.modal = document.createElement('div');
        this.modal.className = 'modal-overlay';
        this.modal.id = 'bulk-assignment-modal';
        this.modal.innerHTML = `
            <div class="modal bulk-assignment-modal">
                <div class="modal-header">
                    <h3><i class="fas fa-user-plus"></i> Bulk Assignment to Staff</h3>
                    <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">&times;</button>
                </div>
                
                <div class="modal-body">
                    <!-- Selected Interventions Preview -->
                    <div class="selected-interventions-preview">
                        <h4><i class="fas fa-list"></i> Selected Interventions (<span id="intervention-count">${this.selectedInterventions.length}</span>)</h4>
                        <div class="interventions-grid" id="interventions-preview">
                            <div class="loading-interventions">
                                <i class="fas fa-spinner fa-spin"></i>
                                Loading intervention details...
                            </div>
                        </div>
                    </div>
                    
                    <!-- Assignment Form -->
                    <form class="assignment-form" id="bulk-assignment-form">
                        <div class="form-section">
                            <h4><i class="fas fa-user-cog"></i> Staff Assignment</h4>
                            
                            <div class="form-row">
                                <div class="form-group">
                                    <label for="assigned-to">Assign To <span class="required">*</span></label>
                                    <input type="text" id="assigned-to" name="assigned_to" 
                                           placeholder="Enter staff member name..." 
                                           autocomplete="off" required>
                                    <div class="staff-suggestions" id="staff-suggestions"></div>
                                </div>
                                
                                <div class="form-group">
                                    <label for="assignment-priority">Priority (optional)</label>
                                    <select id="assignment-priority" name="priority">
                                        <option value="">Keep existing priority</option>
                                        <option value="low">Low</option>
                                        <option value="medium">Medium</option>
                                        <option value="high">High</option>
                                        <option value="critical">Critical</option>
                                    </select>
                                </div>
                            </div>
                            
                            <div class="form-row">
                                <div class="form-group">
                                    <label for="assignment-due-date">Due Date (optional)</label>
                                    <input type="date" id="assignment-due-date" name="due_date">
                                </div>
                                
                                <div class="form-group">
                                    <label for="assignment-status">Update Status (optional)</label>
                                    <select id="assignment-status" name="status">
                                        <option value="">Keep current status</option>
                                        <option value="pending">Pending</option>
                                        <option value="in_progress">In Progress</option>
                                    </select>
                                </div>
                            </div>
                            
                            <div class="form-group">
                                <label for="assignment-notes">Assignment Notes</label>
                                <textarea id="assignment-notes" name="outcome_notes" rows="3"
                                          placeholder="Notes about this bulk assignment..."></textarea>
                            </div>
                            
                            <div class="assignment-options">
                                <div class="option-group">
                                    <label class="checkbox-label">
                                        <input type="checkbox" id="notify-assignee" checked>
                                        <span class="checkmark"></span>
                                        Send notification to assignee (if email available)
                                    </label>
                                </div>
                                
                                <div class="option-group">
                                    <label class="checkbox-label">
                                        <input type="checkbox" id="update-existing">
                                        <span class="checkmark"></span>
                                        Update interventions already assigned to other staff
                                    </label>
                                </div>
                            </div>
                        </div>
                    </form>
                    
                    <!-- Progress Section (hidden initially) -->
                    <div class="bulk-progress-section" id="progress-section" style="display: none;">
                        <div class="progress-header">
                            <h4>Assigning Interventions...</h4>
                            <div class="progress-stats">
                                <span id="progress-completed">0</span> of <span id="progress-total">${this.selectedInterventions.length}</span> assigned
                            </div>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill" id="progress-fill"></div>
                        </div>
                        <div class="progress-details">
                            <div class="progress-message" id="progress-message">Preparing assignment...</div>
                        </div>
                    </div>
                    
                    <!-- Results Section (hidden initially) -->
                    <div class="bulk-results-section" id="results-section" style="display: none;">
                        <div class="results-header">
                            <h4>Assignment Results</h4>
                        </div>
                        <div class="results-stats" id="results-stats">
                            <!-- Results stats will be populated here -->
                        </div>
                        <div class="results-list" id="results-list">
                            <!-- Detailed results will be shown here -->
                        </div>
                    </div>
                </div>
                
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" id="cancel-bulk-assignment">
                        <i class="fas fa-times"></i>
                        Cancel
                    </button>
                    <button type="submit" class="btn btn-primary" id="submit-bulk-assignment" form="bulk-assignment-form">
                        <i class="fas fa-user-plus"></i>
                        Assign <span id="submit-count">${this.selectedInterventions.length}</span> Interventions
                    </button>
                    <button type="button" class="btn btn-success" id="view-assigned-interventions" style="display: none;">
                        <i class="fas fa-eye"></i>
                        View Assigned Interventions
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(this.modal);
    }

    bindEvents() {
        if (!this.modal) return;

        // Form submission
        const form = this.modal.querySelector('#bulk-assignment-form');
        form.addEventListener('submit', (e) => this.handleSubmit(e));

        // Cancel button
        const cancelBtn = this.modal.querySelector('#cancel-bulk-assignment');
        cancelBtn.addEventListener('click', () => this.close());

        // Staff suggestions
        const assignedToInput = this.modal.querySelector('#assigned-to');
        assignedToInput.addEventListener('input', () => this.handleStaffInput());
        assignedToInput.addEventListener('focus', () => this.showStaffSuggestions());
        assignedToInput.addEventListener('blur', () => {
            // Delay hiding to allow clicks on suggestions
            setTimeout(() => this.hideStaffSuggestions(), 150);
        });

        // View assigned interventions
        const viewBtn = this.modal.querySelector('#view-assigned-interventions');
        viewBtn.addEventListener('click', () => this.viewAssignedInterventions());

        // Close on background click
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.close();
            }
        });
    }

    async loadInterventionDetails() {
        const container = this.modal.querySelector('#interventions-preview');
        
        try {
            // Load intervention details for preview
            const interventionDetails = await Promise.all(
                this.selectedInterventions.map(id => this.getInterventionDetails(id))
            );

            const validInterventions = interventionDetails.filter(Boolean);
            
            if (validInterventions.length === 0) {
                container.innerHTML = `
                    <div class="error-message">
                        <i class="fas fa-exclamation-circle"></i>
                        No valid interventions found
                    </div>
                `;
                return;
            }

            container.innerHTML = validInterventions.map(intervention => `
                <div class="intervention-preview">
                    <div class="intervention-preview-info">
                        <div class="intervention-preview-title">${intervention.title}</div>
                        <div class="intervention-preview-meta">
                            ${intervention.intervention_type.replace('_', ' ')} • 
                            Priority: ${intervention.priority} • 
                            Current assignee: ${intervention.assigned_to || 'Unassigned'}
                        </div>
                    </div>
                    <div class="intervention-preview-status">
                        <span class="status-badge ${intervention.status}">${intervention.status.replace('_', ' ')}</span>
                    </div>
                </div>
            `).join('');

        } catch (error) {
            console.error('Error loading intervention details:', error);
            container.innerHTML = `
                <div class="error-message">
                    <i class="fas fa-exclamation-circle"></i>
                    Error loading intervention details
                </div>
            `;
        }
    }

    async loadStaffSuggestions() {
        try {
            // Get staff suggestions from existing interventions
            const token = localStorage.getItem('api_key') || 'dev-key-change-me';
            const response = await fetch('/api/interventions/all?limit=100', {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const data = await response.json();
                const interventions = data.interventions || [];
                
                // Extract unique staff members
                const staffMembers = [...new Set(
                    interventions
                        .map(i => i.assigned_to)
                        .filter(Boolean)
                        .map(name => name.trim())
                )].sort();

                this.staffSuggestions = staffMembers;
            } else {
                this.staffSuggestions = [];
            }
        } catch (error) {
            console.error('Error loading staff suggestions:', error);
            this.staffSuggestions = [];
        }
    }

    handleStaffInput() {
        const input = this.modal.querySelector('#assigned-to');
        const query = input.value.toLowerCase().trim();
        
        if (query.length === 0) {
            this.showStaffSuggestions();
            return;
        }

        const filteredSuggestions = this.staffSuggestions.filter(staff => 
            staff.toLowerCase().includes(query)
        );

        this.displayStaffSuggestions(filteredSuggestions);
    }

    showStaffSuggestions() {
        this.displayStaffSuggestions(this.staffSuggestions || []);
    }

    displayStaffSuggestions(suggestions) {
        const container = this.modal.querySelector('#staff-suggestions');
        
        if (suggestions.length === 0) {
            container.innerHTML = '';
            container.style.display = 'none';
            return;
        }

        container.innerHTML = suggestions.map(staff => `
            <div class="staff-suggestion" onclick="window.bulkAssignmentModal.selectStaff('${staff}')">
                <i class="fas fa-user"></i>
                <span>${staff}</span>
            </div>
        `).join('');
        
        container.style.display = 'block';
    }

    selectStaff(staffName) {
        const input = this.modal.querySelector('#assigned-to');
        input.value = staffName;
        this.hideStaffSuggestions();
        input.focus();
    }

    hideStaffSuggestions() {
        const container = this.modal.querySelector('#staff-suggestions');
        container.style.display = 'none';
    }

    async getInterventionDetails(interventionId) {
        try {
            const token = localStorage.getItem('api_key') || 'dev-key-change-me';
            const response = await fetch(`/api/interventions/${interventionId}`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                return await response.json();
            }
            return null;
        } catch (error) {
            console.error(`Error fetching intervention ${interventionId}:`, error);
            return null;
        }
    }

    async handleSubmit(event) {
        event.preventDefault();
        
        if (this.isProcessing) return;
        
        const formData = new FormData(event.target);
        
        // Validate required fields
        const assignedTo = formData.get('assigned_to')?.trim();
        if (!assignedTo) {
            this.showNotification('Please enter a staff member name', 'error');
            return;
        }

        this.isProcessing = true;
        
        // Prepare update data
        const updateData = {
            intervention_ids: this.selectedInterventions,
            assigned_to: assignedTo,
            priority: formData.get('priority') || null,
            status: formData.get('status') || null,
            outcome_notes: formData.get('outcome_notes') || null
        };

        // Handle due date
        const dueDate = formData.get('due_date');
        if (dueDate) {
            updateData.due_date = dueDate;
        }

        // Remove empty values
        Object.keys(updateData).forEach(key => {
            if (updateData[key] === null || updateData[key] === '') {
                delete updateData[key];
            }
        });

        await this.performBulkAssignment(updateData);
    }

    async performBulkAssignment(updateData) {
        // Show progress section
        this.showProgressSection();
        
        try {
            const token = localStorage.getItem('api_key') || 'dev-key-change-me';
            const response = await fetch('/api/interventions/bulk/update', {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(updateData)
            });

            const result = await response.json();

            if (response.ok) {
                this.showResults(result);
                this.showNotification(`Successfully assigned ${result.successful} of ${result.total_requested} interventions`, 'success');
                
                // Trigger real-time refresh of interventions after successful assignment
                if (typeof safeRefreshInterventions === 'function') {
                    setTimeout(() => safeRefreshInterventions(), 1000); // Brief delay to ensure UI updates
                }
            } else {
                throw new Error(result.detail || 'Failed to assign interventions');
            }

        } catch (error) {
            console.error('Error in bulk assignment:', error);
            this.showError(error.message);
            this.showNotification('Error assigning interventions', 'error');
        } finally {
            this.isProcessing = false;
        }
    }

    showProgressSection() {
        // Hide form section and show progress
        this.modal.querySelector('.assignment-form').style.display = 'none';
        this.modal.querySelector('#progress-section').style.display = 'block';
        this.modal.querySelector('#submit-bulk-assignment').style.display = 'none';
        this.modal.querySelector('#cancel-bulk-assignment').textContent = 'Close';

        // Simulate progress (since API is atomic)
        this.animateProgress();
    }

    animateProgress() {
        const progressFill = this.modal.querySelector('#progress-fill');
        const progressMessage = this.modal.querySelector('#progress-message');
        const progressCompleted = this.modal.querySelector('#progress-completed');
        
        let progress = 0;
        const total = this.selectedInterventions.length;
        
        const interval = setInterval(() => {
            progress += Math.random() * 25;
            if (progress > 100) progress = 100;
            
            progressFill.style.width = `${progress}%`;
            const completed = Math.floor((progress / 100) * total);
            progressCompleted.textContent = completed;
            
            if (progress < 30) {
                progressMessage.textContent = 'Validating staff assignments...';
            } else if (progress < 70) {
                progressMessage.textContent = 'Updating intervention assignments...';
            } else if (progress < 100) {
                progressMessage.textContent = 'Finalizing assignments...';
            } else {
                progressMessage.textContent = 'Assignment complete!';
                clearInterval(interval);
            }
            
            if (progress >= 100) {
                clearInterval(interval);
            }
        }, 120);
    }

    showResults(result) {
        // Hide progress and show results
        this.modal.querySelector('#progress-section').style.display = 'none';
        this.modal.querySelector('#results-section').style.display = 'block';
        this.modal.querySelector('#view-assigned-interventions').style.display = 'inline-flex';

        // Populate results stats
        const statsContainer = this.modal.querySelector('#results-stats');
        statsContainer.innerHTML = `
            <div class="stat-item success">
                <div class="stat-number">${result.successful}</div>
                <div class="stat-label">Assigned</div>
            </div>
            <div class="stat-item error">
                <div class="stat-number">${result.failed}</div>
                <div class="stat-label">Failed</div>
            </div>
            <div class="stat-item info">
                <div class="stat-number">${result.total_requested}</div>
                <div class="stat-label">Total</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">${result.execution_time}s</div>
                <div class="stat-label">Time</div>
            </div>
        `;

        // Populate detailed results
        const resultsContainer = this.modal.querySelector('#results-list');
        resultsContainer.innerHTML = result.results.map(item => `
            <div class="result-item ${item.success ? 'success' : 'error'}">
                <div class="result-icon">
                    <i class="fas ${item.success ? 'fa-check' : 'fa-times'}"></i>
                </div>
                <div class="result-content">
                    <div class="result-title">
                        Intervention ID: ${item.id}
                        ${item.item_data?.intervention_title ? ` - ${item.item_data.intervention_title}` : ''}
                    </div>
                    <div class="result-message ${item.success ? 'success' : 'error'}">
                        ${item.success ? 
                            `Successfully assigned${item.item_data?.updated_fields ? ` (${item.item_data.updated_fields.join(', ')})` : ''}` : 
                            item.error_message
                        }
                    </div>
                </div>
            </div>
        `).join('');
    }

    showError(message) {
        this.modal.querySelector('#progress-section').style.display = 'none';
        this.modal.querySelector('#results-section').style.display = 'block';
        
        const resultsContainer = this.modal.querySelector('#results-list');
        resultsContainer.innerHTML = `
            <div class="error-summary">
                <i class="fas fa-exclamation-circle"></i>
                Bulk assignment failed: ${message}
            </div>
        `;
    }

    viewAssignedInterventions() {
        this.close();
        
        // Switch to analyze tab and refresh interventions
        const analyzeTab = document.querySelector('[data-tab="analyze"]');
        if (analyzeTab && !analyzeTab.disabled) {
            analyzeTab.click();
        }
        
        // Clear selections and exit selection mode
        if (window.selectionManager) {
            window.selectionManager.clearAllSelections();
        }
        
        this.showNotification('Switched to AI Analysis tab. Interventions have been assigned.', 'info');
    }

    close() {
        if (this.modal) {
            this.modal.remove();
            this.modal = null;
        }
        this.selectedInterventions = [];
        this.isProcessing = false;
    }

    showNotification(message, type = 'info') {
        if (window.notificationSystem) {
            if (type === 'success') {
                window.notificationSystem.success(message);
            } else if (type === 'error') {
                window.notificationSystem.error(message);
            } else {
                window.notificationSystem.info(message);
            }
        } else {
            alert(message);
        }
    }
}

// Global instance
window.bulkAssignmentModal = new BulkAssignmentModal();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = BulkAssignmentModal;
}