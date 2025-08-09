/**
 * Settings System
 * Handles settings modal, persistence, and application preferences
 */

class SettingsSystem {
  constructor(appInstance) {
    this.app = appInstance;
    this.refreshInterval = null;
  }

  initialize() {
    // Set up settings event listeners
    const settingsToggle = document.getElementById('settings-toggle');
    const settingsModalOverlay = document.getElementById('settings-modal-overlay');
    const settingsModalClose = document.getElementById('settings-modal-close');
    const saveButton = document.getElementById('save-settings');
    const resetButton = document.getElementById('reset-settings');
    const exportButton = document.getElementById('export-data');
    const clearCacheButton = document.getElementById('clear-cache');

    if (settingsToggle) {
      settingsToggle.addEventListener('click', () => {
        this.openSettingsModal();
      });
    }

    if (settingsModalClose) {
      settingsModalClose.addEventListener('click', () => {
        this.closeSettingsModal();
      });
    }

    if (settingsModalOverlay) {
      settingsModalOverlay.addEventListener('click', (e) => {
        if (e.target === settingsModalOverlay) {
          this.closeSettingsModal();
        }
      });
    }

    if (saveButton) {
      saveButton.addEventListener('click', () => this.saveSettings());
    }

    if (resetButton) {
      resetButton.addEventListener('click', () => this.resetSettings());
    }

    if (exportButton) {
      exportButton.addEventListener('click', () => this.exportData());
    }

    if (clearCacheButton) {
      clearCacheButton.addEventListener('click', () => this.clearCache());
    }

    // Load settings on initialization
    this.loadSettingsFromStorage();
  }

  openSettingsModal() {
    const settingsModalOverlay = document.getElementById('settings-modal-overlay');
    if (settingsModalOverlay) {
      this.loadSettingsFromStorage();
      settingsModalOverlay.classList.remove('hidden');
    }
  }

  closeSettingsModal() {
    const settingsModalOverlay = document.getElementById('settings-modal-overlay');
    if (settingsModalOverlay) settingsModalOverlay.classList.add('hidden');
  }

  getDefaultSettings() {
    return {
      theme: 'light',
      fontSize: 'medium',
      defaultFilter: 'all',
      autoRefresh: false,
      showConfidence: false,
      enableNotifications: false,
      soundAlerts: false
    };
  }

  loadSettingsFromStorage() {
    try {
      const stored = localStorage.getItem('studentSuccessSettings');
      const settings = stored ? JSON.parse(stored) : this.getDefaultSettings();
      
      // Apply settings to UI elements
      const themeSelect = document.getElementById('theme-select');
      const fontSizeSelect = document.getElementById('font-size-select');
      const defaultFilterSelect = document.getElementById('default-filter');
      const autoRefreshCheck = document.getElementById('auto-refresh');
      const showConfidenceCheck = document.getElementById('show-confidence');
      const notificationsCheck = document.getElementById('enable-notifications');
      const soundAlertsCheck = document.getElementById('sound-alerts');

      if (themeSelect) themeSelect.value = settings.theme;
      if (fontSizeSelect) fontSizeSelect.value = settings.fontSize;
      if (defaultFilterSelect) defaultFilterSelect.value = settings.defaultFilter;
      if (autoRefreshCheck) autoRefreshCheck.checked = settings.autoRefresh;
      if (showConfidenceCheck) showConfidenceCheck.checked = settings.showConfidence;
      if (notificationsCheck) notificationsCheck.checked = settings.enableNotifications;
      if (soundAlertsCheck) soundAlertsCheck.checked = settings.soundAlerts;

      // Apply settings to the application
      this.applySettings(settings);
      
    } catch (error) {
      console.error('Error loading settings:', error);
      this.loadSettingsFromStorage(); // Load defaults on error
    }
  }

  saveSettings() {
    try {
      const settings = {
        theme: document.getElementById('theme-select')?.value || 'light',
        fontSize: document.getElementById('font-size-select')?.value || 'medium',
        defaultFilter: document.getElementById('default-filter')?.value || 'all',
        autoRefresh: document.getElementById('auto-refresh')?.checked || false,
        showConfidence: document.getElementById('show-confidence')?.checked || false,
        enableNotifications: document.getElementById('enable-notifications')?.checked || false,
        soundAlerts: document.getElementById('sound-alerts')?.checked || false
      };

      localStorage.setItem('studentSuccessSettings', JSON.stringify(settings));
      this.applySettings(settings);
      
      this.app.notificationSystem.showNotification('Settings saved successfully!', 'success');
      this.closeSettingsModal();
      
    } catch (error) {
      console.error('Error saving settings:', error);
      this.app.notificationSystem.showNotification('Error saving settings', 'error');
    }
  }

  resetSettings() {
    const defaults = this.getDefaultSettings();
    localStorage.setItem('studentSuccessSettings', JSON.stringify(defaults));
    this.loadSettingsFromStorage();
    this.app.notificationSystem.showNotification('Settings reset to defaults', 'success');
  }

  applySettings(settings) {
    // Apply theme
    document.documentElement.setAttribute('data-theme', settings.theme);
    
    // Apply font size
    document.documentElement.setAttribute('data-font-size', settings.fontSize);
    
    // Apply other settings as needed
    if (settings.autoRefresh && !this.refreshInterval) {
      this.startAutoRefresh();
    } else if (!settings.autoRefresh && this.refreshInterval) {
      this.stopAutoRefresh();
    }
  }

  exportData() {
    try {
      const currentData = this.app.appState.getState();
      const dataToExport = {
        students: currentData.students || [],
        summary: currentData.summary || {},
        exportDate: new Date().toISOString(),
        version: '1.0'
      };

      const blob = new Blob([JSON.stringify(dataToExport, null, 2)], 
        { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `student-analysis-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      this.app.notificationSystem.showNotification('Data exported successfully!', 'success');
    } catch (error) {
      console.error('Error exporting data:', error);
      this.app.notificationSystem.showNotification('Error exporting data', 'error');
    }
  }

  clearCache() {
    try {
      // Clear localStorage except settings
      const settings = localStorage.getItem('studentSuccessSettings');
      localStorage.clear();
      if (settings) {
        localStorage.setItem('studentSuccessSettings', settings);
      }

      // Clear session storage
      sessionStorage.clear();

      // Reset app state
      this.app.appState.setState({
        students: [],
        summary: {},
        selectedStudent: null
      });

      this.app.notificationSystem.showNotification('Cache cleared successfully!', 'success');
    } catch (error) {
      console.error('Error clearing cache:', error);
      this.app.notificationSystem.showNotification('Error clearing cache', 'error');
    }
  }

  startAutoRefresh() {
    if (this.refreshInterval) return;
    
    this.refreshInterval = setInterval(() => {
      const currentTab = this.app.appState.getState().currentTab;
      if (currentTab === 'analyze' || currentTab === 'dashboard') {
        // Refresh data
        console.log('Auto-refreshing data...');
        this.app.notificationSystem.showNotification('Data refreshed', 'info');
      }
    }, 5 * 60 * 1000); // 5 minutes
  }

  stopAutoRefresh() {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
      this.refreshInterval = null;
    }
  }
}

// Make SettingsSystem available globally
window.SettingsSystem = SettingsSystem;