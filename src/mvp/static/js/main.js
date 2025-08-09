/**
 * Main Entry Point for Student Success Predictor
 * Initializes the modular application
 */

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  console.log('🚀 Initializing Modern Student Success App');
  const app = new StudentSuccessApp();
  window.modernApp = app;
  console.log('✅ Modern app initialized and attached to window.modernApp');
});