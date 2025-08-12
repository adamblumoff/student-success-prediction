/**
 * Bulk Operations Manager
 * Coordinates between selection manager and bulk operation modals
 */

class BulkOperationsManager {
    constructor() {
        this.init();
    }

    init() {
        console.log('🔧 Bulk Operations Manager initialized');
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Wait for selection manager to be available
        document.addEventListener('DOMContentLoaded', () => {
            this.waitForSelectionManager();
        });
    }

    waitForSelectionManager() {
        if (window.selectionManager) {
            this.bindSelectionManagerEvents();
        } else {
            // Retry after a short delay
            setTimeout(() => this.waitForSelectionManager(), 100);
        }
    }

    bindSelectionManagerEvents() {
        const selectionManager = window.selectionManager;

        // Bulk intervention creation
        selectionManager.on('bulkCreateIntervention', (studentIds) => {
            console.log('🎯 Triggering bulk intervention creation for', studentIds.length, 'students');
            if (window.bulkInterventionModal) {
                window.bulkInterventionModal.show(studentIds);
            }
        });

        // Bulk status update
        selectionManager.on('bulkUpdateStatus', (interventionIds) => {
            console.log('🔄 Triggering bulk status update for', interventionIds.length, 'interventions');
            if (window.bulkStatusModal) {
                window.bulkStatusModal.show(interventionIds);
            }
        });

        // Bulk deletion
        selectionManager.on('bulkDelete', (interventionIds) => {
            console.log('🗑️ Triggering bulk deletion for', interventionIds.length, 'interventions');
            this.handleBulkDelete(interventionIds);
        });

        console.log('✅ Selection manager events bound to bulk operations');
    }

    async handleBulkDelete(interventionIds) {
        if (interventionIds.length === 0) {
            this.showNotification('No interventions selected for deletion', 'warning');
            return;
        }

        // Show confirmation dialog
        const confirmed = await this.showBulkDeleteConfirmation(interventionIds.length);
        if (!confirmed) return;

        try {
            this.showNotification('Deleting interventions...', 'info');

            const token = localStorage.getItem('auth_token');
            const response = await fetch('/api/interventions/bulk/delete', {
                method: 'DELETE',
                headers: {
                    'Authorization': token ? `Bearer ${token}` : '',
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(interventionIds)
            });

            const result = await response.json();

            if (response.ok) {
                this.showNotification(
                    `Successfully deleted ${result.successful} of ${result.total_requested} interventions`, 
                    'success'
                );

                // Clear selections and refresh UI
                if (window.selectionManager) {
                    window.selectionManager.clearInterventionSelection();
                }

                // Refresh the current view
                this.refreshCurrentView();
            } else {
                throw new Error(result.detail || 'Failed to delete interventions');
            }

        } catch (error) {
            console.error('Error in bulk deletion:', error);
            this.showNotification('Error deleting interventions', 'error');
        }
    }

    showBulkDeleteConfirmation(count) {
        return new Promise((resolve) => {
            const modal = document.createElement('div');
            modal.className = 'modal-overlay';
            modal.innerHTML = `
                <div class="modal confirmation-modal">
                    <div class="modal-header">
                        <h3><i class="fas fa-exclamation-triangle text-warning"></i> Confirm Bulk Deletion</h3>
                        <button class="modal-close">&times;</button>
                    </div>
                    <div class="modal-body">
                        <div class="warning-message">
                            <p><strong>⚠️ Warning: This action cannot be undone!</strong></p>
                            <p>You are about to permanently delete <strong>${count} intervention${count !== 1 ? 's' : ''}</strong> from the database.</p>
                            <p>Are you sure you want to proceed?</p>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" id="cancel-bulk-delete">
                            <i class="fas fa-times"></i>
                            Cancel
                        </button>
                        <button type="button" class="btn btn-danger" id="confirm-bulk-delete">
                            <i class="fas fa-trash"></i>
                            Yes, Delete ${count} Intervention${count !== 1 ? 's' : ''}
                        </button>
                    </div>
                </div>
            `;
            
            document.body.appendChild(modal);
            
            const cancelBtn = modal.querySelector('#cancel-bulk-delete');
            const confirmBtn = modal.querySelector('#confirm-bulk-delete');
            const closeBtn = modal.querySelector('.modal-close');
            
            const cleanup = (result) => {
                modal.remove();
                resolve(result);
            };
            
            cancelBtn.addEventListener('click', () => cleanup(false));
            confirmBtn.addEventListener('click', () => cleanup(true));
            closeBtn.addEventListener('click', () => cleanup(false));
            
            modal.addEventListener('click', (e) => {
                if (e.target === modal) cleanup(false);
            });
        });
    }

    refreshCurrentView() {
        // Try to refresh the current view
        try {
            const currentStudent = window.appState?.getState?.()?.selectedStudent;
            if (currentStudent && window.analysisComponent) {
                window.analysisComponent.loadStudentInterventions(currentStudent);
            }
        } catch (error) {
            console.log('Could not refresh current view:', error);
        }
    }

    showNotification(message, type = 'info') {
        if (window.notificationSystem) {
            if (type === 'success') {
                window.notificationSystem.success(message);
            } else if (type === 'error') {
                window.notificationSystem.error(message);
            } else if (type === 'warning') {
                window.notificationSystem.warning(message);
            } else {
                window.notificationSystem.info(message);
            }
        } else {
            alert(message);
        }
    }
}

// Initialize globally
window.bulkOperationsManager = new BulkOperationsManager();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = BulkOperationsManager;
}