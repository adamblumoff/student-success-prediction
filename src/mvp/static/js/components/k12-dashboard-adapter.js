/**
 * K-12 Educational Dashboard Adapter (REFACTOR Phase)
 * 
 * Integrates the K12Dashboard component with the existing Component architecture
 * while maintaining FERPA compliance and educational appropriateness
 */

class K12DashboardAdapter extends Component {
  init() {
    console.log('🚀 K12DashboardAdapter: Initializing...');
    this.k12Dashboard = null;
    this.mockAuthenticatedUser = {
      role: 'teacher',
      institution_id: 1,
      authorized_grades: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], // All grades for demo
      name: 'Demo Teacher'
    };
    
    this.appState.subscribe('students', this.updateDashboard.bind(this));
    this.appState.subscribe('currentTab', this.handleTabChange.bind(this));
    console.log('✅ K12DashboardAdapter: Initialized and subscribed to app state changes');
  }

  handleTabChange(currentTab) {
    console.log('🔄 K12DashboardAdapter: Tab changed to', currentTab);
    if (currentTab === 'dashboard') {
      console.log('🎯 K12DashboardAdapter: Dashboard tab activated, rendering...');
      // Small delay to ensure DOM is ready
      setTimeout(() => {
        this.renderK12Dashboard();
      }, 100);
    }
  }

  updateDashboard(students) {
    if (students && students.length > 0) {
      this.renderK12Dashboard(students);
    }
  }

  renderK12Dashboard(students = null) {
    console.log('📊 K12DashboardAdapter: renderK12Dashboard called with', students ? students.length : 'null', 'students');
    
    // For K-12 dashboard, ALWAYS fetch fresh real data from database
    // This ensures we show real student data, not sample/demo data
    if (!students || !this.isK12Format(students)) {
      console.log('🔄 K12DashboardAdapter: Fetching fresh real student data from database...');
      this.fetchRealStudentData();
      return;
    }

    console.log('📊 Rendering K-12 educational dashboard with', students.length, 'students');
    
    // Check if students are already in K12 format (from database) or need conversion (from app state)
    const k12StudentData = this.isK12Format(students) ? students : this.convertToK12Format(students);
    
    // Create audit logger for FERPA compliance
    const auditLogger = (logEntry) => {
      console.log('🔐 FERPA Audit Log:', logEntry);
      // In production, this would be sent to audit logging system
    };
    
    // Create mock GPT service for testing
    const mockGPTService = (request) => {
      console.log('🤖 GPT Service Request:', request);
      // In production, this would call actual GPT service
      return Promise.resolve();
    };
    
    // Initialize K12Dashboard with FERPA compliance features
    this.k12Dashboard = new K12Dashboard(
      '#tab-dashboard .dashboard-grid',
      this.mockAuthenticatedUser,
      k12StudentData,
      auditLogger,
      mockGPTService
    );
    
    // Render the K-12 compliant dashboard
    this.k12Dashboard.render().then(() => {
      console.log('✅ K-12 dashboard rendered successfully');
      this.addEducationalFeatures();
    }).catch(error => {
      console.error('❌ K-12 dashboard render error:', error);
      this.renderFallbackDashboard(students);
    });
  }

  convertToK12Format(students) {
    return students.map((student, index) => ({
      student_id: student.student_id || `student_${index}`,
      grade_level: this.determineGradeLevel(student),
      risk_category: this.mapRiskCategory(student.risk_score),
      reading_level: this.estimateReadingLevel(student),
      interventions: this.mapInterventions(student),
      special_populations: {
        has_iep: student.has_iep || false,
        is_ell: student.is_ell || false,
        has_504: student.has_504 || false
      },
      credits_earned: student.credits_earned || this.estimateCredits(student),
      college_readiness: student.college_readiness || this.assessCollegeReadiness(student),
      behavioral_concerns: this.identifyBehavioralConcerns(student),
      study_skills_rating: this.assessStudySkills(student),
      last_updated: new Date().toISOString()
    }));
  }

  determineGradeLevel(student) {
    // Use existing grade_level if available, otherwise estimate from other data
    if (student.grade_level) return student.grade_level;
    
    // Estimate based on age or other factors
    if (student.age) {
      return Math.max(1, Math.min(12, student.age - 5));
    }
    
    // Default to middle school for demonstration
    return 7;
  }

  mapRiskCategory(riskScore) {
    if (!riskScore) return 'Monitor Progress';
    
    // Use educational terminology instead of clinical risk language
    if (riskScore >= 0.7) return 'Needs Additional Support';
    if (riskScore >= 0.4) return 'Monitor Progress';
    return 'On Track';
  }

  estimateReadingLevel(student) {
    // Estimate reading level based on grade and performance
    const gradeLevel = this.determineGradeLevel(student);
    const performance = student.current_gpa || 2.5;
    
    // Reading level typically correlates with grade level and academic performance
    const baseLine = gradeLevel;
    const performanceAdjustment = (performance - 2.5) * 0.8; // Scale GPA impact
    
    return Math.max(0.5, baseLine + performanceAdjustment);
  }

  mapInterventions(student) {
    const interventions = [];
    
    if (student.needs_intervention) {
      const riskScore = student.risk_score || 0;
      
      if (riskScore >= 0.7) {
        interventions.push('Academic Support Program', 'Family Engagement Initiative');
      } else if (riskScore >= 0.4) {
        interventions.push('Study Skills Workshop');
      }
      
      // Add specific interventions based on student data
      if (student.attendance_rate && student.attendance_rate < 0.85) {
        interventions.push('Attendance Improvement Plan');
      }
      
      if (student.current_gpa && student.current_gpa < 2.0) {
        interventions.push('Academic Recovery Program');
      }
    }
    
    return interventions;
  }

  estimateCredits(student) {
    const gradeLevel = this.determineGradeLevel(student);
    if (gradeLevel < 9) return undefined; // Elementary/Middle school
    
    // Estimate credits for high school students
    const expectedCreditsPerGrade = 6;
    const baseCredits = Math.max(0, (gradeLevel - 9) * expectedCreditsPerGrade);
    const performanceMultiplier = (student.current_gpa || 2.5) / 4.0;
    
    return Math.round(baseCredits * performanceMultiplier * 10) / 10;
  }

  assessCollegeReadiness(student) {
    const gradeLevel = this.determineGradeLevel(student);
    if (gradeLevel < 11) return undefined; // Not applicable for younger students
    
    const gpa = student.current_gpa || 2.5;
    const attendance = student.attendance_rate || 0.9;
    
    // Simple college readiness assessment
    return gpa >= 3.0 && attendance >= 0.9;
  }

  identifyBehavioralConcerns(student) {
    const concerns = [];
    
    if (student.attendance_rate && student.attendance_rate < 0.85) {
      concerns.push('Attendance');
    }
    
    if (student.risk_score && student.risk_score >= 0.6) {
      concerns.push('Academic Engagement');
    }
    
    return concerns;
  }

  assessStudySkills(student) {
    // Estimate study skills based on GPA and other factors
    const gpa = student.current_gpa || 2.5;
    const studyHours = student.study_hours_week || 5;
    
    // Convert to 1-5 scale
    const gpaScore = (gpa / 4.0) * 2.5;
    const studyScore = Math.min(2.5, studyHours / 4);
    
    return Math.round((gpaScore + studyScore) * 10) / 10;
  }

  async fetchRealStudentData(institutionId = 1, gradeLevels = null) {
    try {
      console.log('🔄 Fetching real student data from database...');
      
      // Build query parameters
      const params = new URLSearchParams();
      if (gradeLevels) {
        params.append('grade_levels', gradeLevels);
      }
      
      // Fetch data from new K12 dashboard endpoint
      const url = `/api/k12-dashboard/students?institution_id=${institutionId}${params.toString() ? '&' + params.toString() : ''}`;
      
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('api_key') || '0dUHi4QroC1GfgnbibLbqowUnv2YFWIe'}`
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch student data: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      
      console.log(`✅ Fetched ${data.students.length} students from database`);
      console.log('📊 Grade distribution:', data.metadata.grade_distribution);
      console.log('⚠️ Risk distribution:', data.metadata.risk_distribution);
      
      // Store K12 dashboard data separately - don't pollute global app state
      // (K12 students are FERPA-compliant and don't have names, which breaks other components)
      this.k12Students = data.students;
      this.k12Metadata = data.metadata;
      
      // Now render with real data
      this.renderK12Dashboard(data.students);
      
    } catch (error) {
      console.error('❌ Failed to fetch real student data:', error);
      
      // Show error message to user
      this.renderErrorState('Unable to load student data from database. Using fallback display.');
      
      // Fallback to empty state or basic demo data
      this.renderEmptyState();
    }
  }

  isK12Format(students) {
    // Check if students array contains K12-formatted objects
    if (!Array.isArray(students) || students.length === 0) {
      return false;
    }
    
    const firstStudent = students[0];
    
    // K12 format has specific fields that distinguish it from app state format
    return firstStudent.hasOwnProperty('reading_level') ||
           firstStudent.hasOwnProperty('special_populations') ||
           firstStudent.hasOwnProperty('behavioral_concerns') ||
           firstStudent.data_source === 'database';
  }

  renderErrorState(message) {
    const dashboardGrid = this.element.querySelector('.dashboard-grid');
    if (!dashboardGrid) return;

    dashboardGrid.innerHTML = `
      <div class="error-state">
        <div class="error-state-icon">
          <i class="fas fa-exclamation-triangle" style="color: #f59e0b;"></i>
        </div>
        <h3>Dashboard Data Error</h3>
        <p>${message}</p>
        <button class="btn btn-primary" onclick="location.reload()">
          <i class="fas fa-refresh"></i>
          Reload Dashboard
        </button>
      </div>
    `;
  }

  addEducationalFeatures() {
    // Add educational-specific UI enhancements
    const dashboardElement = this.element.querySelector('.dashboard-grid');
    if (!dashboardElement) return;

    // Add grade-band navigation
    const gradeBandNav = document.createElement('div');
    gradeBandNav.className = 'grade-band-navigation';
    gradeBandNav.innerHTML = `
      <div class="nav-buttons">
        <button class="grade-band-btn active" data-band="all">All Students</button>
        <button class="grade-band-btn" data-band="elementary">Elementary (K-5)</button>
        <button class="grade-band-btn" data-band="middle">Middle (6-8)</button>
        <button class="grade-band-btn" data-band="high">High School (9-12)</button>
      </div>
    `;
    
    dashboardElement.insertBefore(gradeBandNav, dashboardElement.firstChild);

    // Add event listeners for grade band filtering
    gradeBandNav.querySelectorAll('.grade-band-btn').forEach(btn => {
      this.bindEvent(btn, 'click', this.handleGradeBandFilter);
    });

    // Add FERPA compliance indicator
    const complianceIndicator = document.createElement('div');
    complianceIndicator.className = 'ferpa-compliance-indicator';
    complianceIndicator.innerHTML = `
      <div class="compliance-status">
        <i class="fas fa-shield-alt"></i>
        <span>FERPA Compliant</span>
        <small>Student data is protected and anonymized</small>
      </div>
    `;
    
    dashboardElement.appendChild(complianceIndicator);
  }

  handleGradeBandFilter(event) {
    const band = event.target.getAttribute('data-band');
    
    // Update active button
    this.element.querySelectorAll('.grade-band-btn').forEach(btn => {
      btn.classList.remove('active');
    });
    event.target.classList.add('active');

    if (band === 'all') {
      // Show all students
      const studentCards = this.element.querySelectorAll('.student-card');
      studentCards.forEach(card => {
        card.style.display = 'block';
      });
      console.log('🎯 Showing all students');
      return;
    }

    // If we want to filter by grade band, we could either:
    // 1. Filter existing cards (current approach)
    // 2. Fetch filtered data from API (more efficient for large datasets)
    
    // For now, let's filter existing cards for immediate response
    const studentCards = this.element.querySelectorAll('.student-card');
    studentCards.forEach(card => {
      const gradeLevel = parseInt(card.getAttribute('data-student-grade'));
      let shouldShow = true;

      if (band === 'elementary' && (gradeLevel < 0 || gradeLevel > 5)) {
        shouldShow = false;
      } else if (band === 'middle' && (gradeLevel < 6 || gradeLevel > 8)) {
        shouldShow = false;
      } else if (band === 'high' && (gradeLevel < 9 || gradeLevel > 12)) {
        shouldShow = false;
      }

      card.style.display = shouldShow ? 'block' : 'none';
    });

    console.log(`🎯 Filtered dashboard for ${band} grade band`);
    
    // For large datasets, we could optionally fetch filtered data:
    // this.fetchRealStudentData(1, this.getGradeLevelsForBand(band));
  }

  getGradeLevelsForBand(band) {
    // Convert grade band to specific grade levels for API filtering
    switch (band) {
      case 'elementary':
        return 'K,1,2,3,4,5';
      case 'middle':
        return '6,7,8';
      case 'high':
        return '9,10,11,12';
      default:
        return null;
    }
  }

  renderEmptyState() {
    const dashboardGrid = this.element.querySelector('.dashboard-grid');
    if (!dashboardGrid) return;

    dashboardGrid.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">
          <i class="fas fa-chart-line"></i>
        </div>
        <h3>No Student Data Available</h3>
        <p>Upload student data to view the K-12 educational dashboard with FERPA-compliant analytics.</p>
        <button class="btn btn-primary" onclick="document.querySelector('[data-tab=\"upload\"]').click()">
          <i class="fas fa-upload"></i>
          Upload Student Data
        </button>
      </div>
    `;
  }

  renderFallbackDashboard(students) {
    console.log('📊 Rendering fallback dashboard due to K-12 dashboard error');
    
    const dashboardGrid = this.element.querySelector('.dashboard-grid');
    if (!dashboardGrid) return;

    const totalStudents = students.length;
    const highRisk = students.filter(s => (s.risk_score || 0) >= 0.7).length;

    dashboardGrid.innerHTML = `
      <div class="fallback-dashboard">
        <div class="dashboard-card">
          <h3>Class Overview (Fallback Mode)</h3>
          <div class="metrics-grid">
            <div class="metric">
              <div class="metric-value">${totalStudents}</div>
              <div class="metric-label">Total Students</div>
            </div>
            <div class="metric metric-danger">
              <div class="metric-value">${highRisk}</div>
              <div class="metric-label">Need Support</div>
            </div>
          </div>
          <div class="fallback-notice">
            <i class="fas fa-info-circle"></i>
            <span>Using simplified view. K-12 features temporarily unavailable.</span>
          </div>
        </div>
      </div>
    `;
  }

  destroy() {
    if (this.k12Dashboard) {
      // Clean up K12Dashboard resources if it has a destroy method
      if (typeof this.k12Dashboard.destroy === 'function') {
        this.k12Dashboard.destroy();
      }
    }
    super.destroy();
  }
}

// Make K12DashboardAdapter available globally
window.K12DashboardAdapter = K12DashboardAdapter;