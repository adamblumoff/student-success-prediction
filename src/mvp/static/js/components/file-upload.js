/**
 * File Upload Component
 * Handles CSV file uploads, drag-and-drop, and sample data loading
 */

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
    // Add to notification panel if it exists and we have the app instance
    if (window.modernApp && window.modernApp.addNotificationToPanel) {
      window.modernApp.addNotificationToPanel({
        id: Date.now(),
        type: type,
        message: message,
        timestamp: new Date(),
        read: false
      });
    }

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