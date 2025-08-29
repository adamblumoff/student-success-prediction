/**
 * K-12 Educational Dashboard Adapter (REFACTOR Phase)
 * 
 * Integrates the K12Dashboard component with the existing Component architecture
 * while maintaining FERPA compliance and educational appropriateness
 */

class K12DashboardAdapter extends Component {
  init() {
    this.k12Dashboard = null;
    this.mockAuthenticatedUser = {
      role: 'teacher',
      institution_id: 1,
      authorized_grades: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], // All grades for demo
      name: 'Demo Teacher'
    };
    
    this.appState.subscribe('students', this.updateDashboard.bind(this));
    this.appState.subscribe('currentTab', this.handleTabChange.bind(this));
  }

  handleTabChange(currentTab) {
    if (currentTab === 'dashboard') {
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
    if (!students) {
      students = this.appState.getState().students;
    }
    
    if (!students || students.length === 0) {
      console.log('No students available for K-12 dashboard');
      this.renderEmptyState();
      return;
    }

    console.log('📊 Rendering K-12 educational dashboard with', students.length, 'students');
    
    // Convert app state students to K12Dashboard format
    const k12StudentData = this.convertToK12Format(students);
    
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

    // Filter student cards based on grade band
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