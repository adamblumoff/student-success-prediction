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

// Helper function to safely refresh interventions
function safeRefreshInterventions(studentId) {
    try {
        const currentStudent = window.appState?.getState?.()?.selectedStudent;
        if (currentStudent && window.analysisComponent) {
            window.analysisComponent.loadStudentInterventions(currentStudent);
        } else {
            // Fallback: reload the interventions for the current student
            const listContainer = document.getElementById(`interventions-list-${studentId}`);
            if (listContainer) {
                loadInterventionsForContainer(studentId, listContainer);
            }
        }
    } catch (refreshError) {
        console.log('Could not refresh interventions list:', refreshError);
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
                </div>
            </form>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Show outcome field if status is completed
    const statusSelect = modal.querySelector('#status-select');
    const outcomeGroup = modal.querySelector('#outcome-group');
    
    statusSelect.addEventListener('change', function() {
        if (this.value === 'completed') {
            outcomeGroup.style.display = 'block';
        } else {
            outcomeGroup.style.display = 'none';
        }
    });
    
    // Trigger initial check
    if (currentStatus === 'completed') {
        outcomeGroup.style.display = 'block';
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
        student_id: parseInt(studentId),
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
            safeRefreshInterventions(data.student_id);
        } else {
            const error = await response.json();
            showNotification(error.detail || 'Failed to update intervention', 'error');
        }
    } catch (error) {
        console.error('Error updating intervention:', error);
        showNotification('Error updating intervention', 'error');
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

// Store reference to analysis component for refreshing interventions
window.addEventListener('DOMContentLoaded', function() {
    // Find the analysis component instance
    const analysisElement = document.querySelector('#analysis-tab');
    if (analysisElement && window.Analysis) {
        window.analysisComponent = new window.Analysis();
    }
});