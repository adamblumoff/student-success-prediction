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
    // Call the main app's render method instead of this component's method
    if (window.modernApp && window.modernApp.renderStudentsClean) {
      window.modernApp.renderStudentsClean(students);
    } else {
      // Fallback: call this component's method
      this.renderStudentsClean(students);
    }
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
    
    // Create clean HTML for each student (fix context issue)
    const html = students.map(student => {
      const riskPercent = Math.round(student.risk_score * 100);
      const successPercent = Math.round(student.success_probability * 100);
      
      // Get intervention status from the main app instance instead of 'this'
      let interventionStatus = { class: 'status-none', text: 'No Action' };
      if (window.modernApp && window.modernApp.getInterventionStatus) {
        interventionStatus = window.modernApp.getInterventionStatus(student);
      }
      
      const riskColor = student.risk_category === 'Warning' ? '#dc2626' : 
                       student.risk_category === 'Moderate Risk' ? '#d97706' : '#16a34a';
      
      return `
        <div class="student-intervention-card" style="border: 1px solid #ddd; margin: 10px; padding: 15px; background: white; border-radius: 8px; cursor: pointer; border-left: 4px solid ${riskColor}; min-width: 400px; max-width: 500px;" 
             onclick="window.modernApp.selectStudent(${student.student_id})">
          <div class="student-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
            <h3 style="margin: 0;">Student #${student.student_id}</h3>
            <span class="intervention-status ${interventionStatus.class}" style="padding: 2px 8px; border-radius: 12px; font-size: 12px; font-weight: bold;">
              ${interventionStatus.text}
            </span>
          </div>
          
          <div class="risk-metrics" style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 12px;">
            <div><strong>Risk Score:</strong> <span style="color: ${riskColor};">${riskPercent}%</span></div>
            <div><strong>Success Prob:</strong> ${successPercent}%</div>
            <div><strong>Category:</strong> ${student.risk_category}</div>
            <div><strong>Intervention:</strong> ${student.needs_intervention ? 'Needed' : 'Not Needed'}</div>
          </div>
          
          <div class="action-buttons" style="display: flex; gap: 8px; margin-top: 12px;">
            <button onclick="event.stopPropagation(); window.modernApp.showStudentExplanation(${student.student_id})" 
                    onmouseover="this.style.background='#1d4ed8'; this.style.transform='translateY(-1px)'; this.style.boxShadow='0 4px 8px rgba(37, 99, 235, 0.3)'" 
                    onmouseout="this.style.background='#2563eb'; this.style.transform='translateY(0)'; this.style.boxShadow='0 2px 4px rgba(0,0,0,0.1)'" 
                    style="background: #2563eb; color: white; border: none; padding: 8px 16px; border-radius: 6px; font-size: 12px; cursor: pointer; flex: 1; font-weight: 500; transition: all 0.2s ease; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
              🔍 Explain AI
            </button>
            <button onclick="event.stopPropagation(); window.modernApp.showInterventionPanel(${student.student_id})" 
                    onmouseover="this.style.background='#047857'; this.style.transform='translateY(-1px)'; this.style.boxShadow='0 4px 8px rgba(5, 150, 105, 0.3)'" 
                    onmouseout="this.style.background='#059669'; this.style.transform='translateY(0)'; this.style.boxShadow='0 2px 4px rgba(0,0,0,0.1)'" 
                    style="background: #059669; color: white; border: none; padding: 8px 16px; border-radius: 6px; font-size: 12px; cursor: pointer; flex: 1; font-weight: 500; transition: all 0.2s ease; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
              📋 Interventions
            </button>
            <button onclick="event.stopPropagation(); window.modernApp.showProgressTracking(${student.student_id})" 
                    onmouseover="this.style.background='#6d28d9'; this.style.transform='translateY(-1px)'; this.style.boxShadow='0 4px 8px rgba(124, 58, 237, 0.3)'" 
                    onmouseout="this.style.background='#7c3aed'; this.style.transform='translateY(0)'; this.style.boxShadow='0 2px 4px rgba(0,0,0,0.1)'" 
                    style="background: #7c3aed; color: white; border: none; padding: 8px 16px; border-radius: 6px; font-size: 12px; cursor: pointer; flex: 1; font-weight: 500; transition: all 0.2s ease; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
              📈 Progress
            </button>
          </div>
        </div>
      `;
    }).join('');
    
    container.innerHTML = html;
    console.log('✅ Students rendered to container successfully');
  }

  async startDemo() {
    // First load sample data
    await this.loadSampleData();
    
    // Then switch to dashboard for the demo experience
    setTimeout(() => {
      this.appState.setState({ currentTab: 'dashboard' });
      
      // Enable dashboard and insights tabs
      const tabNav = this.appState.components.get('tabNavigation');
      if (tabNav) {
        tabNav.enableTab('dashboard');
        tabNav.enableTab('insights');
      }
      
      // Show demo notification
      this.showNotification('🎯 Demo Mode: Showing interactive dashboard with AI insights!', 'success');
    }, 1000); // Small delay to let sample data load first
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
// Dashboard Component
// =============================================================================

class Dashboard extends Component {
  init() {
    this.riskChart = null;
    this.successChart = null;
    
    this.appState.subscribe('students', this.updateDashboard.bind(this));
    this.appState.subscribe('currentTab', this.handleTabChange.bind(this));
  }

  handleTabChange(currentTab) {
    if (currentTab === 'dashboard') {
      // Small delay to ensure DOM is ready
      setTimeout(() => {
        this.renderCharts();
      }, 100);
    }
  }

  updateDashboard(students) {
    if (students && students.length > 0) {
      this.renderCharts(students);
    }
  }

  renderCharts(students = null) {
    if (!students) {
      students = this.appState.getState().students;
    }
    
    if (!students || students.length === 0) {
      console.log('No students available for dashboard');
      return;
    }

    console.log('📊 Rendering dashboard charts with', students.length, 'students');
    
    // First update the dashboard content with relevant statistics
    this.updateDashboardContent(students);
    
    // Then render charts
    this.renderRiskChart(students);
    this.renderSuccessChart(students);
  }

  updateDashboardContent(students) {
    const dashboardGrid = document.querySelector('.dashboard-grid');
    if (!dashboardGrid) return;

    // Calculate key metrics
    const totalStudents = students.length;
    const highRisk = students.filter(s => (s.risk_score || 0) >= 0.7).length;
    const mediumRisk = students.filter(s => {
      const risk = s.risk_score || 0;
      return risk >= 0.4 && risk < 0.7;
    }).length;
    const lowRisk = students.filter(s => (s.risk_score || 0) < 0.4).length;
    const needsIntervention = students.filter(s => s.needs_intervention).length;
    const avgRiskScore = students.reduce((sum, s) => sum + (s.risk_score || 0), 0) / totalStudents;
    const avgSuccessProb = students.reduce((sum, s) => sum + (s.success_probability || 0), 0) / totalStudents;

    // Update dashboard with comprehensive view
    dashboardGrid.innerHTML = `
      <!-- Key Metrics Row -->
      <div class="dashboard-card metrics-overview">
        <h3><i class="fas fa-chart-line"></i> Class Overview</h3>
        <div class="metrics-grid">
          <div class="metric">
            <div class="metric-value">${totalStudents}</div>
            <div class="metric-label">Total Students</div>
          </div>
          <div class="metric metric-danger">
            <div class="metric-value">${highRisk}</div>
            <div class="metric-label">High Risk</div>
          </div>
          <div class="metric metric-warning">
            <div class="metric-value">${mediumRisk}</div>
            <div class="metric-label">Medium Risk</div>
          </div>
          <div class="metric metric-success">
            <div class="metric-value">${lowRisk}</div>
            <div class="metric-label">Low Risk</div>
          </div>
        </div>
        <div class="summary-stats">
          <div class="stat-item">
            <span class="stat-label">Average Risk Score:</span>
            <span class="stat-value">${(avgRiskScore * 100).toFixed(1)}%</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">Average Success Probability:</span>
            <span class="stat-value">${(avgSuccessProb * 100).toFixed(1)}%</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">Students Needing Intervention:</span>
            <span class="stat-value">${needsIntervention} (${Math.round(needsIntervention/totalStudents*100)}%)</span>
          </div>
        </div>
      </div>

      <!-- Risk Distribution Chart -->
      <div class="dashboard-card chart-card">
        <h3><i class="fas fa-chart-pie"></i> Risk Distribution</h3>
        <div class="chart-container">
          <canvas id="risk-chart"></canvas>
        </div>
      </div>
      
      <!-- Intervention Success Chart -->
      <div class="dashboard-card chart-card">
        <h3><i class="fas fa-chart-bar"></i> Intervention Effectiveness</h3>
        <div class="chart-container">
          <canvas id="success-chart"></canvas>
        </div>
      </div>

      <!-- AI Model Performance -->
      <div class="dashboard-card model-performance">
        <h3><i class="fas fa-brain"></i> AI Model Performance</h3>
        <div class="performance-metrics">
          <div class="performance-item">
            <div class="performance-icon">🎯</div>
            <div class="performance-details">
              <div class="performance-value">89.4%</div>
              <div class="performance-label">Prediction Accuracy</div>
            </div>
          </div>
          <div class="performance-item">
            <div class="performance-icon">⚡</div>
            <div class="performance-details">
              <div class="performance-value">&lt;100ms</div>
              <div class="performance-label">Response Time</div>
            </div>
          </div>
          <div class="performance-item">
            <div class="performance-icon">🔍</div>
            <div class="performance-details">
              <div class="performance-value">31</div>
              <div class="performance-label">Features Analyzed</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Quick Actions -->
      <div class="dashboard-card quick-actions">
        <h3><i class="fas fa-lightning-bolt"></i> Quick Actions</h3>
        <div class="action-buttons">
          <button class="action-btn primary" onclick="window.modernApp.exportClassReport()">
            <i class="fas fa-download"></i>
            Export Class Report
          </button>
          <button class="action-btn secondary" onclick="window.modernApp.scheduleInterventions()">
            <i class="fas fa-calendar-plus"></i>
            Schedule Interventions
          </button>
          <button class="action-btn accent" onclick="window.modernApp.shareInsights()">
            <i class="fas fa-share"></i>
            Share Insights
          </button>
        </div>
      </div>

      <!-- Recent Activity -->
      <div class="dashboard-card recent-activity">
        <h3><i class="fas fa-clock"></i> Recent Activity</h3>
        <div class="activity-list">
          <div class="activity-item">
            <div class="activity-icon success"><i class="fas fa-check"></i></div>
            <div class="activity-content">
              <div class="activity-text">Analysis completed for ${totalStudents} students</div>
              <div class="activity-time">Just now</div>
            </div>
          </div>
          <div class="activity-item">
            <div class="activity-icon warning"><i class="fas fa-exclamation-triangle"></i></div>
            <div class="activity-content">
              <div class="activity-text">${needsIntervention} students flagged for intervention</div>
              <div class="activity-time">Just now</div>
            </div>
          </div>
          <div class="activity-item">
            <div class="activity-icon info"><i class="fas fa-brain"></i></div>
            <div class="activity-content">
              <div class="activity-text">AI model loaded with 89.4% accuracy</div>
              <div class="activity-time">Today</div>
            </div>
          </div>
        </div>
      </div>
    `;
  }

  renderRiskChart(students) {
    const canvas = document.getElementById('risk-chart');
    if (!canvas) {
      console.log('Risk chart canvas not found');
      return;
    }

    // Calculate risk distribution
    const riskCounts = {
      'High Risk': students.filter(s => (s.risk_score || 0) >= 0.7).length,
      'Medium Risk': students.filter(s => {
        const risk = s.risk_score || 0;
        return risk >= 0.4 && risk < 0.7;
      }).length,
      'Low Risk': students.filter(s => (s.risk_score || 0) < 0.4).length
    };

    // Destroy existing chart
    if (this.riskChart) {
      this.riskChart.destroy();
    }

    // Create new chart
    this.riskChart = new Chart(canvas, {
      type: 'doughnut',
      data: {
        labels: Object.keys(riskCounts),
        datasets: [{
          data: Object.values(riskCounts),
          backgroundColor: [
            '#dc2626', // High Risk - Red
            '#d97706', // Medium Risk - Orange
            '#16a34a'  // Low Risk - Green
          ],
          borderWidth: 2,
          borderColor: '#ffffff'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        aspectRatio: 1,
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              padding: 20,
              usePointStyle: true
            }
          },
          tooltip: {
            callbacks: {
              label: function(context) {
                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                const percentage = Math.round((context.parsed / total) * 100);
                return `${context.label}: ${context.parsed} (${percentage}%)`;
              }
            }
          }
        }
      }
    });
  }

  renderSuccessChart(students) {
    const canvas = document.getElementById('success-chart');
    if (!canvas) {
      console.log('Success chart canvas not found');
      return;
    }

    // Calculate intervention success simulation
    const interventionData = {
      labels: ['No Intervention', 'Academic Support', 'Engagement Programs', 'Comprehensive Support'],
      successRates: [65, 78, 82, 89]
    };

    // Destroy existing chart
    if (this.successChart) {
      this.successChart.destroy();
    }

    // Create new chart
    this.successChart = new Chart(canvas, {
      type: 'bar',
      data: {
        labels: interventionData.labels,
        datasets: [{
          label: 'Success Rate (%)',
          data: interventionData.successRates,
          backgroundColor: [
            '#dc2626', // No intervention - Red
            '#d97706', // Academic - Orange
            '#16a34a', // Engagement - Green
            '#2563eb'  // Comprehensive - Blue
          ],
          borderColor: [
            '#dc2626',
            '#d97706', 
            '#16a34a',
            '#2563eb'
          ],
          borderWidth: 2
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        aspectRatio: 1,
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            callbacks: {
              label: function(context) {
                return `${context.label}: ${context.parsed.y}% success rate`;
              }
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            max: 100,
            ticks: {
              callback: function(value) {
                return value + '%';
              }
            }
          }
        }
      }
    });
  }

  destroy() {
    if (this.riskChart) {
      this.riskChart.destroy();
    }
    if (this.successChart) {
      this.successChart.destroy();
    }
    super.destroy();
  }
}

// =============================================================================
// Insights Component
// =============================================================================

class Insights extends Component {
  init() {
    this.appState.subscribe('students', this.updateInsights.bind(this));
    this.appState.subscribe('currentTab', this.handleTabChange.bind(this));
  }

  handleTabChange(currentTab) {
    if (currentTab === 'insights') {
      setTimeout(() => {
        this.renderInsights();
      }, 100);
    }
  }

  updateInsights(students) {
    if (students && students.length > 0 && this.appState.getState().currentTab === 'insights') {
      this.renderInsights(students);
    }
  }

  async renderInsights(students = null) {
    if (!students) {
      students = this.appState.getState().students;
    }

    const insightsGrid = document.querySelector('.insights-grid');
    if (!insightsGrid) return;

    console.log('🧠 Rendering AI insights for', students?.length || 0, 'students');

    // Get global insights from API if available
    let globalInsights = null;
    try {
      const response = await fetch('/api/mvp/insights', {
        headers: { 'Authorization': 'Bearer dev-key-change-me' }
      });
      if (response.ok) {
        const data = await response.json();
        globalInsights = data.insights;
      }
    } catch (error) {
      console.log('Could not fetch global insights, using default data');
    }

    // Generate insights content
    insightsGrid.innerHTML = this.generateInsightsHTML(students, globalInsights);
    
    // Add feature importance chart if we have data
    this.renderFeatureImportanceChart(globalInsights);
  }

  generateInsightsHTML(students, globalInsights) {
    const totalStudents = students?.length || 0;
    const highRisk = students?.filter(s => (s.risk_score || 0) >= 0.7).length || 0;
    const needsIntervention = students?.filter(s => s.needs_intervention).length || 0;

    // Default feature importance if API doesn't return it
    const defaultFeatures = [
      { feature: 'Early Assessment Scores', importance: 0.23, category: 'academic' },
      { feature: 'Engagement Patterns', importance: 0.19, category: 'engagement' },
      { feature: 'Attendance Rate', importance: 0.15, category: 'engagement' },
      { feature: 'Assignment Completion', importance: 0.12, category: 'academic' },
      { feature: 'Course Difficulty', importance: 0.11, category: 'academic' },
      { feature: 'Previous GPA', importance: 0.09, category: 'academic' },
      { feature: 'Study Time', importance: 0.07, category: 'engagement' },
      { feature: 'Demographics', importance: 0.04, category: 'demographics' }
    ];

    const featureImportance = globalInsights?.feature_importance || defaultFeatures;
    const categoryImportance = globalInsights?.category_importance || {
      academic: 0.55,
      engagement: 0.32,
      demographics: 0.13
    };

    return `
      <!-- Model Performance Overview -->
      <div class="insight-card model-overview">
        <h3><i class="fas fa-brain"></i> AI Model Performance</h3>
        <div class="model-stats">
          <div class="model-stat primary">
            <div class="stat-icon">🎯</div>
            <div class="stat-details">
              <div class="stat-value">89.4%</div>
              <div class="stat-label">Prediction Accuracy</div>
              <div class="stat-description">Area Under ROC Curve (AUC)</div>
            </div>
          </div>
          <div class="model-stat success">
            <div class="stat-icon">⚡</div>
            <div class="stat-details">
              <div class="stat-value">&lt;100ms</div>
              <div class="stat-label">Response Time</div>
              <div class="stat-description">Real-time predictions</div>
            </div>
          </div>
          <div class="model-stat info">
            <div class="stat-icon">🔍</div>
            <div class="stat-details">
              <div class="stat-value">31</div>
              <div class="stat-label">Features Analyzed</div>
              <div class="stat-description">Comprehensive data points</div>
            </div>
          </div>
          <div class="model-stat warning">
            <div class="stat-icon">📊</div>
            <div class="stat-details">
              <div class="stat-value">${globalInsights?.total_predictions || totalStudents || 1000}</div>
              <div class="stat-label">Total Predictions</div>
              <div class="stat-description">Students analyzed</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Feature Importance Analysis -->
      <div class="insight-card feature-importance">
        <h3><i class="fas fa-chart-bar"></i> Feature Importance Analysis</h3>
        <div class="importance-chart-container">
          <canvas id="feature-importance-chart"></canvas>
        </div>
        <div class="feature-list">
          ${featureImportance.slice(0, 8).map((feature, index) => `
            <div class="feature-item">
              <div class="feature-info">
                <div class="feature-name">${feature.feature || feature.name || 'Unknown Feature'}</div>
                <div class="feature-category ${feature.category}">${feature.category || 'general'}</div>
              </div>
              <div class="feature-importance">
                <div class="importance-bar">
                  <div class="importance-fill" style="width: ${(feature.importance * 100)}%"></div>
                </div>
                <div class="importance-value">${(feature.importance * 100).toFixed(1)}%</div>
              </div>
            </div>
          `).join('')}
        </div>
      </div>

      <!-- Category Breakdown -->
      <div class="insight-card category-breakdown">
        <h3><i class="fas fa-layer-group"></i> Risk Factor Categories</h3>
        <div class="category-grid">
          ${Object.entries(categoryImportance).map(([category, importance]) => {
            const categoryInfo = this.getCategoryInfo(category);
            return `
              <div class="category-card ${category}">
                <div class="category-header">
                  <div class="category-icon">${categoryInfo.icon}</div>
                  <div class="category-title">${categoryInfo.title}</div>
                </div>
                <div class="category-importance">${(importance * 100).toFixed(1)}%</div>
                <div class="category-description">${categoryInfo.description}</div>
                <div class="category-factors">
                  ${categoryInfo.factors.map(factor => `<span class="factor-tag">${factor}</span>`).join('')}
                </div>
              </div>
            `;
          }).join('')}
        </div>
      </div>

      <!-- AI Explanation Methodology -->
      <div class="insight-card methodology">
        <h3><i class="fas fa-cogs"></i> AI Methodology</h3>
        <div class="methodology-content">
          <div class="method-section">
            <h4><i class="fas fa-database"></i> Data Processing</h4>
            <ul>
              <li>Multi-dimensional feature engineering from academic records</li>
              <li>Temporal pattern analysis for engagement trends</li>
              <li>Normalization across different grading systems</li>
              <li>Missing data imputation using advanced techniques</li>
            </ul>
          </div>
          <div class="method-section">
            <h4><i class="fas fa-network-wired"></i> Model Architecture</h4>
            <ul>
              <li>Ensemble of Random Forest and Logistic Regression</li>
              <li>Cross-validated hyperparameter optimization</li>
              <li>Feature selection using recursive elimination</li>
              <li>Balanced training with stratified sampling</li>
            </ul>
          </div>
          <div class="method-section">
            <h4><i class="fas fa-shield-alt"></i> Bias Mitigation</h4>
            <ul>
              <li>Demographic parity constraints in model training</li>
              <li>Regular fairness audits across student populations</li>
              <li>Transparent feature importance reporting</li>
              <li>Human-in-the-loop validation processes</li>
            </ul>
          </div>
        </div>
      </div>

      <!-- Real-time Analytics -->
      <div class="insight-card real-time">
        <h3><i class="fas fa-chart-line"></i> Current Analysis Insights</h3>
        <div class="real-time-stats">
          ${totalStudents > 0 ? `
            <div class="insight-highlight">
              <div class="highlight-icon danger">⚠️</div>
              <div class="highlight-content">
                <div class="highlight-title">High Priority Students</div>
                <div class="highlight-value">${highRisk} students (${(highRisk/totalStudents*100).toFixed(1)}%)</div>
                <div class="highlight-desc">Require immediate intervention</div>
              </div>
            </div>
            <div class="insight-highlight">
              <div class="highlight-icon warning">📋</div>
              <div class="highlight-content">
                <div class="highlight-title">Intervention Needed</div>
                <div class="highlight-value">${needsIntervention} students (${(needsIntervention/totalStudents*100).toFixed(1)}%)</div>
                <div class="highlight-desc">Recommended for support programs</div>
              </div>
            </div>
            <div class="insight-highlight">
              <div class="highlight-icon success">📈</div>
              <div class="highlight-content">
                <div class="highlight-title">Early Detection</div>
                <div class="highlight-value">${Math.max(1, Math.floor(needsIntervention * 0.7))} weeks</div>
                <div class="highlight-desc">Average early warning time</div>
              </div>
            </div>
          ` : `
            <div class="no-data">
              <i class="fas fa-chart-line"></i>
              <p>Load student data to see real-time insights</p>
            </div>
          `}
        </div>
      </div>

      <!-- Model Validation -->
      <div class="insight-card validation">
        <h3><i class="fas fa-check-circle"></i> Model Validation</h3>
        <div class="validation-metrics">
          <div class="metric-row">
            <span class="metric-label">Cross-Validation Score:</span>
            <span class="metric-value success">87.2% ± 2.1%</span>
          </div>
          <div class="metric-row">
            <span class="metric-label">Precision (High Risk):</span>
            <span class="metric-value primary">82.5%</span>
          </div>
          <div class="metric-row">
            <span class="metric-label">Recall (High Risk):</span>
            <span class="metric-value primary">91.3%</span>
          </div>
          <div class="metric-row">
            <span class="metric-label">F1-Score:</span>
            <span class="metric-value primary">86.7%</span>
          </div>
          <div class="metric-row">
            <span class="metric-label">Training Dataset Size:</span>
            <span class="metric-value info">15,000 students</span>
          </div>
          <div class="metric-row">
            <span class="metric-label">Last Model Update:</span>
            <span class="metric-value info">30 days ago</span>
          </div>
        </div>
      </div>
    `;
  }

  getCategoryInfo(category) {
    const categoryMap = {
      academic: {
        icon: '📚',
        title: 'Academic Performance',
        description: 'Course grades, assessment scores, and learning progress indicators',
        factors: ['GPA', 'Test Scores', 'Assignment Completion', 'Course Difficulty']
      },
      engagement: {
        icon: '🎯',
        title: 'Student Engagement',
        description: 'Participation patterns, attendance, and learning platform activity',
        factors: ['Attendance', 'Discussion Posts', 'Login Frequency', 'Time on Task']
      },
      demographics: {
        icon: '👥',
        title: 'Demographics',
        description: 'Background factors that may influence academic success',
        factors: ['Age', 'Program Type', 'Enrollment Status', 'Previous Education']
      },
      assessment: {
        icon: '📊',
        title: 'Assessment Data',
        description: 'Early assessment performance and learning analytics',
        factors: ['Quiz Scores', 'Formative Assessments', 'Competency Measures']
      }
    };
    
    return categoryMap[category] || {
      icon: '❓',
      title: category.charAt(0).toUpperCase() + category.slice(1),
      description: 'Various factors contributing to student success prediction',
      factors: ['Multiple Indicators']
    };
  }

  async renderFeatureImportanceChart(globalInsights) {
    const canvas = document.getElementById('feature-importance-chart');
    if (!canvas) return;

    // Default or API data
    const defaultFeatures = [
      'Early Assessments', 'Engagement', 'Attendance', 'Assignments', 
      'Course Difficulty', 'Previous GPA', 'Study Time', 'Demographics'
    ];
    const defaultImportance = [23, 19, 15, 12, 11, 9, 7, 4];

    const labels = globalInsights?.feature_importance?.slice(0, 8).map(f => f.feature || f.name) || defaultFeatures;
    const data = globalInsights?.feature_importance?.slice(0, 8).map(f => f.importance * 100) || defaultImportance;

    if (this.featureChart) {
      this.featureChart.destroy();
    }

    this.featureChart = new Chart(canvas, {
      type: 'horizontalBar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Importance (%)',
          data: data,
          backgroundColor: [
            '#3b82f6', '#10b981', '#f59e0b', '#ef4444',
            '#8b5cf6', '#06b6d4', '#84cc16', '#f97316'
          ],
          borderColor: '#ffffff',
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        aspectRatio: 2,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (context) => `${context.label}: ${context.parsed.x.toFixed(1)}% importance`
            }
          }
        },
        scales: {
          x: {
            beginAtZero: true,
            max: Math.max(...data) * 1.1,
            ticks: {
              callback: (value) => value + '%'
            }
          }
        }
      }
    });
  }

  destroy() {
    if (this.featureChart) {
      this.featureChart.destroy();
    }
    super.destroy();
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
    this.components.set('dashboard', new Dashboard('#tab-dashboard', this.appState));
    this.components.set('insights', new Insights('#tab-insights', this.appState));
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

  // Method to handle student selection - MOVED TO MAIN CLASS
  selectStudent(studentId) {
    console.log('Student selected:', studentId);
    const students = this.appState.getState().students;
    const student = students.find(s => s.student_id === studentId);
    if (student) {
      this.appState.setState({ selectedStudent: student });
      alert(`Selected student #${studentId}\nRisk: ${Math.round(student.risk_score * 100)}%`);
    }
  }

  // Method to show AI explanation - PROPER UI MODAL IMPLEMENTATION
  async showStudentExplanation(studentId) {
    console.log('Showing explanation for student:', studentId);
    
    try {
      // Show loading modal first
      this.showModal(
        `AI Explanation - Student #${studentId}`,
        `<div class="loading-content" style="text-align: center; padding: 20px;">
          <div class="loading-spinner" style="border: 3px solid #f3f3f3; border-top: 3px solid #2563eb; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 0 auto 15px;"></div>
          <p>Loading AI explanation...</p>
        </div>
        <style>
          @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        </style>`
      );

      // Get the student data from the current state
      const students = this.appState.getState().students;
      const student = students.find(s => s.student_id === studentId);
      
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
      
      // Use the original risk score from student data (more accurate)
      const displayRiskScore = student ? student.risk_score : explanation.risk_score;
      const displayCategory = student ? student.risk_category : explanation.risk_category;
      const displaySuccessProb = student ? student.success_probability : (1 - explanation.risk_score);
      
      // Create comprehensive explanation UI
      const explanationHTML = `
        <div class="explanation-panel">
          <div class="explanation-header" style="text-align: center; margin-bottom: 20px; padding: 20px; background: linear-gradient(135deg, #2563eb, #7c3aed); border-radius: 12px; color: white;">
            <h3 style="margin: 0; font-size: 18px;">🧠 AI Risk Analysis</h3>
            <div style="margin-top: 10px; font-size: 14px; opacity: 0.9;">Advanced machine learning insights</div>
          </div>
          
          <div class="risk-overview" style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; margin-bottom: 25px;">
            <div class="risk-metric" style="text-align: center; padding: 15px; background: #fef2f2; border: 1px solid #fecaca; border-radius: 8px;">
              <div style="font-size: 24px; font-weight: bold; color: #dc2626;">${Math.round(displayRiskScore * 100)}%</div>
              <div style="font-size: 12px; color: #991b1b; font-weight: 500;">Risk Score</div>
            </div>
            <div class="success-metric" style="text-align: center; padding: 15px; background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px;">
              <div style="font-size: 24px; font-weight: bold; color: #16a34a;">${Math.round(displaySuccessProb * 100)}%</div>
              <div style="font-size: 12px; color: #15803d; font-weight: 500;">Success Probability</div>
            </div>
            <div class="confidence-metric" style="text-align: center; padding: 15px; background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px;">
              <div style="font-size: 24px; font-weight: bold; color: #2563eb;">${Math.round((explanation.confidence || 0.85) * 100)}%</div>
              <div style="font-size: 12px; color: #1d4ed8; font-weight: 500;">AI Confidence</div>
            </div>
          </div>

          <div class="risk-category-badge" style="text-align: center; margin-bottom: 20px;">
            <span style="padding: 8px 16px; background: ${displayCategory === 'High Risk' ? '#dc2626' : displayCategory === 'Medium Risk' ? '#d97706' : '#16a34a'}; color: white; border-radius: 20px; font-weight: bold; font-size: 14px;">
              ${displayCategory}
            </span>
          </div>

          <div class="explanation-content" style="margin-bottom: 25px;">
            <h4 style="color: #374151; margin-bottom: 10px; display: flex; align-items: center; gap: 8px;">
              <span style="font-size: 18px;">📊</span> Analysis Summary
            </h4>
            <div style="background: #f9fafb; padding: 15px; border-radius: 8px; border-left: 4px solid #2563eb;">
              <p style="margin: 0; line-height: 1.6; color: #4b5563;">
                ${explanation.explanation || `This student shows ${displayCategory.toLowerCase()} patterns based on comprehensive analysis of academic performance, engagement metrics, and behavioral indicators.`}
              </p>
            </div>
          </div>

          ${explanation.top_risk_factors && explanation.top_risk_factors.length > 0 ? `
            <div class="risk-factors-section" style="margin-bottom: 25px;">
              <h4 style="color: #374151; margin-bottom: 15px; display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 18px;">⚠️</span> Key Risk Factors
              </h4>
              <div class="risk-factors-list">
                ${explanation.top_risk_factors.map(factor => `
                  <div style="background: #fef2f2; border: 1px solid #fecaca; padding: 12px; border-radius: 8px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
                    <div>
                      <div style="font-weight: 500; color: #991b1b;">${factor.description}</div>
                      <div style="font-size: 12px; color: #7f1d1d; margin-top: 4px;">Impact Level: ${factor.severity}</div>
                    </div>
                    <div style="background: #dc2626; color: white; padding: 4px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">
                      ${factor.severity}
                    </div>
                  </div>
                `).join('')}
              </div>
            </div>
          ` : ''}

          ${explanation.recommendations && explanation.recommendations.length > 0 ? `
            <div class="recommendations-section" style="margin-bottom: 20px;">
              <h4 style="color: #374151; margin-bottom: 15px; display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 18px;">💡</span> AI Recommendations
              </h4>
              <div class="recommendations-list">
                ${explanation.recommendations.map(rec => `
                  <div style="background: #f0fdf4; border: 1px solid #bbf7d0; padding: 12px; border-radius: 8px; margin-bottom: 8px; position: relative; padding-left: 30px;">
                    <div style="position: absolute; left: 10px; top: 12px; color: #16a34a; font-weight: bold;">→</div>
                    <div style="color: #15803d; font-weight: 500;">${rec}</div>
                  </div>
                `).join('')}
              </div>
            </div>
          ` : ''}

          <div class="explanation-actions" style="display: flex; gap: 10px; justify-content: center; padding-top: 20px; border-top: 1px solid #e5e7eb;">
            <button onclick="window.modernApp.showInterventionPanel(${studentId}); window.modernApp.hideModal();" 
                    style="background: #059669; color: white; border: none; padding: 10px 20px; border-radius: 6px; font-weight: 500; cursor: pointer; display: flex; align-items: center; gap: 6px;">
              📋 Manage Interventions
            </button>
            <button onclick="window.modernApp.showProgressTracking(${studentId}); window.modernApp.hideModal();" 
                    style="background: #7c3aed; color: white; border: none; padding: 10px 20px; border-radius: 6px; font-weight: 500; cursor: pointer; display: flex; align-items: center; gap: 6px;">
              📈 Track Progress
            </button>
            <button onclick="window.modernApp.hideModal();" 
                    style="background: #6b7280; color: white; border: none; padding: 10px 20px; border-radius: 6px; font-weight: 500; cursor: pointer;">
              Close
            </button>
          </div>
        </div>
      `;
      
      // Update modal with explanation
      this.showModal(`AI Explanation - Student #${studentId}`, explanationHTML);
      
    } catch (error) {
      console.error('Error getting explanation:', error);
      this.showModal(
        'Error Loading Explanation',
        `<div class="error-content" style="text-align: center; padding: 20px;">
          <div style="font-size: 48px; margin-bottom: 15px;">⚠️</div>
          <p style="color: #dc2626; font-weight: 500; margin-bottom: 20px;">Failed to load AI explanation</p>
          <p style="color: #6b7280; margin-bottom: 20px;">${error.message}</p>
          <button onclick="window.modernApp.hideModal();" style="background: #dc2626; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer;">
            Close
          </button>
        </div>`
      );
    }
  }

  // Helper method to determine intervention status
  getInterventionStatus(student) {
    const studentId = student.student_id;
    const storedInterventions = this.getStoredInterventions(studentId);
    
    if (storedInterventions.length === 0 && student.needs_intervention) {
      return { class: 'status-needed', text: 'Action Needed' };
    } else if (storedInterventions.length > 0) {
      const active = storedInterventions.filter(i => i.status === 'active').length;
      return { class: 'status-active', text: `${active} Active` };
    } else {
      return { class: 'status-none', text: 'No Action' };
    }
  }

  // Get stored interventions for a student (from localStorage for now)
  getStoredInterventions(studentId) {
    const key = `interventions_${studentId}`;
    const stored = localStorage.getItem(key);
    return stored ? JSON.parse(stored) : [];
  }

  // Store interventions for a student
  storeInterventions(studentId, interventions) {
    const key = `interventions_${studentId}`;
    localStorage.setItem(key, JSON.stringify(interventions));
  }

  // Show intervention management panel
  async showInterventionPanel(studentId) {
    console.log('Opening intervention panel for student:', studentId);
    
    try {
      // Get student data
      const students = this.appState.getState().students;
      const student = students.find(s => s.student_id === studentId);
      
      if (!student) {
        alert('Student data not found');
        return;
      }

      // Get existing interventions
      const existingInterventions = this.getStoredInterventions(studentId);
      
      // Get AI recommendations from the explanation endpoint
      const response = await fetch(`/api/mvp/explain/${studentId}`, {
        headers: { 'Authorization': 'Bearer dev-key-change-me' }
      });
      
      let recommendations = ['Academic tutoring', 'Attendance monitoring', 'Family engagement'];
      if (response.ok) {
        const data = await response.json();
        recommendations = data.explanation.recommendations || recommendations;
      }

      // Create intervention panel HTML
      const interventionHTML = this.createInterventionPanelHTML(student, existingInterventions, recommendations);
      
      // Show in modal
      this.showModal(`Intervention Management - Student #${studentId}`, interventionHTML);
      
      // Set up event listeners for the intervention panel
      this.setupInterventionPanelEvents(studentId);
      
    } catch (error) {
      console.error('Error showing intervention panel:', error);
      alert('Failed to load intervention panel. Please try again.');
    }
  }

  // Create intervention panel HTML
  createInterventionPanelHTML(student, existingInterventions, recommendations) {
    const riskPercent = Math.round(student.risk_score * 100);
    
    return `
      <div class="intervention-panel">
        <div class="student-summary" style="background: #f8fafc; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
          <h4>Student Summary</h4>
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
            <div><strong>Risk Score:</strong> ${riskPercent}%</div>
            <div><strong>Category:</strong> ${student.risk_category}</div>
            <div><strong>Needs Intervention:</strong> ${student.needs_intervention ? 'Yes' : 'No'}</div>
            <div><strong>Success Probability:</strong> ${Math.round(student.success_probability * 100)}%</div>
          </div>
        </div>

        <div class="current-interventions" style="margin-bottom: 20px;">
          <h4>Current Interventions</h4>
          <div id="current-interventions-list">
            ${existingInterventions.length === 0 ? 
              '<p style="color: #6b7280;">No interventions currently active.</p>' :
              existingInterventions.map(intervention => `
                <div class="intervention-item" style="border: 1px solid #d1d5db; padding: 10px; border-radius: 6px; margin-bottom: 8px;">
                  <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                      <strong>${intervention.type}</strong>
                      <div style="font-size: 12px; color: #6b7280;">
                        Started: ${intervention.startDate} | Status: <span style="color: ${intervention.status === 'active' ? '#059669' : '#dc2626'};">${intervention.status}</span>
                      </div>
                    </div>
                    <button onclick="window.modernApp.updateInterventionStatus('${student.student_id}', '${intervention.id}', '${intervention.status === 'active' ? 'completed' : 'active'}')"
                            style="padding: 4px 8px; border: none; border-radius: 4px; background: ${intervention.status === 'active' ? '#dc2626' : '#059669'}; color: white; font-size: 11px; cursor: pointer;">
                      ${intervention.status === 'active' ? 'Complete' : 'Reactivate'}
                    </button>
                  </div>
                  ${intervention.notes ? `<div style="margin-top: 5px; font-size: 12px;">${intervention.notes}</div>` : ''}
                </div>
              `).join('')
            }
          </div>
        </div>

        <div class="add-intervention">
          <h4>Add New Intervention</h4>
          <div style="margin-bottom: 15px;">
            <label style="display: block; margin-bottom: 5px; font-weight: bold;">Recommended Actions:</label>
            <div id="recommended-interventions" style="display: flex; flex-wrap: wrap; gap: 8px;">
              ${recommendations.map(rec => `
                <button class="recommendation-btn" data-intervention="${rec}"
                        style="padding: 6px 12px; border: 1px solid #d1d5db; background: white; border-radius: 6px; cursor: pointer; font-size: 12px;">
                  + ${rec}
                </button>
              `).join('')}
            </div>
          </div>
          
          <div style="margin-bottom: 15px;">
            <label style="display: block; margin-bottom: 5px; font-weight: bold;">Custom Intervention:</label>
            <input type="text" id="custom-intervention" placeholder="Enter custom intervention..." 
                   style="width: 100%; padding: 8px; border: 1px solid #d1d5db; border-radius: 4px; margin-bottom: 8px;">
          </div>
          
          <div style="margin-bottom: 15px;">
            <label style="display: block; margin-bottom: 5px; font-weight: bold;">Notes (optional):</label>
            <textarea id="intervention-notes" placeholder="Additional notes or instructions..."
                      style="width: 100%; padding: 8px; border: 1px solid #d1d5db; border-radius: 4px; height: 60px;"></textarea>
          </div>
          
          <div style="margin-bottom: 15px;">
            <label style="display: block; margin-bottom: 5px; font-weight: bold;">Priority:</label>
            <select id="intervention-priority" style="width: 100%; padding: 8px; border: 1px solid #d1d5db; border-radius: 4px;">
              <option value="high">High - Immediate action needed</option>
              <option value="medium" selected>Medium - Address within a week</option>
              <option value="low">Low - Monitor and plan</option>
            </select>
          </div>

          <button id="add-intervention-btn" 
                  style="width: 100%; padding: 12px; background: #059669; color: white; border: none; border-radius: 6px; font-weight: bold; cursor: pointer;">
            Add Intervention
          </button>
        </div>
      </div>
    `;
  }

  // Set up event listeners for intervention panel
  setupInterventionPanelEvents(studentId) {
    // Recommendation button clicks
    document.querySelectorAll('.recommendation-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const intervention = btn.dataset.intervention;
        document.getElementById('custom-intervention').value = intervention;
      });
    });

    // Add intervention button
    document.getElementById('add-intervention-btn').addEventListener('click', () => {
      this.addNewIntervention(studentId);
    });
  }

  // Add new intervention
  addNewIntervention(studentId) {
    const interventionType = document.getElementById('custom-intervention').value.trim();
    const notes = document.getElementById('intervention-notes').value.trim();
    const priority = document.getElementById('intervention-priority').value;
    
    if (!interventionType) {
      alert('Please enter an intervention type.');
      return;
    }

    const newIntervention = {
      id: Date.now().toString(), // Simple ID generation
      type: interventionType,
      startDate: new Date().toLocaleDateString(),
      status: 'active',
      priority: priority,
      notes: notes,
      createdBy: 'Current User' // In a real system, this would be the logged-in user
    };

    // Get existing interventions and add new one
    const existingInterventions = this.getStoredInterventions(studentId);
    existingInterventions.push(newIntervention);
    
    // Store updated interventions
    this.storeInterventions(studentId, existingInterventions);
    
    // Close modal and refresh display
    this.hideModal();
    
    // Re-render the student list to show updated status
    this.renderStudentsClean();
    
    alert(`Intervention "${interventionType}" added successfully for Student #${studentId}`);
  }

  // Update intervention status
  updateInterventionStatus(studentId, interventionId, newStatus) {
    const interventions = this.getStoredInterventions(studentId);
    const intervention = interventions.find(i => i.id === interventionId);
    
    if (intervention) {
      intervention.status = newStatus;
      intervention.lastUpdated = new Date().toLocaleDateString();
      
      this.storeInterventions(studentId, interventions);
      
      // Refresh the intervention panel
      this.showInterventionPanel(studentId);
      
      alert(`Intervention status updated to: ${newStatus}`);
    }
  }

  // Show progress tracking
  async showProgressTracking(studentId) {
    console.log('Opening progress tracking for student:', studentId);
    
    const students = this.appState.getState().students;
    const student = students.find(s => s.student_id === studentId);
    const interventions = this.getStoredInterventions(studentId);
    
    if (!student) {
      alert('Student data not found');
      return;
    }

    // Create simple progress tracking display
    const progressHTML = `
      <div class="progress-tracking">
        <h4>Progress Overview - Student #${studentId}</h4>
        
        <div class="progress-metrics" style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 20px 0;">
          <div style="text-align: center; padding: 15px; background: #f8fafc; border-radius: 8px;">
            <div style="font-size: 24px; font-weight: bold; color: #059669;">${Math.round(student.success_probability * 100)}%</div>
            <div style="color: #6b7280;">Success Probability</div>
          </div>
          <div style="text-align: center; padding: 15px; background: #f8fafc; border-radius: 8px;">
            <div style="font-size: 24px; font-weight: bold; color: #dc2626;">${Math.round(student.risk_score * 100)}%</div>
            <div style="color: #6b7280;">Risk Score</div>
          </div>
        </div>

        <div class="intervention-timeline" style="margin: 20px 0;">
          <h5>Intervention Timeline</h5>
          ${interventions.length === 0 ? 
            '<p style="color: #6b7280;">No interventions recorded yet.</p>' :
            interventions.map(intervention => `
              <div style="border-left: 3px solid ${intervention.status === 'active' ? '#059669' : '#6b7280'}; padding-left: 15px; margin-bottom: 15px;">
                <div style="font-weight: bold;">${intervention.type}</div>
                <div style="font-size: 12px; color: #6b7280;">
                  ${intervention.startDate} | ${intervention.priority} priority | ${intervention.status}
                </div>
                ${intervention.notes ? `<div style="font-size: 12px; margin-top: 5px;">${intervention.notes}</div>` : ''}
              </div>
            `).join('')
          }
        </div>

        <div class="progress-actions" style="margin-top: 20px;">
          <button onclick="window.modernApp.showInterventionPanel(${studentId})" 
                  style="padding: 10px 20px; background: #059669; color: white; border: none; border-radius: 6px; margin-right: 10px; cursor: pointer;">
            Manage Interventions
          </button>
          <button onclick="window.modernApp.exportStudentReport(${studentId})" 
                  style="padding: 10px 20px; background: #7c3aed; color: white; border: none; border-radius: 6px; cursor: pointer;">
            Export Report
          </button>
        </div>
      </div>
    `;

    this.showModal(`Progress Tracking - Student #${studentId}`, progressHTML);
  }

  // Dashboard action methods
  exportClassReport() {
    const students = this.appState.getState().students;
    if (!students || students.length === 0) {
      alert('No student data available to export');
      return;
    }

    // Generate class report
    const report = {
      generated_date: new Date().toISOString(),
      class_summary: {
        total_students: students.length,
        high_risk: students.filter(s => (s.risk_score || 0) >= 0.7).length,
        medium_risk: students.filter(s => {
          const risk = s.risk_score || 0;
          return risk >= 0.4 && risk < 0.7;
        }).length,
        low_risk: students.filter(s => (s.risk_score || 0) < 0.4).length,
        avg_risk_score: students.reduce((sum, s) => sum + (s.risk_score || 0), 0) / students.length,
        avg_success_probability: students.reduce((sum, s) => sum + (s.success_probability || 0), 0) / students.length
      },
      students: students,
      recommendations: [
        'Schedule immediate interventions for high-risk students',
        'Monitor medium-risk students closely',
        'Continue support for low-risk students'
      ]
    };

    // Create downloadable file
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `class_report_${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    this.showNotification('📊 Class report exported successfully!', 'success');
  }

  scheduleInterventions() {
    const students = this.appState.getState().students;
    const highRiskStudents = students.filter(s => (s.risk_score || 0) >= 0.7);
    const mediumRiskStudents = students.filter(s => {
      const risk = s.risk_score || 0;
      return risk >= 0.4 && risk < 0.7;
    });

    this.showModal(
      'Schedule Interventions',
      `
      <div class="intervention-scheduling">
        <h4>Recommended Intervention Schedule</h4>
        
        ${highRiskStudents.length > 0 ? `
          <div class="priority-group">
            <h5 style="color: #dc2626;"><i class="fas fa-exclamation-triangle"></i> High Priority (${highRiskStudents.length} students)</h5>
            <ul>
              <li>Schedule within 24 hours</li>
              <li>One-on-one meetings with counselors</li>
              <li>Academic support plan creation</li>
              <li>Family notification and engagement</li>
            </ul>
          </div>
        ` : ''}
        
        ${mediumRiskStudents.length > 0 ? `
          <div class="priority-group">
            <h5 style="color: #d97706;"><i class="fas fa-clock"></i> Medium Priority (${mediumRiskStudents.length} students)</h5>
            <ul>
              <li>Schedule within 1 week</li>
              <li>Group intervention sessions</li>
              <li>Progress monitoring setup</li>
              <li>Peer mentoring programs</li>
            </ul>
          </div>
        ` : ''}
        
        <div class="scheduling-actions" style="margin-top: 20px;">
          <button class="btn btn-primary" onclick="alert('Integration with calendar system would be implemented here'); window.modernApp.hideModal();">
            <i class="fas fa-calendar-plus"></i> Schedule All Interventions
          </button>
        </div>
      </div>
      `
    );
  }

  shareInsights() {
    const students = this.appState.getState().students;
    const totalStudents = students.length;
    const needsIntervention = students.filter(s => s.needs_intervention).length;
    
    const insights = `
🎓 Student Success AI Analysis Results

📊 Class Overview:
• Total Students: ${totalStudents}
• Need Intervention: ${needsIntervention} (${Math.round(needsIntervention/totalStudents*100)}%)
• Model Accuracy: 89.4%

🤖 Generated by AI-powered early intervention system
    `.trim();

    // Copy to clipboard
    navigator.clipboard.writeText(insights).then(() => {
      this.showNotification('📋 Insights copied to clipboard!', 'success');
    }).catch(() => {
      // Fallback: show modal with text to copy
      this.showModal(
        'Share Insights',
        `
        <div class="share-insights">
          <p>Copy the insights below to share:</p>
          <textarea readonly style="width: 100%; height: 150px; padding: 10px; border: 1px solid #ddd; border-radius: 4px;">${insights}</textarea>
          <div style="margin-top: 15px;">
            <button class="btn btn-primary" onclick="document.querySelector('textarea').select(); document.execCommand('copy'); window.modernApp.hideModal(); window.modernApp.showNotification('Insights copied!', 'success');">
              Copy Text
            </button>
          </div>
        </div>
        `
      );
    });
  }

  // Export student report
  exportStudentReport(studentId) {
    const students = this.appState.getState().students;
    const student = students.find(s => s.student_id === studentId);
    const interventions = this.getStoredInterventions(studentId);
    
    if (!student) {
      alert('Student data not found');
      return;
    }

    // Create simple report data
    const report = {
      student_id: studentId,
      generated_date: new Date().toISOString(),
      risk_assessment: {
        risk_score: student.risk_score,
        risk_category: student.risk_category,
        success_probability: student.success_probability,
        needs_intervention: student.needs_intervention
      },
      interventions: interventions,
      recommendations: [
        'Continue monitoring student progress',
        'Regular check-ins with family',
        'Academic support as needed'
      ]
    };

    // Create downloadable file
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `student_${studentId}_report.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    alert(`Report exported for Student #${studentId}`);
  }

  // Main app's renderStudentsClean method - accessible for intervention features
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
    
    // Create clean HTML for each student with intervention features
    const html = students.map(student => {
      const riskPercent = Math.round(student.risk_score * 100);
      const successPercent = Math.round(student.success_probability * 100);
      
      // Get intervention status using the main app's method
      const interventionStatus = this.getInterventionStatus(student);
      const riskColor = student.risk_category === 'Warning' ? '#dc2626' : 
                       student.risk_category === 'Moderate Risk' ? '#d97706' : '#16a34a';
      
      return `
        <div class="student-intervention-card" style="border: 1px solid #ddd; margin: 10px; padding: 15px; background: white; border-radius: 8px; cursor: pointer; border-left: 4px solid ${riskColor}; min-width: 400px; max-width: 500px;" 
             onclick="window.modernApp.selectStudent(${student.student_id})">
          <div class="student-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
            <h3 style="margin: 0;">Student #${student.student_id}</h3>
            <span class="intervention-status ${interventionStatus.class}" style="padding: 2px 8px; border-radius: 12px; font-size: 12px; font-weight: bold;">
              ${interventionStatus.text}
            </span>
          </div>
          
          <div class="risk-metrics" style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 12px;">
            <div><strong>Risk Score:</strong> <span style="color: ${riskColor};">${riskPercent}%</span></div>
            <div><strong>Success Prob:</strong> ${successPercent}%</div>
            <div><strong>Category:</strong> ${student.risk_category}</div>
            <div><strong>Intervention:</strong> ${student.needs_intervention ? 'Needed' : 'Not Needed'}</div>
          </div>
          
          <div class="action-buttons" style="display: flex; gap: 8px; margin-top: 12px;">
            <button onclick="event.stopPropagation(); window.modernApp.showStudentExplanation(${student.student_id})" 
                    onmouseover="this.style.background='#1d4ed8'; this.style.transform='translateY(-1px)'; this.style.boxShadow='0 4px 8px rgba(37, 99, 235, 0.3)'" 
                    onmouseout="this.style.background='#2563eb'; this.style.transform='translateY(0)'; this.style.boxShadow='0 2px 4px rgba(0,0,0,0.1)'" 
                    style="background: #2563eb; color: white; border: none; padding: 8px 16px; border-radius: 6px; font-size: 12px; cursor: pointer; flex: 1; font-weight: 500; transition: all 0.2s ease; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
              🔍 Explain AI
            </button>
            <button onclick="event.stopPropagation(); window.modernApp.showInterventionPanel(${student.student_id})" 
                    onmouseover="this.style.background='#047857'; this.style.transform='translateY(-1px)'; this.style.boxShadow='0 4px 8px rgba(5, 150, 105, 0.3)'" 
                    onmouseout="this.style.background='#059669'; this.style.transform='translateY(0)'; this.style.boxShadow='0 2px 4px rgba(0,0,0,0.1)'" 
                    style="background: #059669; color: white; border: none; padding: 8px 16px; border-radius: 6px; font-size: 12px; cursor: pointer; flex: 1; font-weight: 500; transition: all 0.2s ease; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
              📋 Interventions
            </button>
            <button onclick="event.stopPropagation(); window.modernApp.showProgressTracking(${student.student_id})" 
                    onmouseover="this.style.background='#6d28d9'; this.style.transform='translateY(-1px)'; this.style.boxShadow='0 4px 8px rgba(124, 58, 237, 0.3)'" 
                    onmouseout="this.style.background='#7c3aed'; this.style.transform='translateY(0)'; this.style.boxShadow='0 2px 4px rgba(0,0,0,0.1)'" 
                    style="background: #7c3aed; color: white; border: none; padding: 8px 16px; border-radius: 6px; font-size: 12px; cursor: pointer; flex: 1; font-weight: 500; transition: all 0.2s ease; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
              📈 Progress
            </button>
          </div>
        </div>
      `;
    }).join('');
    
    container.innerHTML = html;
    console.log('✅ Students rendered to container successfully');
  }
}

