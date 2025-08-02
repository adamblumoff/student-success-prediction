/**
 * Unified Integration Controller
 * Manages the dropdown selection and coordinates between Canvas, PowerSchool, and Google Classroom integrations
 */

class UnifiedIntegrationController {
    constructor() {
        this.currentIntegration = null;
        this.integrationInstances = {};
        this.init();
    }

    init() {
        this.bindEvents();
        this.initializeIntegrationInstances();
    }

    bindEvents() {
        // Integration type selection
        document.getElementById('integration-type')?.addEventListener('change', (e) => {
            this.selectIntegration(e.target.value);
        });
    }

    initializeIntegrationInstances() {
        // Initialize individual integration classes when they're available
        if (typeof CanvasIntegration !== 'undefined') {
            this.integrationInstances.canvas = new CanvasIntegration();
        }
        if (typeof PowerSchoolIntegration !== 'undefined') {
            this.integrationInstances.powerschool = new PowerSchoolIntegration();
        }
        if (typeof GoogleClassroomIntegration !== 'undefined') {
            this.integrationInstances.google = new GoogleClassroomIntegration();
        }
    }

    selectIntegration(integrationType) {
        // Hide all integration forms
        this.hideAllIntegrations();
        
        if (!integrationType) {
            this.currentIntegration = null;
            return;
        }
        
        // Show selected integration form
        const integrationForm = document.getElementById(`${integrationType}-integration`);
        if (integrationForm) {
            integrationForm.classList.remove('hidden');
            this.currentIntegration = integrationType;
            
            // Initialize the specific integration if needed
            this.initializeSpecificIntegration(integrationType);
        }
    }

    hideAllIntegrations() {
        const integrationForms = document.querySelectorAll('.integration-form');
        integrationForms.forEach(form => {
            form.classList.add('hidden');
        });
    }

    initializeSpecificIntegration(type) {
        switch (type) {
            case 'canvas':
                // Canvas integration is already initialized
                break;
            case 'powerschool':
                // PowerSchool integration is already initialized
                break;
            case 'google-classroom':
                // Google Classroom integration is already initialized
                break;
        }
    }

    showMessage(message, type = 'info') {
        const statusDiv = document.getElementById('integration-status');
        if (!statusDiv) return;
        
        statusDiv.className = `status-message ${type}`;
        statusDiv.textContent = message;
        statusDiv.classList.remove('hidden');
        
        if (type === 'success' || type === 'error') {
            setTimeout(() => {
                statusDiv.classList.add('hidden');
            }, 5000);
        }
    }

    getCurrentIntegration() {
        return this.currentIntegration;
    }

    getIntegrationInstance(type) {
        return this.integrationInstances[type];
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    if (typeof window !== 'undefined') {
        window.unifiedIntegration = new UnifiedIntegrationController();
    }
});

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = UnifiedIntegrationController;
}