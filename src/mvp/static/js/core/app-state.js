/**
 * Application State Management
 * Centralized state management for the Student Success Predictor
 */

class AppState {
  constructor() {
    this.state = {
      currentTab: 'upload',
      isAuthenticated: false,
      students: [],
      selectedStudent: null,
      integrations: {
        canvas: { connected: false, courses: [] },
        powerschool: { connected: false, schools: [] },
        google: { connected: false, courses: [] }
      },
      notifications: {
        enabled: true,
        websocket: null,
        connected: false,
        alerts: []
      },
      ui: {
        loading: false,
        modal: { open: false, title: '', content: '' },
        progress: 20
      }
    };
    
    this.listeners = new Map();
    this.components = new Map();
  }

  subscribe(key, callback) {
    if (!this.listeners.has(key)) {
      this.listeners.set(key, []);
    }
    this.listeners.get(key).push(callback);
  }

  setState(updates) {
    const oldState = { ...this.state };
    this.state = { ...this.state, ...updates };
    
    Object.keys(updates).forEach(key => {
      if (this.listeners.has(key)) {
        this.listeners.get(key).forEach(callback => callback(this.state[key], oldState[key]));
      }
    });
  }

  getState() {
    return { ...this.state };
  }
}

// Make AppState available globally
window.AppState = AppState;