/**
 * Tab Navigation Component
 * Manages tab switching and progress tracking
 */

class TabNavigation extends Component {
  init() {
    this.tabs = document.querySelectorAll('.tab-button');
    this.tabContents = document.querySelectorAll('.tab-content');
    this.progressBar = document.querySelector('.progress-fill');
    
    this.tabs.forEach(tab => {
      this.bindEvent(tab, 'click', this.handleTabClick);
    });

    this.appState.subscribe('currentTab', this.updateActiveTab.bind(this));
    this.appState.subscribe('ui', this.updateProgress.bind(this));
  }

  handleTabClick(event) {
    const tabId = event.currentTarget.dataset.tab;
    if (!event.currentTarget.disabled) {
      this.appState.setState({ currentTab: tabId });
    }
  }

  updateActiveTab(currentTab) {
    this.tabs.forEach(tab => {
      tab.classList.toggle('active', tab.dataset.tab === currentTab);
    });

    this.tabContents.forEach(content => {
      content.classList.toggle('active', content.id === `tab-${currentTab}`);
    });

    // Bulk actions are now embedded in the analyze tab content

    this.updateProgressForTab(currentTab);
    this.updateTabStates(currentTab);
  }


  updateProgressForTab(tab) {
    const progressMap = {
      'upload': 20,
      'connect': 40,
      'analyze': 60,
      'dashboard': 80
    };
    
    const progress = progressMap[tab] || 20;
    this.appState.setState({ ui: { ...this.appState.getState().ui, progress } });
  }

  updateProgress(uiState) {
    if (this.progressBar && uiState.progress !== undefined) {
      this.progressBar.style.width = `${uiState.progress}%`;
    }
  }

  updateTabStates(currentTab) {
    const tabOrder = ['upload', 'connect', 'analyze', 'dashboard'];
    const currentIndex = tabOrder.indexOf(currentTab);
    
    this.tabs.forEach(tab => {
      const tabIndex = tabOrder.indexOf(tab.dataset.tab);
      tab.disabled = tabIndex > currentIndex + 1;
    });
  }

  enableTab(tabName) {
    const tab = document.querySelector(`[data-tab="${tabName}"]`);
    if (tab) {
      tab.disabled = false;
    }
  }
}