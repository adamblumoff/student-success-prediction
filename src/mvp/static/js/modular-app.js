/**
 * Modular Student Success Predictor Application
 * Coordinates all components and systems
 */

class StudentSuccessApp {
  constructor() {
    this.appState = new AppState();
    this.components = new Map();
    this.notificationSystem = null;
    this.settingsSystem = null;
    this.cleanupManager = SecureDOM.createCleanupManager();
    this.init();
  }

  async init() {
    try {
      if (document.readyState === 'loading') {
        await new Promise(resolve => {
          document.addEventListener('DOMContentLoaded', resolve);
        });
      }

      this.initializeComponents();
      this.initializeSystems();
      this.appState.components = this.components;
      
      console.log('✅ Modular Student Success App initialized');
      
    } catch (error) {
      console.error('❌ Modular app initialization failed:', error);
    }
  }

  initializeComponents() {
    // Initialize login component first
    if (document.querySelector('#login-container')) {
      this.components.set('login', new LoginComponent('#login-container', this.appState));
    }

    // Initialize main app components only if their DOM elements exist
    if (document.querySelector('.nav-tabs')) {
      this.components.set('tabNavigation', new TabNavigation('.nav-tabs', this.appState));
    }

    if (document.querySelector('#tab-upload')) {
      this.components.set('fileUpload', new FileUpload('#tab-upload', this.appState));
    }

    if (document.querySelector('#tab-analyze')) {
      this.components.set('analysis', new Analysis('#tab-analyze', this.appState));
    }

    if (document.querySelector('#tab-dashboard')) {
      this.components.set('dashboard', new Dashboard('#tab-dashboard', this.appState));
    }

    if (document.querySelector('#tab-insights')) {
      this.components.set('insights', new Insights('#tab-insights', this.appState));
    }

    if (document.querySelector('#loading-overlay')) {
      this.components.set('loading', new LoadingOverlay('#loading-overlay', this.appState));
    }
    
    this.setupGlobalEvents();
  }

  initializeSystems() {
    // Initialize notification system
    this.notificationSystem = new NotificationSystem(this);
    this.notificationSystem.initialize();
    
    // Initialize settings system
    this.settingsSystem = new SettingsSystem(this);
    this.settingsSystem.initialize();
  }

  setupGlobalEvents() {
    // Existing modal events
    const modalOverlay = document.getElementById('modal-overlay');
    const modalClose = document.getElementById('modal-close');
    
    if (modalClose) {
      modalClose.addEventListener('click', () => {
        if (modalOverlay) modalOverlay.classList.add('hidden');
      });
    }
    
    if (modalOverlay) {
      modalOverlay.addEventListener('click', (e) => {
        if (e.target === modalOverlay) {
          modalOverlay.classList.add('hidden');
        }
      });
    }
  }

  // Convenience methods for systems
  showNotification(message, type = 'info') {
    if (this.notificationSystem) {
      this.notificationSystem.showNotification(message, type);
    }
  }

  openSettingsModal() {
    if (this.settingsSystem) {
      this.settingsSystem.openSettingsModal();
    }
  }

  closeSettingsModal() {
    if (this.settingsSystem) {
      this.settingsSystem.closeSettingsModal();
    }
  }

  // Modal management methods (used by components) - XSS-safe
  showModal(title, content, isHTML = false) {
    const modal = document.getElementById('modal');
    const modalOverlay = document.getElementById('modal-overlay');
    const modalTitle = document.getElementById('modal-title');
    const modalContent = document.getElementById('modal-content');

    if (modal && modalTitle && modalContent) {
      // Safely set title (always text)
      SecureDOM.setText(modalTitle, title);
      
      // Safely set content
      if (isHTML) {
        SecureDOM.setHTML(modalContent, content);
      } else {
        SecureDOM.setText(modalContent, content);
      }
      
      if (modalOverlay) modalOverlay.classList.remove('hidden');
    }
  }

  hideModal() {
    const modalOverlay = document.getElementById('modal-overlay');
    if (modalOverlay) modalOverlay.classList.add('hidden');
  }

  // Loading management
  showLoading(show, message = 'Processing...') {
    this.appState.setState({
      ui: {
        ...this.appState.getState().ui,
        loading: show
      }
    });
    
    const loadingOverlay = document.getElementById('loading-overlay');
    const loadingMessage = document.getElementById('loading-message');
    
    if (loadingOverlay) {
      if (show) {
        if (loadingMessage) loadingMessage.textContent = message;
        loadingOverlay.classList.remove('hidden');
      } else {
        loadingOverlay.classList.add('hidden');
      }
    }
  }

  // Component access methods
  getComponent(name) {
    return this.components.get(name);
  }

  // State management shortcuts
  setState(updates) {
    this.appState.setState(updates);
  }

  getState() {
    return this.appState.getState();
  }

  // Make compatible with existing explainable UI integration
  renderStudentsClean(students) {
    if (this.components.has('analysis')) {
      const analysisComponent = this.components.get('analysis');
      if (analysisComponent && analysisComponent.renderStudents) {
        analysisComponent.renderStudents(students);
      }
    }
  }
  
  // Memory leak prevention: cleanup event listeners and references
  cleanup() {
    if (this.cleanupManager) {
      this.cleanupManager.cleanup();
    }
    
    // Clean up components
    for (let [name, component] of this.components) {
      if (component && typeof component.destroy === 'function') {
        component.destroy();
      }
    }
    
    // Clean up systems
    if (this.notificationSystem && typeof this.notificationSystem.cleanup === 'function') {
      this.notificationSystem.cleanup();
    }
    
    if (this.settingsSystem && typeof this.settingsSystem.cleanup === 'function') {
      this.settingsSystem.cleanup();
    }
    
    // Clear references
    this.components.clear();
    this.notificationSystem = null;
    this.settingsSystem = null;
  }

  // Graceful cleanup on page unload or component destruction
  destroy() {
    console.log('🧹 Cleaning up Modular Student Success App');
    this.cleanup();
  }
}

// Make StudentSuccessApp available globally
window.StudentSuccessApp = StudentSuccessApp;

// Automatic cleanup on page unload to prevent memory leaks
window.addEventListener('beforeunload', () => {
  if (window.studentSuccessApp && typeof window.studentSuccessApp.cleanup === 'function') {
    window.studentSuccessApp.cleanup();
  }
});

// Also cleanup on visibility change (when tab becomes hidden)
document.addEventListener('visibilitychange', () => {
  if (document.hidden && window.studentSuccessApp) {
    // Cleanup non-essential resources when tab is hidden
    if (typeof window.studentSuccessApp.cleanup === 'function') {
      window.studentSuccessApp.cleanup();
    }
  }
});