/**
 * Modern Student Success Predictor - Fixed with Working Integration Patterns
 * Replicates the exact working patterns from the original app.js
 */

// =============================================================================
// Application State Management
// =============================================================================

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

// =============================================================================
// Component Base Class
// =============================================================================

class Component {
  constructor(selector, appState) {
    this.element = document.querySelector(selector);
    this.appState = appState;
    this.boundMethods = new Set();
    
    if (!this.element) {
      console.warn(`Component element not found: ${selector}`);
      return;
    }
    
    this.init();
  }

  init() {
    // Override in subclasses
  }

  bindEvent(element, event, handler) {
    const boundHandler = handler.bind(this);
    element.addEventListener(event, boundHandler);
    this.boundMethods.add(() => element.removeEventListener(event, boundHandler));
    return boundHandler;
  }

  destroy() {
    this.boundMethods.forEach(cleanup => cleanup());
    this.boundMethods.clear();
  }

  show() {
    if (this.element) this.element.classList.remove('hidden');
  }

  hide() {
    if (this.element) this.element.classList.add('hidden');
  }

  setContent(content) {
    if (this.element) this.element.innerHTML = content;
  }
}

// =============================================================================
// Tab Navigation Component
// =============================================================================

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

    this.updateProgressForTab(currentTab);
    this.updateTabStates(currentTab);
  }

  updateProgressForTab(tab) {
    const progressMap = {
      'upload': 20,
      'connect': 40,
      'analyze': 60,
      'dashboard': 80,
      'insights': 100
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
    const tabOrder = ['upload', 'connect', 'analyze', 'dashboard', 'insights'];
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

// =============================================================================
// File Upload Component - EXACT REPLICA OF WORKING VERSION
// =============================================================================

class FileUpload extends Component {
  init() {
    this.fileInput = document.getElementById('file-input');
    this.uploadZone = document.getElementById('upload-zone');
    this.sampleButton = document.getElementById('load-sample');
    this.demoButton = document.getElementById('start-demo');
    
    // Initialize exactly like the working version
    this.initializeAuthentication();
    
    if (this.fileInput) {
      this.bindEvent(this.fileInput, 'change', this.handleFileSelect);
    }
    
    if (this.uploadZone) {
      this.setupDragAndDrop();
    }
    
    if (this.sampleButton) {
      this.bindEvent(this.sampleButton, 'click', this.loadSampleData);
    }
    
    if (this.demoButton) {
      this.bindEvent(this.demoButton, 'click', this.startDemo);
    }
  }

  // EXACT REPLICA of working authentication
  async initializeAuthentication() {
    try {
      // Check if already authenticated
      const statusResponse = await fetch('/api/mvp/auth/status');
      if (statusResponse.ok) {
        console.log('✅ Already authenticated');
        return;
      }
    } catch (error) {
      // Not authenticated, proceed with login
    }

    try {
      // Perform web login to get session cookie
      const loginResponse = await fetch('/api/mvp/auth/web-login', {
        method: 'POST',
        credentials: 'include' // Important: include cookies
      });
      
      if (loginResponse.ok) {
        console.log('✅ Web authentication successful');
      } else {
        console.error('❌ Authentication failed');
      }
    } catch (error) {
      console.error('❌ Authentication error:', error);
    }
  }

  setupDragAndDrop() {
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
      this.bindEvent(this.uploadZone, eventName, this.preventDefaults);
    });

    ['dragenter', 'dragover'].forEach(eventName => {
      this.bindEvent(this.uploadZone, eventName, this.highlight);
    });

    ['dragleave', 'drop'].forEach(eventName => {
      this.bindEvent(this.uploadZone, eventName, this.unhighlight);
    });

    this.bindEvent(this.uploadZone, 'drop', this.handleDrop);
  }

  preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
  }

  highlight() {
    this.uploadZone.classList.add('drag-over');
  }

  unhighlight() {
    this.uploadZone.classList.remove('drag-over');
  }

  handleDrop(e) {
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      this.handleFileUpload(files[0]);
    }
  }

  handleFileSelect(e) {
    const files = e.target.files;
    if (files.length > 0) {
      this.handleFileUpload(files[0]);
    }
  }

  // EXACT REPLICA of working file upload
  async handleFileUpload(file) {
    if (!file.name.endsWith('.csv')) {
      alert('Please upload a CSV file.');
      return;
    }

    this.showLoading(true);

    try {
      const formData = new FormData();
      formData.append('file', file);

      // Use the WORKING endpoint from original
      const response = await fetch('/api/mvp/analyze', {
        method: 'POST',
        credentials: 'include', // Include session cookies
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.text();
        console.error('CSV Analysis Error:', response.status, errorData);
        throw new Error(`Failed to analyze student data (${response.status}): ${errorData}`);
      }

      const data = await response.json();
      this.displayResults(data);
    } catch (error) {
      console.error('Error analyzing data:', error);
      alert('Error analyzing student data. Please check your file format and try again.');
    } finally {
      this.showLoading(false);
    }
  }

  // EXACT REPLICA of working sample data loading
  async loadSampleData() {
    this.showLoading(true);

    try {
      const response = await fetch('/api/mvp/sample', {
        credentials: 'include'
      });
      if (!response.ok) {
        const errorData = await response.text();
        console.error('Sample Data Error:', response.status, errorData);
        throw new Error(`Failed to load sample data (${response.status}): ${errorData}`);
      }

      const data = await response.json();
      this.displayResults(data);
    } catch (error) {
      console.error('Error loading sample data:', error);
      alert('Error loading sample data. Please try again.');
    } finally {
      this.showLoading(false);
    }
  }

  // EXACT REPLICA of working result display
  displayResults(data) {
    console.log('API Response received:', data);
    
    // Ensure students array is properly set and normalized
    const students = data.students || data.predictions || [];
    
    if (students.length === 0) {
      console.error('No students found in API response');
      alert('No students found in the analysis results.');
      return;
    }
    
    console.log('Students extracted:', students);
    
    // Update application state with results
    this.appState.setState({
      students: students,
      currentTab: 'analyze'
    });
    
    // Enable analysis tab and subsequent tabs
    const tabNav = this.appState.components.get('tabNavigation');
    if (tabNav) {
      tabNav.enableTab('analyze');
      tabNav.enableTab('dashboard');
      tabNav.enableTab('insights');
    }
    
    // Show success message
    this.showNotification(`Analysis complete! Found ${students.length} students.`, 'success');
    
    // CRITICAL: Actually render the students using working pattern from app.js
    this.renderStudentsClean(students);
  }

  // EXACT WORKING METHOD FROM app.js - Simple student rendering 
  renderStudentsClean(students = null) {
    if (!students) students = this.appState.getState().students;
    if (!students || students.length === 0) {
      console.log('No students to render');
      return;
    }
    
    // Find a container - try multiple options (exact same logic as working app.js)
    let container = document.getElementById('student-list-compact');
    if (!container) {
      container = document.getElementById('student-list'); // Modern interface has this
      if (container) {
        // Make sure the container is visible (key fix!)
        container.classList.remove('hidden');
      }
    }
    if (!container) {
      container = document.getElementById('students-list'); // Backup fallback
      if (container) {
        container.classList.remove('hidden');
      }
    }
    if (!container) {
      console.error('No suitable container found for student display');
      return;
    }
    
    console.log('✅ Using container:', container.id);
    
    // Create clean HTML for each student (exact same as working app.js)
    const html = students.map(student => {
      const riskPercent = Math.round(student.risk_score * 100);
      const successPercent = Math.round(student.success_probability * 100);
      
      return `
        <div style="border: 1px solid #ddd; margin: 10px; padding: 15px; background: white; border-radius: 8px; cursor: pointer;" 
             onclick="window.modernApp.selectStudent(${student.student_id})">
          <h3>Student #${student.student_id}</h3>
          <p><strong>Risk Score:</strong> ${riskPercent}%</p>
          <p><strong>Success Probability:</strong> ${successPercent}%</p>
          <p><strong>Category:</strong> ${student.risk_category}</p>
          <p><strong>Needs Intervention:</strong> ${student.needs_intervention ? 'Yes' : 'No'}</p>
          <button onclick="event.stopPropagation(); window.modernApp.showStudentExplanation(${student.student_id})" 
                  style="background: #2563eb; color: white; border: none; padding: 8px 16px; border-radius: 4px; margin-top: 8px; cursor: pointer;">
            🔍 Explain AI Prediction
          </button>
        </div>
      `;
    }).join('');
    
    container.innerHTML = html;
    console.log('✅ Students rendered to container successfully');
  }

  // Method to handle student selection 
  selectStudent(studentId) {
    console.log('Student selected:', studentId);
    const students = this.appState.getState().students;
    const student = students.find(s => s.student_id === studentId);
    if (student) {
      this.appState.setState({ selectedStudent: student });
      alert(`Selected student #${studentId}\nRisk: ${Math.round(student.risk_score * 100)}%`);
    }
  }

  // Method to show AI explanation
  async showStudentExplanation(studentId) {
    console.log('Showing explanation for student:', studentId);
    try {
      const response = await fetch(`/api/mvp/explain/${studentId}`, {
        headers: {
          'Authorization': 'Bearer dev-key-change-me'
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to get explanation');
      }
      
      const data = await response.json();
      const explanation = data.explanation;
      
      // Show explanation in simple alert for now
      alert(`AI Explanation for Student #${studentId}:

Risk Score: ${Math.round(explanation.risk_score * 100)}%
Category: ${explanation.risk_category}
Confidence: ${Math.round(explanation.confidence * 100)}%

${explanation.explanation}`);
      
    } catch (error) {
      console.error('Error getting explanation:', error);
      alert('Failed to get AI explanation. Please try again.');
    }
  }

  startDemo() {
    this.appState.setState({ currentTab: 'dashboard' });
    this.appState.components.get('dashboard')?.startDemoMode();
  }

  showLoading(show) {
    this.appState.setState({
      ui: { 
        ...this.appState.getState().ui, 
        loading: show,
        loadingMessage: show ? 'Processing your data with AI...' : ''
      }
    });
  }

  showNotification(message, type = 'info') {
    // Create toast notification
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
      <div class="toast-content">
        <i class="fas fa-${type === 'error' ? 'exclamation-circle' : type === 'success' ? 'check-circle' : 'info-circle'}"></i>
        <span>${message}</span>
      </div>
      <button class="toast-close">&times;</button>
    `;

    document.body.appendChild(toast);

    // Auto remove after 5 seconds
    setTimeout(() => {
      toast.remove();
    }, 5000);

    // Manual close
    toast.querySelector('.toast-close').addEventListener('click', () => {
      toast.remove();
    });
  }
}

// =============================================================================
// Analysis Component - Using Working Patterns
// =============================================================================

class Analysis extends Component {
  init() {
    this.studentList = document.getElementById('student-list');
    this.studentDetail = document.getElementById('student-detail');
    this.searchInput = document.getElementById('student-search');
    this.filterButtons = document.querySelectorAll('.filter-btn');
    
    if (this.searchInput) {
      this.bindEvent(this.searchInput, 'input', this.handleSearch);
    }
    
    this.filterButtons.forEach(btn => {
      this.bindEvent(btn, 'click', this.handleFilter);
    });
    
    this.appState.subscribe('students', this.updateStudentList.bind(this));
    this.appState.subscribe('selectedStudent', this.updateStudentDetail.bind(this));
  }

  handleSearch(e) {
    const query = e.target.value.toLowerCase();
    this.filterStudents(query);
  }

  handleFilter(e) {
    const filter = e.target.dataset.filter;
    
    this.filterButtons.forEach(btn => {
      btn.classList.toggle('active', btn.dataset.filter === filter);
    });
    
    this.filterStudents('', filter);
  }

  filterStudents(query = '', riskFilter = 'all') {
    const students = this.appState.getState().students;
    
    const filtered = students.filter(student => {
      const matchesQuery = query === '' || 
        student.student_id?.toString().toLowerCase().includes(query) ||
        student.name?.toLowerCase().includes(query);
      
      const matchesRisk = riskFilter === 'all' || this.matchesRiskFilter(student, riskFilter);
      
      return matchesQuery && matchesRisk;
    });
    
    this.renderStudentList(filtered);
  }

  matchesRiskFilter(student, filter) {
    // Use the same risk calculation as the original
    const risk = student.risk_score || student.success_probability || 0;
    switch (filter) {
      case 'high': return risk >= 0.7;
      case 'medium': return risk >= 0.4 && risk < 0.7;
      case 'low': return risk < 0.4;
      default: return true;
    }
  }

  updateStudentList(students) {
    this.renderStudentList(students);
    this.updateStats(students);
  }

  renderStudentList(students) {
    if (!this.studentList) return;
    
    if (students.length === 0) {
      this.studentList.innerHTML = `
        <div class="no-students">
          <i class="fas fa-user-slash"></i>
          <p>No students found</p>
        </div>
      `;
      return;
    }
    
    const html = students.map(student => this.renderStudentCard(student)).join('');
    this.studentList.innerHTML = html;
    
    // Add click handlers
    this.studentList.querySelectorAll('.student-card').forEach(card => {
      this.bindEvent(card, 'click', (e) => {
        const studentId = e.currentTarget.dataset.studentId;
        const student = students.find(s => (s.student_id || s.id)?.toString() === studentId);
        if (student) {
          this.appState.setState({ selectedStudent: student });
        }
      });
    });
  }

  renderStudentCard(student) {
    // Handle the original data format
    const studentId = student.student_id || student.id || 'Unknown';
    const risk = student.risk_score || student.success_probability || 0;
    const riskLevel = risk >= 0.7 ? 'high' : risk >= 0.4 ? 'medium' : 'low';
    const riskColor = riskLevel === 'high' ? 'var(--danger-500)' : 
                     riskLevel === 'medium' ? 'var(--warning-500)' : 
                     'var(--success-500)';
    
    const displayName = student.name || `Student ${studentId}`;
    
    return `
      <div class="student-card" data-student-id="${studentId}">
        <div class="student-info">
          <div class="student-name">${displayName}</div>
          <div class="student-risk">
            <div class="risk-indicator" style="background-color: ${riskColor}"></div>
            <span class="risk-score">${(risk * 100).toFixed(1)}% risk</span>
          </div>
          ${student.grade_level ? `<div class="student-grade">Grade ${student.grade_level}</div>` : ''}
        </div>
        <div class="student-actions">
          <i class="fas fa-chevron-right"></i>
        </div>
      </div>
    `;
  }

  updateStudentDetail(student) {
    if (!this.studentDetail) return;
    
    if (!student) {
      this.studentDetail.innerHTML = `
        <div class="no-selection">
          <i class="fas fa-user-graduate"></i>
          <h3>Select a Student</h3>
          <p>Choose a student from the list to view detailed AI analysis, risk factors, and intervention recommendations.</p>
        </div>
      `;
      return;
    }
    
    this.renderStudentDetail(student);
  }

  renderStudentDetail(student) {
    const studentId = student.student_id || student.id || 'Unknown';
    const risk = student.risk_score || student.success_probability || 0;
    const successProb = 1 - risk;
    const riskLevel = risk >= 0.7 ? 'High Risk' : risk >= 0.4 ? 'Medium Risk' : 'Low Risk';
    const riskColor = risk >= 0.7 ? 'var(--danger-500)' : 
                     risk >= 0.4 ? 'var(--warning-500)' : 
                     'var(--success-500)';
    
    const displayName = student.name || `Student ${studentId}`;
    const needsIntervention = student.needs_intervention || risk >= 0.5;
    
    this.studentDetail.innerHTML = `
      <div class="student-detail-content">
        <div class="detail-header">
          <h3>${displayName}</h3>
          <div class="risk-badge" style="background-color: ${riskColor}">
            ${riskLevel}
          </div>
        </div>
        
        <div class="detail-stats">
          <div class="stat">
            <label>Risk Score</label>
            <value>${(risk * 100).toFixed(1)}%</value>
          </div>
          <div class="stat">
            <label>Success Probability</label>
            <value>${(successProb * 100).toFixed(1)}%</value>
          </div>
          <div class="stat">
            <label>Needs Intervention</label>
            <value>${needsIntervention ? 'Yes' : 'No'}</value>
          </div>
        </div>
        
        <div class="detail-sections">
          <div class="detail-section">
            <h4><i class="fas fa-brain"></i> AI Analysis</h4>
            <p>This student shows ${riskLevel.toLowerCase()} patterns based on machine learning analysis of academic and engagement factors.</p>
            <br>
            <button class="btn btn-primary btn-small" onclick="showExplanation('${studentId}')">
              <i class="fas fa-search-plus"></i>
              View Detailed Explanation
            </button>
          </div>
          
          <div class="detail-section">
            <h4><i class="fas fa-bullseye"></i> Recommended Actions</h4>
            <ul class="action-list">
              ${this.generateRecommendations(student).map(rec => `<li>${rec}</li>`).join('')}
            </ul>
          </div>
        </div>
      </div>
    `;
  }

  generateRecommendations(student) {
    const risk = student.risk_score || student.success_probability || 0;
    
    if (risk >= 0.7) {
      return [
        'Schedule immediate one-on-one meeting',
        'Connect with academic advisor',
        'Assess for additional support services',
        'Weekly check-ins for next 4 weeks'
      ];
    } else if (risk >= 0.4) {
      return [
        'Monitor progress closely',
        'Offer tutoring resources',
        'Bi-weekly progress meetings',
        'Encourage study group participation'
      ];
    } else {
      return [
        'Continue current support level',
        'Monthly progress check-ins',
        'Consider peer mentoring opportunities'
      ];
    }
  }

  updateStats(students) {
    const statsGrid = document.getElementById('analysis-stats');
    if (!statsGrid) return;
    
    const total = students.length;
    const highRisk = students.filter(s => (s.risk_score || s.success_probability || 0) >= 0.7).length;
    const mediumRisk = students.filter(s => {
      const risk = s.risk_score || s.success_probability || 0;
      return risk >= 0.4 && risk < 0.7;
    }).length;
    const lowRisk = students.filter(s => (s.risk_score || s.success_probability || 0) < 0.4).length;
    const needsIntervention = students.filter(s => s.needs_intervention || (s.risk_score || s.success_probability || 0) >= 0.5).length;
    
    statsGrid.innerHTML = `
      <div class="stat-card">
        <div class="stat-value">${total}</div>
        <div class="stat-label">Total Students</div>
      </div>
      <div class="stat-card stat-danger">
        <div class="stat-value">${highRisk}</div>
        <div class="stat-label">High Risk</div>
      </div>
      <div class="stat-card stat-warning">
        <div class="stat-value">${mediumRisk}</div>
        <div class="stat-label">Medium Risk</div>
      </div>
      <div class="stat-card stat-success">
        <div class="stat-value">${lowRisk}</div>
        <div class="stat-label">Low Risk</div>
      </div>
      <div class="stat-card stat-primary">
        <div class="stat-value">${needsIntervention}</div>
        <div class="stat-label">Need Intervention</div>
      </div>
    `;
  }
}

// =============================================================================
// Loading Component
// =============================================================================

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

// =============================================================================
// Application Initialization
// =============================================================================

class StudentSuccessApp {
  constructor() {
    this.appState = new AppState();
    this.components = new Map();
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
      this.appState.components = this.components;
      
      console.log('✅ Student Success App initialized');
      
    } catch (error) {
      console.error('❌ App initialization failed:', error);
    }
  }

  initializeComponents() {
    this.components.set('tabNavigation', new TabNavigation('.nav-tabs', this.appState));
    this.components.set('fileUpload', new FileUpload('#tab-upload', this.appState));
    this.components.set('analysis', new Analysis('#tab-analyze', this.appState));
    this.components.set('loading', new LoadingOverlay('#loading-overlay', this.appState));
    
    this.setupGlobalEvents();
  }

  setupGlobalEvents() {
    const modalOverlay = document.getElementById('modal-overlay');
    const modalClose = document.getElementById('modal-close');
    
    if (modalClose) {
      modalClose.addEventListener('click', () => {
        modalOverlay?.classList.add('hidden');
      });
    }
    
    if (modalOverlay) {
      modalOverlay.addEventListener('click', (e) => {
        if (e.target === modalOverlay) {
          modalOverlay.classList.add('hidden');
        }
      });
    }

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        modalOverlay?.classList.add('hidden');
      }
    });
  }

  showModal(title, content) {
    const modal = document.getElementById('modal');
    const modalTitle = document.getElementById('modal-title');
    const modalContent = document.getElementById('modal-content');
    const modalOverlay = document.getElementById('modal-overlay');
    
    if (modalTitle) modalTitle.textContent = title;
    if (modalContent) modalContent.innerHTML = content;
    if (modalOverlay) modalOverlay.classList.remove('hidden');
  }

  hideModal() {
    const modalOverlay = document.getElementById('modal-overlay');
    if (modalOverlay) modalOverlay.classList.add('hidden');
  }
}

// =============================================================================
// Global Functions - Using Working Explanation Patterns
// =============================================================================

let appInstance = null;

// Initialize app when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    appInstance = new StudentSuccessApp();
  });
} else {
  appInstance = new StudentSuccessApp();
}

// Global functions - EXACT REPLICA of working explanation system
window.showExplanation = async function(studentId) {
  if (!appInstance) return;
  
  try {
    // Show loading in modal first
    appInstance.showModal(
      `AI Explanation - Student ${studentId}`,
      '<div class="loading-content"><div class="loading-spinner"></div><p>Loading explanation...</p></div>'
    );
    
    // Use the WORKING explanation endpoint with proper auth
    const response = await fetch(`/api/mvp/explain/${studentId}`, {
      headers: {
        'Authorization': 'Bearer dev-key-change-me'
      }
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const explanation = await response.json();
    
    // Update modal with explanation
    const modalContent = document.getElementById('modal-content');
    if (modalContent) {
      modalContent.innerHTML = `
        <div class="explanation-content">
          <h4>🧠 AI Risk Analysis</h4>
          <div class="explanation-summary">
            <div class="risk-overview">
              <div class="risk-score-large">${((explanation.risk_score || 0) * 100).toFixed(1)}%</div>
              <div class="risk-label">Risk Score</div>
            </div>
            <div class="confidence-score">
              <div class="confidence-value">${((explanation.confidence || 0.5) * 100).toFixed(1)}%</div>
              <div class="confidence-label">Confidence</div>
            </div>
          </div>
          
          <div class="explanation-factors">
            <h5>🎯 Key Factors:</h5>
            <div class="explanation-text">${explanation.explanation || 'AI analysis shows this student has moderate risk based on academic performance and engagement patterns.'}</div>
          </div>
          
          <div class="explanation-actions">
            <button class="btn btn-primary" onclick="appInstance.hideModal()">Close</button>
          </div>
        </div>
      `;
    }
    
  } catch (error) {
    console.error('Failed to load explanation:', error);
    appInstance.showModal(
      'Error Loading Explanation',
      `<div class="error-content"><p>Failed to load explanation: ${error.message}</p><button class="btn btn-primary" onclick="appInstance.hideModal()">Close</button></div>`
    );
  }
};

// Integration forms - simplified working versions
window.showIntegrationForm = function(type) {
  alert(`Integration form for ${type} would be shown here. This feature connects to your LMS/SIS systems.`);
};

// Additional CSS for components
const additionalStyles = `
<style>
.toast {
  position: fixed;
  top: 20px;
  right: 20px;
  background: white;
  border: 1px solid var(--gray-200);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
  box-shadow: var(--shadow-xl);
  z-index: 200;
  max-width: 400px;
  animation: slideIn 0.3s ease-out;
}

.toast-error { border-left: 4px solid var(--danger-500); }
.toast-success { border-left: 4px solid var(--success-500); }
.toast-info { border-left: 4px solid var(--primary-500); }

.toast-content {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.toast-close {
  background: none;
  border: none;
  font-size: var(--font-size-lg);
  cursor: pointer;
  color: var(--gray-500);
  margin-left: var(--space-3);
}

@keyframes slideIn {
  from { transform: translateX(100%); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}

.drag-over {
  border-color: var(--primary-400) !important;
  background-color: var(--primary-50) !important;
}

.student-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-4);
  border: 1px solid var(--gray-200);
  border-radius: var(--radius-lg);
  margin-bottom: var(--space-3);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.student-card:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
  border-color: var(--primary-300);
}

.student-info {
  flex: 1;
}

.student-name {
  font-weight: 600;
  color: var(--gray-900);
  margin-bottom: var(--space-1);
}

.student-risk {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-1);
}

.student-grade {
  font-size: var(--font-size-xs);
  color: var(--gray-500);
}

.risk-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.risk-score {
  font-size: var(--font-size-sm);
  color: var(--gray-600);
}

.stat-card {
  background: white;
  padding: var(--space-6);
  border-radius: var(--radius-lg);
  border: 1px solid var(--gray-200);
  text-align: center;
}

.stat-value {
  font-size: var(--font-size-3xl);
  font-weight: 700;
  color: var(--gray-900);
  margin-bottom: var(--space-2);
}

.stat-label {
  color: var(--gray-600);
  font-size: var(--font-size-sm);
  font-weight: 500;
}

.stat-card.stat-danger .stat-value { color: var(--danger-500); }
.stat-card.stat-warning .stat-value { color: var(--warning-500); }
.stat-card.stat-success .stat-value { color: var(--success-500); }
.stat-card.stat-primary .stat-value { color: var(--primary-500); }

.detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-6);
}

.risk-badge {
  padding: var(--space-2) var(--space-4);
  border-radius: var(--radius-lg);
  color: white;
  font-weight: 600;
  font-size: var(--font-size-sm);
}

.detail-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: var(--space-4);
  margin-bottom: var(--space-8);
}

