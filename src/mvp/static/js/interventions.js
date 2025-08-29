/**
 * Interventions Management
 * Global functions for creating and managing student interventions
 */

// Helper function to load interventions for a specific container
async function loadInterventionsForContainer(studentId, container) {
    try {
        const token = localStorage.getItem('auth_token');
        const response = await fetch(`/api/interventions/student/${studentId}`, {
            headers: {
                'Authorization': token ? `Bearer ${token}` : '',
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            const interventions = await response.json();
            if (interventions.length === 0) {
                container.innerHTML = '<p class="text-muted">No interventions created yet</p>';
            } else {
                container.innerHTML = interventions.map(intervention => renderInterventionCard(intervention)).join('');
            }
        } else {
            container.innerHTML = '<p class="text-muted">No interventions found</p>';
        }
    } catch (error) {
        console.error('Error loading interventions:', error);
        container.innerHTML = '<p class="text-danger">Error loading interventions</p>';
    }
}

// Helper function to render intervention card (simplified version)
function renderInterventionCard(intervention) {
    const priorityColor = {
        'low': 'var(--success-500)',
        'medium': 'var(--warning-500)', 
        'high': 'var(--danger-500)',
        'critical': 'var(--danger-700)'
    }[intervention.priority] || 'var(--neutral-500)';
    
    const statusColor = {
        'pending': 'var(--warning-500)',
        'in_progress': 'var(--primary-500)',
        'completed': 'var(--success-500)',
        'cancelled': 'var(--neutral-500)'
    }[intervention.status] || 'var(--neutral-500)';
    
    return `
        <div class="intervention-card" data-intervention-id="${intervention.id}">
            <div class="intervention-header">
                <h5 class="intervention-title">${intervention.title}</h5>
                <div class="intervention-badges">
                    <span class="badge" style="background-color: ${priorityColor}">${intervention.priority}</span>
                    <span class="badge" style="background-color: ${statusColor}">${intervention.status.replace('_', ' ')}</span>
                </div>
            </div>
            <div class="intervention-body">
                <p class="intervention-type"><strong>${intervention.intervention_type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}</strong></p>
                ${intervention.description ? `<p class="intervention-description">${intervention.description}</p>` : ''}
                ${intervention.assigned_to ? `<p class="intervention-assigned">Assigned to: ${intervention.assigned_to}</p>` : ''}
            </div>
            <div class="intervention-actions">
                <button class="btn btn-sm btn-outline" onclick="updateInterventionStatus(${intervention.id}, '${intervention.status}')">
                    <i class="fas fa-edit"></i>
                    Update Status
                </button>
                <button class="btn btn-sm btn-outline" onclick="viewInterventionDetails(${intervention.id})">
                    <i class="fas fa-eye"></i>
                    Details
                </button>
            </div>
        </div>
    `;
}

// Helper function to safely refresh interventions with enhanced real-time updates
function safeRefreshInterventions(studentId) {
    try {
        console.log('🔄 Refreshing interventions in real-time...');
        
        // Method 1: Use analysis component if available
        const currentStudent = window.appState?.getState?.()?.selectedStudent;
        if (currentStudent && window.analysisComponent) {
            console.log('📊 Refreshing via analysis component');
            window.analysisComponent.loadStudentInterventions(currentStudent);
        }
        
        // Method 2: Refresh specific container if studentId provided
        if (studentId) {
            const listContainer = document.getElementById(`interventions-list-${studentId}`);
            if (listContainer) {
                console.log(`📋 Refreshing interventions list for student ${studentId}`);
                loadInterventionsForContainer(studentId, listContainer);
            }
        }
        
        // Method 3: Refresh all visible intervention containers
        const allInterventionContainers = document.querySelectorAll('[id^="interventions-list-"]');
        allInterventionContainers.forEach(container => {
            const containerStudentId = container.id.replace('interventions-list-', '');
            if (containerStudentId && containerStudentId !== studentId) {
                console.log(`📋 Refreshing additional container for student ${containerStudentId}`);
                loadInterventionsForContainer(containerStudentId, container);
            }
        });
        
        // Method 4: Refresh any bulk selection checkboxes if in selection mode
        if (window.selectionManager && window.selectionManager.isInSelectionMode()) {
            console.log('🎯 Refreshing selection mode checkboxes');
            setTimeout(() => {
                window.selectionManager.addCheckboxesToCards();
            }, 500); // Give time for new intervention cards to load
        }
        
        // Method 5: Trigger a global refresh event for other components
        window.dispatchEvent(new CustomEvent('interventionsUpdated', {
            detail: { studentId, timestamp: Date.now() }
        }));
        
        console.log('✅ Real-time intervention refresh completed');
    } catch (refreshError) {
        console.log('⚠️ Could not refresh interventions list:', refreshError);
        // Still successful operation, just couldn't refresh UI
    }
}

// Global intervention functions
async function createIntervention(studentId) {
    console.log('Creating intervention for student:', studentId);
    
    // Show intervention creation modal
    showInterventionModal(studentId);
}

async function updateInterventionStatus(interventionId, currentStatus) {
    console.log('Updating intervention status:', interventionId, currentStatus);
    
    // Show status update modal
    showStatusUpdateModal(interventionId, currentStatus);
}

async function viewInterventionDetails(interventionId) {
    console.log('Viewing intervention details:', interventionId);
    
    try {
        // Fetch intervention details from API
        const token = localStorage.getItem('auth_token');
        const response = await fetch(`/api/interventions/${interventionId}`, {
            headers: {
                'Authorization': token ? `Bearer ${token}` : '',
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error(`Failed to fetch intervention details: ${response.status}`);
        }
        
        const intervention = await response.json();
        showInterventionDetailsModal(intervention);
        
    } catch (error) {
        console.error('Error fetching intervention details:', error);
        showNotification('Error loading intervention details', 'error');
    }
}

function showInterventionModal(studentId) {
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal intervention-modal">
            <div class="modal-header">
                <h3><i class="fas fa-plus-circle"></i> Create New Intervention</h3>
                <button class="modal-close" onclick="closeModal(this)">&times;</button>
            </div>
            <form id="intervention-form" onsubmit="handleInterventionSubmit(event, '${studentId}')">
                <div class="modal-body">
                    <div class="form-group">
                        <label for="intervention-type">Intervention Type <span class="required">*</span></label>
                        <select id="intervention-type" name="intervention_type" required>
                            <option value="">Select Type...</option>
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
                        <label for="intervention-title">Title <span class="required">*</span></label>
                        <input type="text" id="intervention-title" name="title" required 
                               placeholder="Brief title for this intervention">
                    </div>
                    
                    <div class="form-group">
                        <label for="intervention-description">Description</label>
                        <textarea id="intervention-description" name="description" rows="3"
                                  placeholder="Detailed description of the intervention plan"></textarea>
                    </div>
                    
                    <div class="form-row">
                        <div class="form-group">
                            <label for="intervention-priority">Priority</label>
                            <select id="intervention-priority" name="priority">
                                <option value="low">Low</option>
                                <option value="medium" selected>Medium</option>
                                <option value="high">High</option>
                                <option value="critical">Critical</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label for="intervention-assigned">Assigned To</label>
                            <input type="text" id="intervention-assigned" name="assigned_to" 
                                   placeholder="Staff member name">
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label for="intervention-due">Due Date</label>
                        <input type="date" id="intervention-due" name="due_date">
                    </div>
                </div>
                
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" onclick="closeModal(this)">Cancel</button>
                    <button type="submit" class="btn btn-success">
                        <i class="fas fa-plus"></i>
                        Create Intervention
                    </button>
                </div>
            </form>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Focus first input
    setTimeout(() => {
        const firstInput = modal.querySelector('#intervention-type');
        if (firstInput) firstInput.focus();
    }, 100);
}

function showStatusUpdateModal(interventionId, currentStatus) {
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal status-modal">
            <div class="modal-header">
                <h3><i class="fas fa-edit"></i> Update Intervention Status</h3>
                <button class="modal-close" onclick="closeModal(this)">&times;</button>
            </div>
            <form id="status-form" onsubmit="handleStatusUpdate(event, '${interventionId}')">
                <div class="modal-body">
                    <div class="form-group">
                        <label for="status-select">Status <span class="required">*</span></label>
                        <select id="status-select" name="status" required>
                            <option value="pending" ${currentStatus === 'pending' ? 'selected' : ''}>Pending</option>
                            <option value="in_progress" ${currentStatus === 'in_progress' ? 'selected' : ''}>In Progress</option>
                            <option value="completed" ${currentStatus === 'completed' ? 'selected' : ''}>Completed</option>
                            <option value="cancelled" ${currentStatus === 'cancelled' ? 'selected' : ''}>Cancelled</option>
                        </select>
                    </div>
                    
                    <div class="form-group" id="outcome-group" style="display: none;">
                        <label for="outcome-select">Outcome</label>
                        <select id="outcome-select" name="outcome">
                            <option value="">Select outcome...</option>
                            <option value="successful">Successful</option>
                            <option value="partially_successful">Partially Successful</option>
                            <option value="unsuccessful">Unsuccessful</option>
                            <option value="ongoing">Ongoing</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label for="status-notes">Notes</label>
                        <textarea id="status-notes" name="outcome_notes" rows="3"
                                  placeholder="Additional notes about this status update"></textarea>
                    </div>
                </div>
                
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" onclick="closeModal(this)">Cancel</button>
                    <button type="submit" class="btn btn-primary">
                        <i class="fas fa-save"></i>
                        Update Status
                    </button>
                    <button type="button" id="delete-completed-btn" class="btn btn-danger" style="display: none;" 
                            onclick="handleCompletedInterventionDeletion('${interventionId}')">
                        <i class="fas fa-trash"></i>
                        Delete Completed
                    </button>
                </div>
            </form>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Show outcome field and delete button if status is completed
    const statusSelect = modal.querySelector('#status-select');
    const outcomeGroup = modal.querySelector('#outcome-group');
    const deleteBtn = modal.querySelector('#delete-completed-btn');
    
    statusSelect.addEventListener('change', function() {
        if (this.value === 'completed') {
            outcomeGroup.style.display = 'block';
            deleteBtn.style.display = 'inline-flex';
        } else {
            outcomeGroup.style.display = 'none';
            deleteBtn.style.display = 'none';
        }
    });
    
    // Trigger initial check
    if (currentStatus === 'completed') {
        outcomeGroup.style.display = 'block';
        deleteBtn.style.display = 'inline-flex';
    }
}

function showInterventionDetailsModal(intervention) {
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    
    // Format dates
    const createdDate = intervention.created_at ? new Date(intervention.created_at).toLocaleDateString() : 'N/A';
    const updatedDate = intervention.updated_at ? new Date(intervention.updated_at).toLocaleDateString() : 'N/A';
    const dueDate = intervention.due_date ? new Date(intervention.due_date).toLocaleDateString() : 'Not set';
    const completedDate = intervention.completed_date ? new Date(intervention.completed_date).toLocaleDateString() : 'N/A';
    
    // Format intervention type
    const formattedType = intervention.intervention_type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
    
    // Get status and priority colors
    const statusColor = {
        'pending': 'var(--warning-500)',
        'in_progress': 'var(--primary-500)',
        'completed': 'var(--success-500)',
        'cancelled': 'var(--neutral-500)'
    }[intervention.status] || 'var(--neutral-500)';
    
    const priorityColor = {
        'low': 'var(--success-500)',
        'medium': 'var(--warning-500)', 
        'high': 'var(--danger-500)',
        'critical': 'var(--danger-700)'
    }[intervention.priority] || 'var(--neutral-500)';
    
    modal.innerHTML = `
        <div class="modal intervention-details-modal">
            <div class="modal-header">
                <h3><i class="fas fa-info-circle"></i> Intervention Details</h3>
                <button class="modal-close" onclick="closeModal(this)">&times;</button>
            </div>
            <div class="modal-body">
                <div class="intervention-details-content">
                    <div class="detail-header">
                        <h4>${intervention.title}</h4>
                        <div class="status-badges">
                            <span class="badge" style="background-color: ${statusColor}">
                                ${intervention.status.replace('_', ' ').toUpperCase()}
                            </span>
                            <span class="badge" style="background-color: ${priorityColor}">
                                ${intervention.priority.toUpperCase()} PRIORITY
                            </span>
                        </div>
                    </div>
                    
                    <div class="detail-grid">
                        <div class="detail-item">
                            <label>Type:</label>
                            <value>${formattedType}</value>
                        </div>
                        
                        <div class="detail-item">
                            <label>Student:</label>
                            <value>${intervention.student_name || `ID: ${intervention.student_id}`}</value>
                        </div>
                        
                        ${intervention.assigned_to ? `
                        <div class="detail-item">
                            <label>Assigned To:</label>
                            <value>${intervention.assigned_to}</value>
                        </div>
                        ` : ''}
                        
                        <div class="detail-item">
                            <label>Created:</label>
                            <value>${createdDate}</value>
                        </div>
                        
                        <div class="detail-item">
                            <label>Last Updated:</label>
                            <value>${updatedDate}</value>
                        </div>
                        
                        <div class="detail-item">
                            <label>Due Date:</label>
                            <value>${dueDate}</value>
                        </div>
                        
                        ${intervention.status === 'completed' ? `
                        <div class="detail-item">
                            <label>Completed:</label>
                            <value>${completedDate}</value>
                        </div>
                        ` : ''}
                        
                        ${intervention.outcome ? `
                        <div class="detail-item">
                            <label>Outcome:</label>
                            <value>${intervention.outcome.replace('_', ' ').toUpperCase()}</value>
                        </div>
                        ` : ''}
                    </div>
                    
                    ${intervention.description ? `
                    <div class="detail-section">
                        <label>Description:</label>
                        <div class="description-text">${intervention.description}</div>
                    </div>
                    ` : ''}
                    
                    ${intervention.outcome_notes ? `
                    <div class="detail-section">
                        <label>Notes:</label>
                        <div class="notes-text">${intervention.outcome_notes}</div>
                    </div>
                    ` : ''}
                </div>
            </div>
            
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="closeModal(this)">Close</button>
                <button class="btn btn-primary" onclick="closeModal(this); updateInterventionStatus(${intervention.id}, '${intervention.status}')">
                    <i class="fas fa-edit"></i>
                    Update Status
                </button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
}

async function handleInterventionSubmit(event, studentId) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    
    // Convert FormData to JSON
    const data = {
        student_id: studentId, // Keep as-is to support both string and integer IDs
        intervention_type: formData.get('intervention_type'),
        title: formData.get('title'),
        description: formData.get('description'),
        priority: formData.get('priority'),
        assigned_to: formData.get('assigned_to'),
        due_date: formData.get('due_date') || null
    };
    
    try {
        const token = localStorage.getItem('auth_token');
        const response = await fetch('/api/interventions/', {
            method: 'POST',
            headers: {
                'Authorization': token ? `Bearer ${token}` : '',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            const intervention = await response.json();
            
            // Show success notification
            showNotification('Intervention created successfully', 'success');
            
            // Close modal
            closeModal(form);
            
            // Refresh interventions list
            safeRefreshInterventions(data.student_id);
        } else {
            const error = await response.json();
            showNotification(error.detail || 'Failed to create intervention', 'error');
        }
    } catch (error) {
        console.error('Error creating intervention:', error);
        showNotification('Error creating intervention', 'error');
    }
}

async function handleStatusUpdate(event, interventionId) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    
    const data = {
        status: formData.get('status'),
        outcome: formData.get('outcome'),
        outcome_notes: formData.get('outcome_notes')
    };
    
    // Handle cancellation with confirmation and deletion
    if (data.status === 'cancelled') {
        const confirmed = await showCancellationConfirmation();
        if (!confirmed) {
            return; // User cancelled the cancellation
        }
        
        // Delete the intervention instead of updating status
        try {
            const token = localStorage.getItem('auth_token');
            const response = await fetch(`/api/interventions/${interventionId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': token ? `Bearer ${token}` : '',
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                showNotification('Intervention cancelled and deleted permanently', 'success');
                closeModal(form);
                safeRefreshInterventions();
            } else {
                const error = await response.json();
                showNotification(error.detail || 'Failed to delete intervention', 'error');
            }
        } catch (error) {
            console.error('Error deleting intervention:', error);
            showNotification('Error deleting intervention', 'error');
        }
        return;
    }
    
    // Handle normal status updates
    try {
        const token = localStorage.getItem('auth_token');
        const response = await fetch(`/api/interventions/${interventionId}`, {
            method: 'PUT',
            headers: {
                'Authorization': token ? `Bearer ${token}` : '',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            // Show success notification
            showNotification('Intervention status updated', 'success');
            
            // Close modal
            closeModal(form);
            
            // Refresh interventions list
            safeRefreshInterventions();
        } else {
            const error = await response.json();
            showNotification(error.detail || 'Failed to update intervention', 'error');
        }
    } catch (error) {
        console.error('Error updating intervention:', error);
        showNotification('Error updating intervention', 'error');
    }
}

async function handleCompletedInterventionDeletion(interventionId) {
    console.log('Handling completed intervention deletion:', interventionId);
    
    // Show confirmation dialog
    const confirmed = await showCompletedDeletionConfirmation();
    if (!confirmed) {
        return; // User cancelled the deletion
    }
    
    // Delete the completed intervention
    try {
        const token = localStorage.getItem('auth_token');
        const response = await fetch(`/api/interventions/${interventionId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': token ? `Bearer ${token}` : '',
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            showNotification('Completed intervention deleted successfully', 'success');
            
            // Close the status update modal
            const modal = document.querySelector('.modal-overlay');
            if (modal) modal.remove();
            
            // Refresh interventions list
            safeRefreshInterventions();
        } else {
            const error = await response.json();
            showNotification(error.detail || 'Failed to delete completed intervention', 'error');
        }
    } catch (error) {
        console.error('Error deleting completed intervention:', error);
        showNotification('Error deleting completed intervention', 'error');
    }
}

function closeModal(element) {
    const modal = element.closest('.modal-overlay');
    if (modal) {
        modal.remove();
    }
}

function showNotification(message, type = 'info') {
    // Use the existing notification system if available
    if (window.notificationSystem) {
        if (type === 'success') {
            window.notificationSystem.success(message);
        } else if (type === 'error') {
            window.notificationSystem.error(message);
        } else {
            window.notificationSystem.info(message);
        }
    } else {
        // Fallback to alert
        alert(message);
    }
}

function showCancellationConfirmation() {
    return new Promise((resolve) => {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal confirmation-modal">
                <div class="modal-header">
                    <h3><i class="fas fa-exclamation-triangle text-warning"></i> Confirm Intervention Cancellation</h3>
                    <button class="modal-close" onclick="this.closest('.modal-overlay').remove(); arguments[0].resolve(false);">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="warning-message">
                        <p><strong>⚠️ Warning: This action cannot be undone!</strong></p>
                        <p>Cancelling this intervention will <strong>permanently delete</strong> it from the database.</p>
                        <p>Are you sure you want to proceed?</p>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" id="cancel-deletion">
                        <i class="fas fa-times"></i>
                        Keep Intervention
                    </button>
                    <button type="button" class="btn btn-danger" id="confirm-deletion">
                        <i class="fas fa-trash"></i>
                        Yes, Delete Permanently
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Add event listeners
        const cancelBtn = modal.querySelector('#cancel-deletion');
        const confirmBtn = modal.querySelector('#confirm-deletion');
        const closeBtn = modal.querySelector('.modal-close');
        
        cancelBtn.addEventListener('click', () => {
            modal.remove();
            resolve(false);
        });
        
        confirmBtn.addEventListener('click', () => {
            modal.remove();
            resolve(true);
        });
        
        closeBtn.addEventListener('click', () => {
            modal.remove();
            resolve(false);
        });
        
        // Close on background click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
                resolve(false);
            }
        });
    });
}

function showCompletedDeletionConfirmation() {
    return new Promise((resolve) => {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal confirmation-modal">
                <div class="modal-header">
                    <h3><i class="fas fa-check-circle text-success"></i> Delete Completed Intervention</h3>
                    <button class="modal-close" onclick="this.closest('.modal-overlay').remove(); arguments[0].resolve(false);">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="warning-message">
                        <p><strong>🗂️ Archive Completed Intervention</strong></p>
                        <p>This intervention has been completed successfully. You can delete it to clean up your intervention list.</p>
                        <p><strong>⚠️ Note:</strong> This action <strong>permanently removes</strong> the intervention from the database.</p>
                        <p>Are you sure you want to delete this completed intervention?</p>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" id="keep-completed">
                        <i class="fas fa-archive"></i>
                        Keep for Records
                    </button>
                    <button type="button" class="btn btn-danger" id="delete-completed">
                        <i class="fas fa-trash"></i>
                        Yes, Delete Permanently
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Add event listeners
        const keepBtn = modal.querySelector('#keep-completed');
        const deleteBtn = modal.querySelector('#delete-completed');
        const closeBtn = modal.querySelector('.modal-close');
        
        keepBtn.addEventListener('click', () => {
            modal.remove();
            resolve(false);
        });
        
        deleteBtn.addEventListener('click', () => {
            modal.remove();
            resolve(true);
        });
        
        closeBtn.addEventListener('click', () => {
            modal.remove();
            resolve(false);
        });
        
        // Close on background click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
                resolve(false);
            }
        });
    });
}

// Store reference to analysis component for refreshing interventions
window.addEventListener('DOMContentLoaded', function() {
    // Find the analysis component instance
    const analysisElement = document.querySelector('#analysis-tab');
    if (analysisElement && window.Analysis) {
        window.analysisComponent = new window.Analysis();
    }
});