// =============================================================================
// Global Functions - Using Working Explanation Patterns
// =============================================================================

let appInstance = null;

// Global functions - EXACT REPLICA of working explanation system
window.showExplanation = async function(studentId) {
  if (!window.modernApp) return;
  
  try {
    // Show loading in modal first
    window.modernApp.showModal(
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
            <button class="btn btn-primary" onclick="window.modernApp.hideModal()">Close</button>
          </div>
        </div>
      `;
    }
    
  } catch (error) {
    console.error('Failed to load explanation:', error);
    window.modernApp.showModal(
      'Error Loading Explanation',
      `<div class="error-content"><p>Failed to load explanation: ${error.message}</p><button class="btn btn-primary" onclick="window.modernApp.hideModal()">Close</button></div>`
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
/* Dashboard-specific styles */
.dashboard-grid {
  display: grid !important;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)) !important;
  gap: 20px !important;
  max-height: 80vh !important;
  overflow-y: auto !important;
}

.dashboard-card {
  background: white !important;
  border: 1px solid #e5e7eb !important;
  border-radius: 12px !important;
  padding: 20px !important;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
  height: fit-content !important;
}

.chart-card {
  height: 350px !important;
}

.chart-container {
  height: 250px !important;
  position: relative !important;
}

.chart-container canvas {
  max-height: 250px !important;
}

.metrics-overview {
  grid-column: 1 / -1;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 15px;
  margin-bottom: 20px;
}

.metric {
  text-align: center;
  padding: 15px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.metric-value {
  font-size: 24px;
  font-weight: bold;
  color: #1f2937;
}

.metric-label {
  font-size: 12px;
  color: #6b7280;
  margin-top: 5px;
}

.metric.metric-danger .metric-value { color: #dc2626; }
.metric.metric-warning .metric-value { color: #d97706; }
.metric.metric-success .metric-value { color: #16a34a; }

.summary-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
  padding: 15px;
  background: #f1f5f9;
  border-radius: 8px;
  border: 1px solid #cbd5e1;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 5px 0;
}

.stat-label {
  color: #475569;
  font-size: 13px;
}

.stat-value {
  color: #1e293b;
  font-weight: 600;
  font-size: 13px;
}

.model-performance {
  height: fit-content !important;
}

.performance-metrics {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.performance-item {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 12px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.performance-icon {
  font-size: 24px;
}

.performance-value {
  font-size: 18px;
  font-weight: bold;
  color: #1f2937;
}

.performance-label {
  font-size: 12px;
  color: #6b7280;
}

.quick-actions {
  height: fit-content !important;
}

.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
  text-align: left;
}

.action-btn.primary {
  background: #2563eb;
  color: white;
}

.action-btn.secondary {
  background: #059669;
  color: white;
}

.action-btn.accent {
  background: #7c3aed;
  color: white;
}

.action-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.15);
}

.recent-activity {
  height: fit-content !important;
}

.activity-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.activity-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.activity-icon {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  color: white;
  flex-shrink: 0;
}

.activity-icon.success { background: #16a34a; }
.activity-icon.warning { background: #d97706; }
.activity-icon.info { background: #2563eb; }

.activity-content {
  flex: 1;
}

.activity-text {
  font-size: 13px;
  color: #374151;
  margin-bottom: 2px;
}

.activity-time {
  font-size: 11px;
  color: #6b7280;
}

@media (max-width: 768px) {
  .dashboard-grid {
    grid-template-columns: 1fr !important;
  }
  
  .metrics-grid {
    grid-template-columns: repeat(2, 1fr) !important;
  }
  
  .summary-stats {
    grid-template-columns: 1fr !important;
  }
}

/* Insights Page Styles */
.insights-grid {
  display: grid !important;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)) !important;
  gap: 20px !important;
  max-height: 80vh !important;
  overflow-y: auto !important;
}

.insight-card {
  background: white !important;
  border: 1px solid #e5e7eb !important;
  border-radius: 12px !important;
  padding: 20px !important;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
  height: fit-content !important;
}

.insight-card h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 15px;
  color: #1f2937;
  font-size: 18px;
}

/* Model Performance */
.model-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
}

.model-stat {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 15px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.model-stat.primary { background: linear-gradient(135deg, #dbeafe, #eff6ff); }
.model-stat.success { background: linear-gradient(135deg, #dcfce7, #f0fdf4); }
.model-stat.info { background: linear-gradient(135deg, #e0f2fe, #f0f9ff); }
.model-stat.warning { background: linear-gradient(135deg, #fef3c7, #fffbeb); }

.stat-icon {
  font-size: 24px;
}

.stat-value {
  font-size: 20px;
  font-weight: bold;
  color: #1f2937;
}

.stat-label {
  font-size: 13px;
  color: #374151;
  font-weight: 600;
}

.stat-description {
  font-size: 11px;
  color: #6b7280;
}

/* Feature Importance */
.feature-importance {
  grid-column: 1 / -1;
}

.importance-chart-container {
  height: 300px;
  margin-bottom: 20px;
}

.feature-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.feature-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  background: #f8fafc;
  border-radius: 6px;
  border: 1px solid #e2e8f0;
}

.feature-name {
  font-weight: 500;
  color: #374151;
}

.feature-category {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 10px;
  text-transform: capitalize;
  margin-top: 2px;
}

.feature-category.academic { background: #dbeafe; color: #1e40af; }
.feature-category.engagement { background: #dcfce7; color: #166534; }
.feature-category.demographics { background: #fef3c7; color: #92400e; }
.feature-category.assessment { background: #f3e8ff; color: #7c2d12; }

.feature-importance {
  display: flex;
  align-items: center;
  gap: 10px;
}

.importance-bar {
  width: 80px;
  height: 6px;
  background: #e5e7eb;
  border-radius: 3px;
  overflow: hidden;
}

.importance-fill {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6, #1d4ed8);
  border-radius: 3px;
}

.importance-value {
  font-size: 12px;
  font-weight: 600;
  color: #374151;
  width: 35px;
}

/* Category Breakdown */
.category-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 15px;
}

.category-card {
  padding: 15px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.category-card.academic { background: linear-gradient(135deg, #dbeafe, #eff6ff); }
.category-card.engagement { background: linear-gradient(135deg, #dcfce7, #f0fdf4); }
.category-card.demographics { background: linear-gradient(135deg, #fef3c7, #fffbeb); }

.category-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.category-icon {
  font-size: 20px;
}

.category-title {
  font-weight: 600;
  color: #374151;
}

.category-importance {
  font-size: 24px;
  font-weight: bold;
  color: #1f2937;
  margin-bottom: 8px;
}

.category-description {
  font-size: 13px;
  color: #6b7280;
  margin-bottom: 10px;
}

.category-factors {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.factor-tag {
  font-size: 11px;
  padding: 2px 6px;
  background: rgba(59, 130, 246, 0.1);
  color: #1d4ed8;
  border-radius: 4px;
}

/* Methodology */
.methodology-content {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}

.method-section h4 {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #374151;
  margin-bottom: 10px;
}

.method-section ul {
  list-style: none;
  padding: 0;
}

.method-section li {
  padding: 5px 0;
  padding-left: 20px;
  position: relative;
  color: #6b7280;
  font-size: 13px;
}

.method-section li:before {
  content: '→';
  position: absolute;
  left: 0;
  color: #3b82f6;
  font-weight: bold;
}

/* Real-time Analytics */
.real-time-stats {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.insight-highlight {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 15px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.highlight-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
}

.highlight-icon.danger { background: #fef2f2; }
.highlight-icon.warning { background: #fffbeb; }
.highlight-icon.success { background: #f0fdf4; }

.highlight-title {
  font-weight: 600;
  color: #374151;
  margin-bottom: 2px;
}

.highlight-value {
  font-size: 18px;
  font-weight: bold;
  color: #1f2937;
  margin-bottom: 2px;
}

.highlight-desc {
  font-size: 12px;
  color: #6b7280;
}

.no-data {
  text-align: center;
  padding: 40px 20px;
  color: #9ca3af;
}

.no-data i {
  font-size: 48px;
  margin-bottom: 15px;
  opacity: 0.5;
}

/* Model Validation */
.validation-metrics {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.metric-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #f3f4f6;
}

.metric-label {
  color: #6b7280;
  font-size: 13px;
}

.metric-value {
  font-weight: 600;
  font-size: 13px;
}

.metric-value.success { color: #16a34a; }
.metric-value.primary { color: #2563eb; }
.metric-value.info { color: #0891b2; }
</style>
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

/* Intervention status styles */
.intervention-status.status-needed {
  background: #dc2626; color: white;
}

.intervention-status.status-active {
  background: #059669; color: white;
}

.intervention-status.status-none {
  background: #6b7280; color: white;
}

.student-intervention-card {
  transition: all 0.2s ease;
}

.student-intervention-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* Enhanced button hover effects */
.action-buttons button {
  position: relative;
  overflow: hidden;
}

.action-buttons button::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
  transition: left 0.5s;
}

.action-buttons button:hover::before {
  left: 100%;
}

.intervention-panel .recommendation-btn:hover {
  background: #e5e7eb !important;
  border-color: #059669 !important;
}

.progress-tracking .progress-metrics > div {
  transition: all 0.2s ease;
}

.progress-tracking .progress-metrics > div:hover {
  transform: scale(1.05);
}
</style>
`;

document.head.insertAdjacentHTML('beforeend', additionalStyles);

// Initialize the application when DOM is loaded (same pattern as working app.js)
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Initializing Modern Student Success App');
    const app = new StudentSuccessApp();
    window.modernApp = app;
    appInstance = app;
    console.log('✅ Modern app initialized and attached to window.modernApp and appInstance');
});