.stat label {
  display: block;
  font-size: var(--font-size-sm);
  color: var(--gray-600);
  margin-bottom: var(--space-1);
}

.stat value {
  font-size: var(--font-size-xl);
  font-weight: 600;
  color: var(--gray-900);
}

.detail-section {
  margin-bottom: var(--space-6);
  padding: var(--space-6);
  background: var(--gray-50);
  border-radius: var(--radius-lg);
}

.detail-section h4 {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-4);
  color: var(--gray-900);
}

.action-list {
  list-style: none;
  padding: 0;
  margin: var(--space-4) 0 0 0;
}

.action-list li {
  padding: var(--space-2) 0;
  border-bottom: 1px solid var(--gray-200);
  position: relative;
  padding-left: var(--space-6);
}

.action-list li:before {
  content: '→';
  position: absolute;
  left: 0;
  color: var(--primary-600);
  font-weight: bold;
}

.btn-small {
  padding: var(--space-2) var(--space-4);
  font-size: var(--font-size-xs);
}

.no-students {
  text-align: center;
  padding: var(--space-8);
  color: var(--gray-500);
}

.explanation-summary {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-6);
  margin-bottom: var(--space-6);
  padding: var(--space-4);
  background: var(--gray-50);
  border-radius: var(--radius-lg);
}

.risk-overview, .confidence-score {
  text-align: center;
}

.risk-score-large, .confidence-value {
  font-size: var(--font-size-3xl);
  font-weight: 700;
  color: var(--primary-600);
  margin-bottom: var(--space-1);
}

.risk-label, .confidence-label {
  font-size: var(--font-size-sm);
  color: var(--gray-600);
}

.explanation-factors {
  margin-bottom: var(--space-6);
}

.explanation-text {
  background: var(--gray-50);
  padding: var(--space-4);
  border-radius: var(--radius-md);
  border-left: 3px solid var(--primary-500);
  margin-top: var(--space-3);
}

.explanation-actions {
  display: flex;
  gap: var(--space-3);
  justify-content: center;
  margin-top: var(--space-6);
  padding-top: var(--space-6);
  border-top: 1px solid var(--gray-200);
}
</style>
`;

document.head.insertAdjacentHTML('beforeend', additionalStyles);

// Initialize the application when DOM is loaded (same pattern as working app.js)
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Initializing Modern Student Success App');
    window.modernApp = new StudentSuccessApp();
    console.log('✅ Modern app initialized and attached to window.modernApp');
});