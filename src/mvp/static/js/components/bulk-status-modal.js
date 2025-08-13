/**
 * Bulk Status Update Modal Component
 * Handles bulk updates of intervention statuses
 */

class BulkStatusModal {
    constructor() {
        this.modal = null;
        this.selectedInterventions = [];
        this.isProcessing = false;
    }

    show(interventionIds) {
        if (this.isProcessing) return;
        
        this.selectedInterventions = interventionIds;
        console.log('🔄 Opening bulk status update modal for', interventionIds.length, 'interventions');
        
        this.createModal();
        this.bindEvents();
        this.loadInterventionDetails();
    }

    createModal() {
        // Remove existing modal if any
        if (this.modal) {
            this.modal.remove();
        }

        this.modal = document.createElement('div');
        this.modal.className = 'modal-overlay';
        this.modal.id = 'bulk-status-modal';
        this.modal.innerHTML = `
            <div class="modal bulk-status-modal">
                <div class="modal-header">
                    <h3><i class="fas fa-edit"></i> Bulk Status Update</h3>
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
                    
                    <!-- Status Update Form -->
                    <form class="status-form" id="bulk-status-form">
                        <div class="form-section">
                            <h4><i class="fas fa-cog"></i> Status Update</h4>
                            
                            <div class="form-row">
                                <div class="form-group">
                                    <label for="bulk-status">New Status <span class="required">*</span></label>
                                    <select id="bulk-status" name="status" required>
                                        <option value="">Select new status...</option>
                                        <option value="pending">Pending</option>
                                        <option value="in_progress">In Progress</option>
                                        <option value="completed">Completed</option>
                                        <option value="cancelled">Cancelled</option>
                                    </select>
                                </div>
                                
                                <div class="form-group">
                                    <label for="bulk-priority">Priority (optional)</label>
                                    <select id="bulk-priority" name="priority">
                                        <option value="">Keep existing priority</option>
                                        <option value="low">Low</option>
                                        <option value="medium">Medium</option>
                                        <option value="high">High</option>
                                        <option value="critical">Critical</option>
                                    </select>
                                </div>
                            </div>
                            
                            <div class="form-group" id="outcome-group" style="display: none;">
                                <label for="bulk-outcome">Outcome (for completed interventions)</label>
                                <select id="bulk-outcome" name="outcome">
                                    <option value="">Select outcome...</option>
                                    <option value="successful">Successful</option>
                                    <option value="partially_successful">Partially Successful</option>
                                    <option value="unsuccessful">Unsuccessful</option>
                                    <option value="ongoing">Ongoing</option>
                                </select>
                            </div>
                            
                            <div class="form-group">
                                <label for="bulk-assigned-to">Assigned To (optional)</label>
                                <input type="text" id="bulk-assigned-to" name="assigned_to" 
                                       placeholder="Staff member name (leave blank to keep existing)">
                            </div>
                            
                            <div class="form-group">
                                <label for="bulk-notes">Update Notes</label>
                                <textarea id="bulk-notes" name="outcome_notes" rows="3"
                                          placeholder="Notes about this bulk status update..."></textarea>
                            </div>
                        </div>
                    </form>
                    
                    <!-- Progress Section (hidden initially) -->
                    <div class="bulk-progress-section" id="progress-section" style="display: none;">
                        <div class="progress-header">
                            <h4>Updating Interventions...</h4>
                            <div class="progress-stats">
                                <span id="progress-completed">0</span> of <span id="progress-total">${this.selectedInterventions.length}</span> completed
                            </div>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill" id="progress-fill"></div>
                        </div>
                        <div class="progress-details">
                            <div class="progress-message" id="progress-message">Preparing update...</div>
                        </div>
                    </div>
                    
                    <!-- Results Section (hidden initially) -->
                    <div class="bulk-results-section" id="results-section" style="display: none;">
                        <div class="results-header">
                            <h4>Update Results</h4>
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
                    <button type="button" class="btn btn-secondary" id="cancel-bulk-status">
                        <i class="fas fa-times"></i>
                        Cancel
                    </button>
                    <button type="submit" class="btn btn-warning" id="submit-bulk-status" form="bulk-status-form">
                        <i class="fas fa-edit"></i>
                        Update <span id="submit-count">${this.selectedInterventions.length}</span> Interventions
                    </button>
                    <button type="button" class="btn btn-success" id="view-updated-interventions" style="display: none;">
                        <i class="fas fa-eye"></i>
                        View Updated Interventions
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(this.modal);
    }

    bindEvents() {
        if (!this.modal) return;

        // Form submission
        const form = this.modal.querySelector('#bulk-status-form');
        form.addEventListener('submit', (e) => this.handleSubmit(e));

        // Cancel button
        const cancelBtn = this.modal.querySelector('#cancel-bulk-status');
        cancelBtn.addEventListener('click', () => this.close());

        // Status change handler
        const statusSelect = this.modal.querySelector('#bulk-status');
        statusSelect.addEventListener('change', () => this.handleStatusChange());

        // View updated interventions
        const viewBtn = this.modal.querySelector('#view-updated-interventions');
        viewBtn.addEventListener('click', () => this.viewUpdatedInterventions());

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
                            Status: ${intervention.status.replace('_', ' ')} • 
                            Priority: ${intervention.priority}
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

    async getInterventionDetails(interventionId) {
        try {
            const token = localStorage.getItem('auth_token');
            const response = await fetch(`/api/interventions/${interventionId}`, {
                headers: {
                    'Authorization': token ? `Bearer ${token}` : '',
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

    handleStatusChange() {
        const statusSelect = this.modal.querySelector('#bulk-status');
        const outcomeGroup = this.modal.querySelector('#outcome-group');
        
        if (statusSelect.value === 'completed') {
            outcomeGroup.style.display = 'block';
        } else {
            outcomeGroup.style.display = 'none';
        }
    }

    async handleSubmit(event) {
        event.preventDefault();
        
        if (this.isProcessing) return;
        
        const formData = new FormData(event.target);
        
        // Validate required fields
        if (!formData.get('status')) {
            this.showNotification('Please select a status', 'error');
            return;
        }

        // Show confirmation for cancelled status
        if (formData.get('status') === 'cancelled') {
            const confirmed = await this.showCancellationConfirmation();
            if (!confirmed) return;
        }

        this.isProcessing = true;
        
        // Prepare update data
        const updateData = {
            intervention_ids: this.selectedInterventions,
            status: formData.get('status'),
            outcome: formData.get('outcome') || null,
            outcome_notes: formData.get('outcome_notes') || null,
            assigned_to: formData.get('assigned_to') || null,
            priority: formData.get('priority') || null
        };

        // Remove empty values
        Object.keys(updateData).forEach(key => {
            if (updateData[key] === null || updateData[key] === '') {
                delete updateData[key];
            }
        });

        await this.performBulkUpdate(updateData);
    }

    async performBulkUpdate(updateData) {
        // Show progress section
        this.showProgressSection();
        
        try {
            const token = localStorage.getItem('auth_token');
            const response = await fetch('/api/interventions/bulk/update', {
                method: 'PUT',
                headers: {
                    'Authorization': token ? `Bearer ${token}` : '',
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(updateData)
            });

            const result = await response.json();

            if (response.ok) {
                this.showResults(result);
                this.showNotification(`Successfully updated ${result.successful} of ${result.total_requested} interventions`, 'success');
                
                // Trigger real-time refresh of interventions after successful update
                if (typeof safeRefreshInterventions === 'function') {
                    setTimeout(() => safeRefreshInterventions(), 1000); // Brief delay to ensure UI updates
                }
            } else {
                throw new Error(result.detail || 'Failed to update interventions');
            }

        } catch (error) {
            console.error('Error in bulk update:', error);
            this.showError(error.message);
            this.showNotification('Error updating interventions', 'error');
        } finally {
            this.isProcessing = false;
        }
    }

    showProgressSection() {
        // Hide form section and show progress
        this.modal.querySelector('.status-form').style.display = 'none';
        this.modal.querySelector('#progress-section').style.display = 'block';
        this.modal.querySelector('#submit-bulk-status').style.display = 'none';
        this.modal.querySelector('#cancel-bulk-status').textContent = 'Close';

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
            progress += Math.random() * 20;
            if (progress > 100) progress = 100;
            
            progressFill.style.width = `${progress}%`;
            const completed = Math.floor((progress / 100) * total);
            progressCompleted.textContent = completed;
            
            if (progress < 30) {
                progressMessage.textContent = 'Validating interventions...';
            } else if (progress < 70) {
                progressMessage.textContent = 'Updating intervention statuses...';
            } else if (progress < 100) {
                progressMessage.textContent = 'Finalizing changes...';
            } else {
                progressMessage.textContent = 'Update complete!';
                clearInterval(interval);
            }
            
            if (progress >= 100) {
                clearInterval(interval);
            }
        }, 150);
    }

    showResults(result) {
        // Hide progress and show results
        this.modal.querySelector('#progress-section').style.display = 'none';
        this.modal.querySelector('#results-section').style.display = 'block';
        this.modal.querySelector('#view-updated-interventions').style.display = 'inline-flex';

        // Populate results stats
        const statsContainer = this.modal.querySelector('#results-stats');
        statsContainer.innerHTML = `
            <div class="stat-item success">
                <div class="stat-number">${result.successful}</div>
                <div class="stat-label">Updated</div>
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
                            `Updated successfully${item.item_data?.updated_fields ? ` (${item.item_data.updated_fields.join(', ')})` : ''}` : 
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
                Bulk update failed: ${message}
            </div>
        `;
    }

    async showCancellationConfirmation() {
        return new Promise((resolve) => {
            const confirmModal = document.createElement('div');
            confirmModal.className = 'modal-overlay';
            confirmModal.innerHTML = `
                <div class="modal confirmation-modal">
                    <div class="modal-header">
                        <h3><i class="fas fa-exclamation-triangle text-warning"></i> Confirm Bulk Cancellation</h3>
                        <button class="modal-close">&times;</button>
                    </div>
                    <div class="modal-body">
                        <div class="warning-message">
                            <p><strong>⚠️ Warning: This will cancel ${this.selectedInterventions.length} interventions!</strong></p>
                            <p>Setting interventions to "cancelled" status will permanently delete them from the database.</p>
                            <p>This action cannot be undone. Are you sure you want to proceed?</p>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" id="cancel-cancellation">
                            <i class="fas fa-times"></i>
                            Keep Interventions
                        </button>
                        <button type="button" class="btn btn-danger" id="confirm-cancellation">
                            <i class="fas fa-trash"></i>
                            Yes, Cancel All Interventions
                        </button>
                    </div>
                </div>
            `;
            
            document.body.appendChild(confirmModal);
            
            const cancelBtn = confirmModal.querySelector('#cancel-cancellation');
            const confirmBtn = confirmModal.querySelector('#confirm-cancellation');
            const closeBtn = confirmModal.querySelector('.modal-close');
            
            const cleanup = (result) => {
                confirmModal.remove();
                resolve(result);
            };
            
            cancelBtn.addEventListener('click', () => cleanup(false));
            confirmBtn.addEventListener('click', () => cleanup(true));
            closeBtn.addEventListener('click', () => cleanup(false));
            
            confirmModal.addEventListener('click', (e) => {
                if (e.target === confirmModal) cleanup(false);
            });
        });
    }

    viewUpdatedInterventions() {
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
        
        // Trigger real-time refresh of interventions
        if (typeof safeRefreshInterventions === 'function') {
            safeRefreshInterventions();
        }
        
        this.showNotification('Switched to AI Analysis tab. Interventions have been updated.', 'info');
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
window.bulkStatusModal = new BulkStatusModal();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = BulkStatusModal;
}