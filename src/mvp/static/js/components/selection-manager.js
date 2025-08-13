/**
 * Selection Manager - Handles bulk selection state and operations
 * Core component for managing student and intervention selections
 */

class SelectionManager {
    constructor() {
        this.selectedStudents = new Set();
        this.selectedInterventions = new Set();
        this.selectionMode = false;
        this.callbacks = new Map();
        this.init();
    }

    init() {
        console.log('🎯 Selection Manager initialized');
        this.hasShownBulkModeGuidance = localStorage.getItem('bulk_mode_guidance_shown') === 'true';
        this.createFloatingToolbar();
        this.bindEvents();
    }

    // ========== SELECTION STATE MANAGEMENT ==========

    toggleSelectionMode() {
        this.selectionMode = !this.selectionMode;
        
        if (this.selectionMode) {
            this.enterSelectionMode();
        } else {
            this.exitSelectionMode();
        }
        
        this.trigger('selectionModeChanged', this.selectionMode);
        console.log(`Selection mode: ${this.selectionMode ? 'ON' : 'OFF'}`);
    }

    enterSelectionMode() {
        document.body.classList.add('bulk-selection-mode');
        this.showFloatingToolbar();
        this.addCheckboxesToCards();
        this.updateFloatingToolbar();
        
        // Show guidance for first-time users
        if (!this.hasShownBulkModeGuidance) {
            this.showBulkModeGuidance();
        }
    }

    exitSelectionMode() {
        document.body.classList.remove('bulk-selection-mode');
        this.hideFloatingToolbar();
        this.removeCheckboxesFromCards();
        this.clearAllSelections();
    }

    // ========== STUDENT SELECTION ==========

    toggleStudentSelection(studentId) {
        const wasSelected = this.selectedStudents.has(studentId);
        
        if (wasSelected) {
            this.selectedStudents.delete(studentId);
        } else {
            this.selectedStudents.add(studentId);
        }
        
        this.updateStudentCardVisual(studentId, !wasSelected);
        this.updateFloatingToolbar();
        this.trigger('studentSelectionChanged', {
            studentId,
            selected: !wasSelected,
            totalSelected: this.selectedStudents.size
        });
        
        console.log(`🎓 Student ${studentId} ${!wasSelected ? 'selected' : 'deselected'}`);
        console.log(`📊 Current selections: ${this.selectedStudents.size} students, ${this.selectedInterventions.size} interventions`);
    }

    selectAllStudents() {
        const studentCards = document.querySelectorAll('[data-student-id]');
        studentCards.forEach(card => {
            const studentId = parseInt(card.dataset.studentId);
            if (!this.selectedStudents.has(studentId)) {
                this.selectedStudents.add(studentId);
                this.updateStudentCardVisual(studentId, true);
            }
        });
        
        this.updateFloatingToolbar();
        this.trigger('bulkStudentSelection', {
            action: 'selectAll',
            totalSelected: this.selectedStudents.size
        });
        
        console.log(`Selected all students (${this.selectedStudents.size})`);
    }

    clearStudentSelection() {
        const previousCount = this.selectedStudents.size;
        
        this.selectedStudents.forEach(studentId => {
            this.updateStudentCardVisual(studentId, false);
        });
        
        this.selectedStudents.clear();
        this.updateFloatingToolbar();
        this.trigger('bulkStudentSelection', {
            action: 'clearAll',
            previousCount,
            totalSelected: 0
        });
        
        console.log(`Cleared all student selections (${previousCount} were selected)`);
    }

    // ========== INTERVENTION SELECTION ==========

    toggleInterventionSelection(interventionId) {
        const wasSelected = this.selectedInterventions.has(interventionId);
        
        if (wasSelected) {
            this.selectedInterventions.delete(interventionId);
        } else {
            this.selectedInterventions.add(interventionId);
        }
        
        this.updateInterventionCardVisual(interventionId, !wasSelected);
        this.updateFloatingToolbar();
        this.trigger('interventionSelectionChanged', {
            interventionId,
            selected: !wasSelected,
            totalSelected: this.selectedInterventions.size
        });
        
        console.log(`📋 Intervention ${interventionId} ${!wasSelected ? 'selected' : 'deselected'}`);
        console.log(`📊 Current selections: ${this.selectedStudents.size} students, ${this.selectedInterventions.size} interventions`);
    }

    selectAllInterventions() {
        const interventionCards = document.querySelectorAll('[data-intervention-id]');
        interventionCards.forEach(card => {
            const interventionId = parseInt(card.dataset.interventionId);
            if (!this.selectedInterventions.has(interventionId)) {
                this.selectedInterventions.add(interventionId);
                this.updateInterventionCardVisual(interventionId, true);
            }
        });
        
        this.updateFloatingToolbar();
        this.trigger('bulkInterventionSelection', {
            action: 'selectAll',
            totalSelected: this.selectedInterventions.size
        });
    }

