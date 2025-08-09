/**
 * Loading Overlay Component
 * Shows loading states and progress indicators
 */

class LoadingOverlay extends Component {
  init() {
    this.overlay = document.getElementById('loading-overlay');
    this.messageElement = document.getElementById('loading-message');
    
    this.appState.subscribe('ui', this.updateLoadingState.bind(this));
  }

  updateLoadingState(uiState) {
    if (!this.overlay) return;
    
    if (uiState.loading) {
      this.show();
      if (this.messageElement && uiState.loadingMessage) {
        this.messageElement.textContent = uiState.loadingMessage;
      }
    } else {
      this.hide();
    }
  }

  show() {
    this.overlay.classList.remove('hidden');
  }

  hide() {
    this.overlay.classList.add('hidden');
  }
}