    clearInterventionSelection() {
        this.selectedInterventions.forEach(interventionId => {
            this.updateInterventionCardVisual(interventionId, false);
        });
        
        this.selectedInterventions.clear();
        this.updateFloatingToolbar();
        this.trigger('bulkInterventionSelection', {
            action: 'clearAll',
            totalSelected: 0
        });
    }

    clearAllSelections() {
        this.clearStudentSelection();
        this.clearInterventionSelection();
    }

    // ========== UI VISUAL MANAGEMENT ==========

    addCheckboxesToCards() {
        // Add checkboxes to student cards
        const studentCards = document.querySelectorAll('[data-student-id]');
        console.log(`🎯 Adding checkboxes to ${studentCards.length} student cards`);
        console.log('🔍 Student cards found:', Array.from(studentCards).map(card => ({
            id: card.dataset.studentId,
            hasCheckbox: !!card.querySelector('.selection-checkbox'),
            className: card.className
        })));
        
        studentCards.forEach((card, index) => {
            if (!card.querySelector('.selection-checkbox')) {
                const checkbox = this.createSelectionCheckbox('student');
                card.insertBefore(checkbox, card.firstChild);
                console.log(`✅ Added checkbox to student card ${index} (ID: ${card.dataset.studentId})`);
            } else {
                console.log(`⚠️ Student card ${index} already has checkbox (ID: ${card.dataset.studentId})`);
            }
        });

        // Add checkboxes to intervention cards
        const interventionCards = document.querySelectorAll('[data-intervention-id]');
        console.log(`🎯 Adding checkboxes to ${interventionCards.length} intervention cards`);
        interventionCards.forEach(card => {
            if (!card.querySelector('.selection-checkbox')) {
                const checkbox = this.createSelectionCheckbox('intervention');
                card.insertBefore(checkbox, card.firstChild);
            }
        });
    }

    removeCheckboxesFromCards() {
        document.querySelectorAll('.selection-checkbox').forEach(checkbox => {
            checkbox.remove();
        });
    }

    createSelectionCheckbox(type = 'student') {
        const checkbox = document.createElement('div');
        checkbox.className = 'selection-checkbox';
        checkbox.innerHTML = `
            <input type="checkbox" class="selection-input" data-type="${type}">
            <div class="selection-indicator">
                <i class="fas fa-check"></i>
            </div>
        `;
        
        const input = checkbox.querySelector('.selection-input');
        input.addEventListener('change', (e) => {
            e.stopPropagation();
            const card = e.target.closest('[data-student-id], [data-intervention-id]');
            
            console.log(`🖱️ Checkbox clicked: type=${type}, card found:`, card);
            console.log(`📋 Card data:`, card ? {
                studentId: card.dataset.studentId,
                interventionId: card.dataset.interventionId,
                className: card.className
            } : 'No card found');
            
            if (type === 'student' && card && card.dataset.studentId) {
                console.log(`🎓 Triggering student selection for ID: ${card.dataset.studentId}`);
                this.toggleStudentSelection(parseInt(card.dataset.studentId));
            } else if (type === 'intervention' && card && card.dataset.interventionId) {
                console.log(`📋 Triggering intervention selection for ID: ${card.dataset.interventionId}`);
                this.toggleInterventionSelection(parseInt(card.dataset.interventionId));
            } else {
                console.error(`❌ Selection failed: type=${type}, card exists=${!!card}, studentId=${card?.dataset.studentId}, interventionId=${card?.dataset.interventionId}`);
            }
        });
        
        return checkbox;
    }

    updateStudentCardVisual(studentId, selected) {
        const card = document.querySelector(`[data-student-id="${studentId}"]`);
        if (!card) return;
        
        const checkbox = card.querySelector('.selection-input');
        const indicator = card.querySelector('.selection-indicator');
        
        if (checkbox) checkbox.checked = selected;
        
        if (selected) {
            card.classList.add('selected');
            if (indicator) indicator.classList.add('checked');
        } else {
            card.classList.remove('selected');
            if (indicator) indicator.classList.remove('checked');
        }
    }

    updateInterventionCardVisual(interventionId, selected) {
        const card = document.querySelector(`[data-intervention-id="${interventionId}"]`);
        if (!card) return;
        
        const checkbox = card.querySelector('.selection-input');
        if (checkbox) checkbox.checked = selected;
        
        if (selected) {
            card.classList.add('selected');
        } else {
            card.classList.remove('selected');
        }
    }

    // ========== FLOATING TOOLBAR ==========

    createFloatingToolbar() {
        const toolbar = document.createElement('div');
        toolbar.id = 'bulk-action-toolbar';
        toolbar.className = 'bulk-action-toolbar hidden';
        toolbar.innerHTML = `
            <div class="toolbar-content">
                <div class="selection-info">
                    <span class="selection-count">0 items selected</span>
                    <button class="btn btn-sm btn-ghost" id="clear-selection">
                        <i class="fas fa-times"></i>
                        Clear
                    </button>
                </div>
                
                <div class="toolbar-actions">
                    <button class="btn btn-sm btn-primary" id="bulk-create-intervention" style="display: none;">
                        <i class="fas fa-plus"></i>
                        Create Interventions (<span class="student-count">0</span>)
                    </button>
                    
                    <button class="btn btn-sm btn-warning" id="bulk-update-status" style="display: none;">
                        <i class="fas fa-edit"></i>
                        Update Status (<span class="intervention-count">0</span>)
                    </button>
                    
                    <button class="btn btn-sm btn-primary" id="bulk-assign" style="display: none;">
                        <i class="fas fa-user-plus"></i>
                        Assign Staff (<span class="assign-count">0</span>)
                    </button>
                    
                    <button class="btn btn-sm btn-danger" id="bulk-delete" style="display: none;">
                        <i class="fas fa-trash"></i>
                        Delete (<span class="delete-count">0</span>)
                    </button>
                    
                    <button class="btn btn-sm btn-success" id="bulk-mixed-action" style="display: none;">
                        <i class="fas fa-magic"></i>
                        Mixed Actions (<span class="mixed-count">0</span>)
                    </button>
                </div>
                
                <div class="toolbar-toggle">
                    <button class="btn btn-sm btn-ghost" id="exit-selection-mode">
                        <i class="fas fa-times"></i>
                        Exit Selection
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(toolbar);
    }

    showFloatingToolbar() {
        const toolbar = document.getElementById('bulk-action-toolbar');
        if (toolbar) {
            toolbar.classList.remove('hidden');
            // Animate in
            setTimeout(() => toolbar.classList.add('visible'), 10);
        }
    }

    hideFloatingToolbar() {
        const toolbar = document.getElementById('bulk-action-toolbar');
        if (toolbar) {
            toolbar.classList.remove('visible');
            setTimeout(() => toolbar.classList.add('hidden'), 200);
        }
    }

    updateFloatingToolbar() {
        const toolbar = document.getElementById('bulk-action-toolbar');
        if (!toolbar) return;
        
        const studentCount = this.selectedStudents.size;
        const interventionCount = this.selectedInterventions.size;
        const totalCount = studentCount + interventionCount;
        
        // Update selection info
        const countElement = toolbar.querySelector('.selection-count');
        if (countElement) {
            if (totalCount === 0) {
                countElement.textContent = 'No items selected';
            } else if (studentCount > 0 && interventionCount > 0) {
                countElement.textContent = `${studentCount} students, ${interventionCount} interventions selected`;
            } else if (studentCount > 0) {
                countElement.textContent = `${studentCount} student${studentCount !== 1 ? 's' : ''} selected`;
            } else if (interventionCount > 0) {
                countElement.textContent = `${interventionCount} intervention${interventionCount !== 1 ? 's' : ''} selected`;
            }
        }
        
        // Update action buttons
        const bulkCreateBtn = toolbar.querySelector('#bulk-create-intervention');
        const bulkUpdateBtn = toolbar.querySelector('#bulk-update-status');
        const bulkAssignBtn = toolbar.querySelector('#bulk-assign');
        const bulkDeleteBtn = toolbar.querySelector('#bulk-delete');
        const bulkMixedBtn = toolbar.querySelector('#bulk-mixed-action');
        
        if (bulkCreateBtn) {
            bulkCreateBtn.style.display = studentCount > 0 ? 'flex' : 'none';
            const studentCountSpan = bulkCreateBtn.querySelector('.student-count');
            if (studentCountSpan) studentCountSpan.textContent = studentCount;
        }
        
        if (bulkUpdateBtn) {
            bulkUpdateBtn.style.display = interventionCount > 0 ? 'flex' : 'none';
            const interventionCountSpan = bulkUpdateBtn.querySelector('.intervention-count');
            if (interventionCountSpan) interventionCountSpan.textContent = interventionCount;
        }
        
        if (bulkAssignBtn) {
            bulkAssignBtn.style.display = interventionCount > 0 ? 'flex' : 'none';
            const assignCountSpan = bulkAssignBtn.querySelector('.assign-count');
            if (assignCountSpan) assignCountSpan.textContent = interventionCount;
        }
        
        if (bulkDeleteBtn) {
            bulkDeleteBtn.style.display = interventionCount > 0 ? 'flex' : 'none';
            const deleteCountSpan = bulkDeleteBtn.querySelector('.delete-count');
            if (deleteCountSpan) deleteCountSpan.textContent = interventionCount;
        }
        
        // Show mixed action button when both students and interventions are selected
        if (bulkMixedBtn) {
            const showMixed = (studentCount > 0 && interventionCount > 0);
            console.log(`🎭 Mixed button logic: ${studentCount} students, ${interventionCount} interventions, show: ${showMixed}`);
            bulkMixedBtn.style.display = showMixed ? 'flex' : 'none';
            const mixedCountSpan = bulkMixedBtn.querySelector('.mixed-count');
            if (mixedCountSpan) mixedCountSpan.textContent = totalCount;
        }
    }

    // ========== EVENT MANAGEMENT ==========

    bindEvents() {
        // Toolbar events
        document.addEventListener('click', (e) => {
            if (e.target.id === 'clear-selection' || e.target.closest('#clear-selection')) {
                this.clearAllSelections();
            } else if (e.target.id === 'exit-selection-mode' || e.target.closest('#exit-selection-mode')) {
                this.toggleSelectionMode();
            } else if (e.target.id === 'bulk-create-intervention' || e.target.closest('#bulk-create-intervention')) {
                this.trigger('bulkCreateIntervention', Array.from(this.selectedStudents));
            } else if (e.target.id === 'bulk-update-status' || e.target.closest('#bulk-update-status')) {
                this.trigger('bulkUpdateStatus', Array.from(this.selectedInterventions));
            } else if (e.target.id === 'bulk-assign' || e.target.closest('#bulk-assign')) {
                this.trigger('bulkAssign', Array.from(this.selectedInterventions));
            } else if (e.target.id === 'bulk-delete' || e.target.closest('#bulk-delete')) {
                this.trigger('bulkDelete', Array.from(this.selectedInterventions));
            } else if (e.target.id === 'bulk-mixed-action' || e.target.closest('#bulk-mixed-action')) {
                this.trigger('bulkMixedAction', {
                    students: Array.from(this.selectedStudents),
                    interventions: Array.from(this.selectedInterventions)
                });
            }
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (this.selectionMode) {
                if (e.key === 'Escape') {
                    this.toggleSelectionMode();
                } else if ((e.ctrlKey || e.metaKey) && e.key === 'a') {
                    e.preventDefault();
                    this.selectAllStudents();
                    this.selectAllInterventions();
                } else if ((e.ctrlKey || e.metaKey) && e.key === 'd') {
                    e.preventDefault();
                    this.clearAllSelections();
                }
            }
        });
    }

    // ========== UTILITY METHODS ==========

    getSelectedStudents() {
        return Array.from(this.selectedStudents);
    }

    getSelectedInterventions() {
        return Array.from(this.selectedInterventions);
    }

    getSelectionCounts() {
        return {
            students: this.selectedStudents.size,
            interventions: this.selectedInterventions.size,
            total: this.selectedStudents.size + this.selectedInterventions.size
        };
    }

    isInSelectionMode() {
        return this.selectionMode;
    }

    // Event system
    on(event, callback) {
        if (!this.callbacks.has(event)) {
            this.callbacks.set(event, []);
        }
        this.callbacks.get(event).push(callback);
    }

    trigger(event, data = null) {
        if (this.callbacks.has(event)) {
            this.callbacks.get(event).forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`Error in ${event} callback:`, error);
                }
            });
        }
    }

    // Cleanup
    destroy() {
        this.hideFloatingToolbar();
        document.getElementById('bulk-action-toolbar')?.remove();
        this.removeCheckboxesFromCards();
        document.body.classList.remove('bulk-selection-mode');
        this.callbacks.clear();
        console.log('🗑️ Selection Manager destroyed');
    }

    showBulkModeGuidance() {
        this.hasShownBulkModeGuidance = true;
        localStorage.setItem('bulk_mode_guidance_shown', 'true');

        // Use notification system to show guidance
        if (window.notificationSystem) {
            window.notificationSystem.addNotification({
                title: '🎯 Bulk Actions Enabled!',
                message: 'You can now select multiple students using checkboxes to create interventions for them all at once. Click students to select them, then use the floating toolbar to create bulk interventions.',
                type: 'info',
                duration: 8000
            });
        }
    }
}

// Global instance
window.selectionManager = new SelectionManager();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SelectionManager;
}