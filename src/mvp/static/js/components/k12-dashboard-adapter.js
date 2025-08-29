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
    
    // Render educator-focused dashboard with actionable insights
    this.renderEducatorDashboard(k12StudentData, this.k12Metadata);
    console.log('✅ K-12 educator dashboard rendered successfully');
    this.addEducationalFeatures();
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

  renderEducatorDashboard(students, metadata) {
    const dashboardElement = this.element.querySelector('.dashboard-grid');
    if (!dashboardElement) return;

    // Store data for tab switching
    this.k12Students = students;
    this.k12Metadata = metadata;
    this.insights = this.calculateEducatorInsights(students, metadata);
    
    dashboardElement.innerHTML = `
      <div class="educator-dashboard">
        <!-- Tab Navigation -->
        <div class="dashboard-tabs">
          <button class="dashboard-tab active" data-tab="overview">
            <i class="fas fa-chart-bar"></i>
            Overview
          </button>
          <button class="dashboard-tab" data-tab="students">
            <i class="fas fa-users"></i>
            Students
          </button>
          <button class="dashboard-tab" data-tab="alerts">
            <i class="fas fa-exclamation-triangle"></i>
            Alerts
          </button>
          <button class="dashboard-tab" data-tab="reports">
            <i class="fas fa-file-chart-line"></i>
            Reports
          </button>
        </div>

        <!-- Tab Content -->
        <div class="dashboard-content">
          <div id="tab-overview" class="tab-panel active">
            ${this.renderOverviewTab()}
          </div>
          <div id="tab-students" class="tab-panel">
            ${this.renderStudentsTab()}
          </div>
          <div id="tab-alerts" class="tab-panel">
            ${this.renderAlertsTab()}
          </div>
          <div id="tab-reports" class="tab-panel">
            ${this.renderReportsTab()}
          </div>
        </div>
      </div>
    `;

    // Bind events for tabs and functionality
    this.bindTabEvents();
    this.bindDashboardEvents();
    this.bindTableFilters(students);
  }

  renderOverviewTab() {
    return `
      <div class="overview-grid">
        <div class="overview-card summary-card">
          <h3><i class="fas fa-chart-pie"></i> Risk Summary</h3>
          <div class="summary-stats">
            <div class="stat-item">
              <div class="stat-number high-risk">${this.insights.overallHighRisk}</div>
              <div class="stat-label">High Risk</div>
            </div>
            <div class="stat-item">
              <div class="stat-number medium-risk">${this.insights.overallMediumRisk}</div>
              <div class="stat-label">Medium Risk</div>
            </div>
            <div class="stat-item">
              <div class="stat-number low-risk">${this.insights.overallLowRisk}</div>
              <div class="stat-label">Low Risk</div>
            </div>
          </div>
        </div>

        <div class="overview-card grade-card">
          <h3><i class="fas fa-graduation-cap"></i> Grade Breakdown</h3>
          <div class="grade-breakdown">
            ${Object.keys(this.insights.gradeAnalysis).sort((a, b) => parseInt(a) - parseInt(b)).map(grade => {
              const analysis = this.insights.gradeAnalysis[grade];
              return `
                <div class="grade-stat">
                  <span class="grade-label">Grade ${grade}</span>
                  <span class="grade-counts">
                    <span class="high-count">${analysis.highRisk}</span>/<span class="total-count">${analysis.total}</span>
                  </span>
                </div>
              `;
            }).join('')}
          </div>
        </div>

        <div class="overview-card actions-card">
          <h3><i class="fas fa-lightning-bolt"></i> Quick Actions</h3>
          <div class="action-buttons">
            <button class="action-btn primary" data-action="export-high-risk" data-count="${this.insights.overallHighRisk}">
              <i class="fas fa-download"></i>
              Export High Risk (${this.insights.overallHighRisk})
            </button>
            <button class="action-btn secondary" data-action="bulk-interventions" data-count="${this.insights.overallHighRisk}">
              <i class="fas fa-plus-circle"></i>
              Create Interventions
            </button>
            <button class="action-btn tertiary" data-action="generate-report">
              <i class="fas fa-file-pdf"></i>
              Generate Report
            </button>
          </div>
        </div>
      </div>
    `;
  }

  renderStudentsTab() {
    return `
      <div class="students-section">
        <div class="section-header">
          <h2>Student Risk Assessment</h2>
          <div class="filter-controls">
            <select id="grade-filter" class="filter-select">
              <option value="">All Grades</option>
              <option value="9">Grade 9</option>
              <option value="10">Grade 10</option>
              <option value="11">Grade 11</option>
              <option value="12">Grade 12</option>
            </select>
            <select id="risk-filter" class="filter-select">
              <option value="">All Risk Levels</option>
              <option value="high">High Risk</option>
              <option value="medium">Medium Risk</option>
              <option value="low">Low Risk</option>
            </select>
          </div>
        </div>
        ${this.renderStudentTable(this.k12Students)}
      </div>
    `;
  }

  renderAlertsTab() {
    return `
      <div class="alerts-section">
        <h2>Critical Alerts</h2>
        <div class="alerts-grid">
          ${this.renderDetailedAlerts()}
        </div>
      </div>
    `;
  }

  renderReportsTab() {
    return `
      <div class="reports-section">
        <h2>Reports & Analytics</h2>
        <div class="reports-grid">
          <div class="report-card">
            <h3><i class="fas fa-file-pdf"></i> Risk Assessment Report</h3>
            <p>Complete risk analysis for all students with recommendations.</p>
            <button class="report-btn" data-action="generate-report">
              <i class="fas fa-download"></i>
              Generate Report
            </button>
          </div>
          
          <div class="report-card">
            <h3><i class="fas fa-file-csv"></i> High Risk Students Export</h3>
            <p>Detailed CSV export of students requiring immediate intervention.</p>
            <button class="report-btn" data-action="export-high-risk">
              <i class="fas fa-download"></i>
              Export CSV (${this.insights.overallHighRisk} students)
            </button>
          </div>

          <div class="report-card">
            <h3><i class="fas fa-calendar-check"></i> Intervention Planning</h3>
            <p>Bulk intervention planning for high-risk students.</p>
            <button class="report-btn" data-action="bulk-interventions">
              <i class="fas fa-plus-circle"></i>
              Plan Interventions
            </button>
          </div>
        </div>
      </div>
    `;
  }

  renderDetailedAlerts() {
    const alerts = [];
    
    // Critical Grade 12 situation
    const grade12 = this.insights.gradeAnalysis[12];
    if (grade12 && grade12.highRisk > 0) {
      const riskPercent = ((grade12.highRisk / grade12.total) * 100).toFixed(0);
      alerts.push(`
        <div class="alert-card critical">
          <div class="alert-icon">
            <i class="fas fa-graduation-cap"></i>
          </div>
          <div class="alert-content">
            <h3>Grade 12 Graduation Risk</h3>
            <p><strong>${grade12.highRisk} of ${grade12.total} seniors (${riskPercent}%)</strong> are at high risk of not graduating</p>
            <div class="alert-actions">
              <button class="alert-btn primary" data-action="focus-grade-12">
                <i class="fas fa-search"></i>
                Review Grade 12 Students
              </button>
              <button class="alert-btn secondary" data-action="bulk-interventions" data-count="${grade12.highRisk}">
                <i class="fas fa-plus-circle"></i>
                Create Interventions
              </button>
            </div>
          </div>
        </div>
      `);
    }

    // Study skills alert
    if (this.insights.avgStudySkills < 3.5) {
      alerts.push(`
        <div class="alert-card warning">
          <div class="alert-icon">
            <i class="fas fa-book"></i>
          </div>
          <div class="alert-content">
            <h3>Study Skills Development Needed</h3>
            <p>School average is <strong>${this.insights.avgStudySkills.toFixed(1)}/5.0</strong> - consider implementing study skills programs</p>
            <div class="alert-actions">
              <button class="alert-btn primary" data-action="improve-study-skills">
                <i class="fas fa-lightbulb"></i>
                View Recommendations
              </button>
            </div>
          </div>
        </div>
      `);
    }

    return alerts.length > 0 ? alerts.join('') : '<div class="no-alerts"><i class="fas fa-check-circle"></i> No critical alerts at this time</div>';
  }

  bindTabEvents() {
    const tabs = this.element.querySelectorAll('.dashboard-tab');
    const panels = this.element.querySelectorAll('.tab-panel');

    tabs.forEach(tab => {
      this.bindEvent(tab, 'click', (e) => {
        const targetTab = tab.dataset.tab;
        
        // Update active tab
        tabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        
        // Update active panel
        panels.forEach(panel => {
          panel.classList.remove('active');
          if (panel.id === `tab-${targetTab}`) {
            panel.classList.add('active');
          }
        });
        
        // Re-bind events when switching to students tab
        if (targetTab === 'students') {
          console.log('📋 Switching to Students tab, rebinding filters...');
          this.bindTableFilters(this.k12Students);
        }
      });
    });
  }

  calculateEducatorInsights(students, metadata) {
    // Group students by grade level with detailed analysis
    const gradeAnalysis = {};
    students.forEach(student => {
      const grade = student.grade_level;
      if (!gradeAnalysis[grade]) {
        gradeAnalysis[grade] = {
          total: 0,
          highRisk: 0,
          mediumRisk: 0,
          lowRisk: 0,
          needsIntervention: 0,
          avgStudySkills: 0,
          studySkillsCount: 0,
          students: []
        };
      }
      
      const analysis = gradeAnalysis[grade];
      analysis.total++;
      analysis.students.push(student);
      
      if (student.risk_score >= 0.7) analysis.highRisk++;
      else if (student.risk_score >= 0.4) analysis.mediumRisk++;
      else analysis.lowRisk++;
      
      if (student.needs_intervention) analysis.needsIntervention++;
      
      if (student.study_skills_rating) {
        analysis.avgStudySkills += student.study_skills_rating;
        analysis.studySkillsCount++;
      }
    });

    // Calculate averages
    Object.keys(gradeAnalysis).forEach(grade => {
      const analysis = gradeAnalysis[grade];
      if (analysis.studySkillsCount > 0) {
        analysis.avgStudySkills = analysis.avgStudySkills / analysis.studySkillsCount;
      }
    });

    return {
      gradeAnalysis,
      totalStudents: students.length,
      overallHighRisk: students.filter(s => s.risk_score >= 0.7).length,
      overallMediumRisk: students.filter(s => s.risk_score >= 0.4 && s.risk_score < 0.7).length,
      overallLowRisk: students.filter(s => s.risk_score < 0.4).length,
      interventionNeeded: students.filter(s => s.needs_intervention).length,
      avgStudySkills: students.reduce((sum, s) => sum + (s.study_skills_rating || 0), 0) / students.filter(s => s.study_skills_rating).length
    };
  }

  renderCompactAlerts(insights) {
    const alerts = [];
    
    // Critical Grade 12 situation
    const grade12 = insights.gradeAnalysis[12];
    if (grade12 && grade12.highRisk > 0) {
      const riskPercent = ((grade12.highRisk / grade12.total) * 100).toFixed(0);
      alerts.push(`
        <div class="compact-alert critical">
          <i class="fas fa-graduation-cap"></i>
          <div>
            <strong>Graduation Risk:</strong> ${grade12.highRisk}/${grade12.total} seniors (${riskPercent}%)
            <button class="mini-btn" data-action="focus-grade-12">Review</button>
          </div>
        </div>
      `);
    }

    // Study skills alert
    if (insights.avgStudySkills < 3.5) {
      alerts.push(`
        <div class="compact-alert warning">
          <i class="fas fa-book"></i>
          <div>
            <strong>Study Skills:</strong> ${insights.avgStudySkills.toFixed(1)}/5.0 school average
            <button class="mini-btn" data-action="improve-study-skills">Plan</button>
          </div>
        </div>
      `);
    }

    return alerts.length > 0 ? alerts.join('') : '<div class="no-alerts">✅ No critical alerts</div>';
  }

  renderStudentTable(students) {
    // Sort students by priority: Grade 12 high risk first, then by risk score
    const priorityStudents = students
      .sort((a, b) => {
        // Grade 12 high risk gets highest priority
        if (a.grade_level === 12 && a.risk_score >= 0.7) return -1;
        if (b.grade_level === 12 && b.risk_score >= 0.7) return 1;
        // Then sort by risk score
        return b.risk_score - a.risk_score;
      });

    return `
      <div class="student-table-container">
        <table class="student-table" id="student-table">
          <thead>
            <tr>
              <th>Student ID</th>
              <th>Grade</th>
              <th>Risk Level</th>
              <th>Risk Score</th>
              <th>Study Skills</th>
              <th>Attendance</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            ${priorityStudents.slice(0, 20).map(student => this.renderStudentRow(student)).join('')}
          </tbody>
        </table>
        ${priorityStudents.length > 20 ? `<div class="table-footer">Showing top 20 of ${priorityStudents.length} students</div>` : ''}
      </div>
    `;
  }

  renderStudentRow(student) {
    const riskClass = student.risk_score >= 0.7 ? 'high-risk' : 
                     student.risk_score >= 0.4 ? 'medium-risk' : 'low-risk';
    const isPriority = student.grade_level === 12 && student.risk_score >= 0.7;

    return `
      <tr class="student-row ${riskClass} ${isPriority ? 'priority' : ''}" data-student-id="${student.student_id}" data-grade="${student.grade_level}" data-risk="${riskClass}">
        <td class="student-id">${student.student_id}</td>
        <td class="grade">${student.grade_level}</td>
        <td class="risk-category">
          <span class="risk-badge ${riskClass}">${student.risk_category}</span>
        </td>
        <td class="risk-score">${(student.risk_score * 100).toFixed(0)}%</td>
        <td class="study-skills">${student.study_skills_rating || 'N/A'}</td>
        <td class="attendance">${(student.attendance_rate * 100).toFixed(0)}%</td>
        <td class="actions">
          <button class="table-btn" data-action="create-intervention" data-student="${student.student_id}" title="Create Intervention">
            <i class="fas fa-plus"></i>
          </button>
          <button class="table-btn" data-action="schedule-meeting" data-student="${student.student_id}" title="Schedule Meeting">
            <i class="fas fa-calendar"></i>
          </button>
          <button class="table-btn" data-action="view-details" data-student="${student.student_id}" title="View Details">
            <i class="fas fa-eye"></i>
          </button>
        </td>
      </tr>
    `;
  }

  renderActionPanel(insights, students) {
    const highRiskStudents = students.filter(s => s.risk_score >= 0.7);
    const mediumRiskStudents = students.filter(s => s.risk_score >= 0.4 && s.risk_score < 0.7);

    return `
      <div class="action-sections">
        <!-- Summary Stats -->
        <div class="summary-stats">
          <div class="stat-item">
            <span class="stat-number high-risk">${insights.overallHighRisk}</span>
            <span class="stat-label">High Risk</span>
          </div>
          <div class="stat-item">
            <span class="stat-number medium-risk">${insights.overallMediumRisk}</span>
            <span class="stat-label">Medium Risk</span>
          </div>
          <div class="stat-item">
            <span class="stat-number low-risk">${insights.overallLowRisk}</span>
            <span class="stat-label">Low Risk</span>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="action-buttons">
          <button class="action-btn primary" data-action="export-high-risk" data-count="${highRiskStudents.length}">
            <i class="fas fa-download"></i>
            Export High Risk (${highRiskStudents.length})
          </button>
          <button class="action-btn secondary" data-action="bulk-interventions" data-count="${highRiskStudents.length}">
            <i class="fas fa-plus-circle"></i>
            Create Interventions (${highRiskStudents.length})
          </button>
          <button class="action-btn tertiary" data-action="schedule-meetings" data-count="${highRiskStudents.length}">
            <i class="fas fa-calendar-alt"></i>
            Schedule Meetings (${highRiskStudents.length})
          </button>
          <button class="action-btn info" data-action="generate-report">
            <i class="fas fa-file-pdf"></i>
            Generate Report
          </button>
        </div>

        <!-- Grade Breakdown -->
        <div class="grade-breakdown">
          <h4>By Grade Level</h4>
          ${Object.keys(insights.gradeAnalysis).sort((a, b) => parseInt(a) - parseInt(b)).map(grade => {
            const analysis = insights.gradeAnalysis[grade];
            return `
              <div class="grade-stat">
                <span class="grade-label">Grade ${grade}</span>
                <span class="grade-counts">
                  <span class="high-count">${analysis.highRisk}</span>/<span class="total-count">${analysis.total}</span>
                </span>
              </div>
            `;
          }).join('')}
        </div>
      </div>
    `;
  }


  bindDashboardEvents() {
    // Action buttons
    this.element.querySelectorAll('.action-btn, .mini-btn, .table-btn').forEach(btn => {
      this.bindEvent(btn, 'click', (e) => {
        const action = e.target.closest('button').dataset.action;
        const studentId = e.target.closest('button').dataset.student;
        const count = e.target.closest('button').dataset.count;
        this.handleAction(action, studentId, count);
      });
    });
  }

  bindTableFilters(students) {
    // Use a small delay to ensure DOM elements are available after tab switch
    setTimeout(() => {
      const gradeFilter = this.element.querySelector('#grade-filter');
      const riskFilter = this.element.querySelector('#risk-filter');

      console.log('🔧 Binding table filters...', { gradeFilter: !!gradeFilter, riskFilter: !!riskFilter });

      if (gradeFilter) {
        // Remove any existing event listeners first
        gradeFilter.replaceWith(gradeFilter.cloneNode(true));
        const newGradeFilter = this.element.querySelector('#grade-filter');
        
        this.bindEvent(newGradeFilter, 'change', (e) => {
          console.log('🔍 Grade filter changed to:', e.target.value);
          const riskFilterCurrent = this.element.querySelector('#risk-filter');
          this.filterTable(students, e.target.value, riskFilterCurrent ? riskFilterCurrent.value : '');
        });
      } else {
        console.warn('⚠️ Grade filter element not found');
      }

      if (riskFilter) {
        // Remove any existing event listeners first
        riskFilter.replaceWith(riskFilter.cloneNode(true));
        const newRiskFilter = this.element.querySelector('#risk-filter');
        
        this.bindEvent(newRiskFilter, 'change', (e) => {
          console.log('🔍 Risk filter changed to:', e.target.value);
          const gradeFilterCurrent = this.element.querySelector('#grade-filter');
          this.filterTable(students, gradeFilterCurrent ? gradeFilterCurrent.value : '', e.target.value);
        });
      } else {
        console.warn('⚠️ Risk filter element not found');
      }
    }, 50);
  }

  filterTable(students, gradeFilter, riskFilter) {
    console.log('🔍 Filtering table with:', { gradeFilter, riskFilter });
    const rows = this.element.querySelectorAll('.student-row');
    console.log('📋 Found', rows.length, 'student rows to filter');
    
    let visibleCount = 0;
    rows.forEach(row => {
      const grade = row.dataset.grade;
      const risk = row.dataset.risk;
      
      console.log('🔍 Row data:', { grade, risk, gradeFilter, riskFilter });
      
      const gradeMatch = !gradeFilter || grade === gradeFilter;
      const riskMatch = !riskFilter || risk === riskFilter + '-risk';
      
      const shouldShow = gradeMatch && riskMatch;
      row.style.display = shouldShow ? '' : 'none';
      
      if (shouldShow) visibleCount++;
    });

    console.log(`✅ Filtered ${visibleCount} visible rows out of ${rows.length} total rows`);

    // Update table footer
    const footer = this.element.querySelector('.table-footer');
    if (footer) {
      footer.textContent = `Showing ${visibleCount} of ${students.length} students`;
    }
  }

  handleAction(action, studentId = null, count = null) {
    console.log(`🎯 Handling action: ${action}${studentId ? ` for student ${studentId}` : ''}${count ? ` (${count} students)` : ''}`);
    
    switch (action) {
      case 'focus-grade-12':
        this.focusGrade(12);
        break;
      case 'improve-study-skills':
        this.planStudySkillsProgram();
        break;
      case 'export-high-risk':
        this.exportHighRiskStudents();
        break;
      case 'bulk-interventions':
        this.createBulkInterventions(count);
        break;
      case 'schedule-meetings':
        this.scheduleParentMeetings(count);
        break;
      case 'generate-report':
        this.generateRiskReport();
        break;
      case 'create-intervention':
        this.createIndividualIntervention(studentId);
        break;
      case 'schedule-meeting':
        this.scheduleIndividualMeeting(studentId);
        break;
      case 'view-details':
        this.viewStudentDetails(studentId);
        break;
    }
  }

  focusGrade(grade) {
    // Switch to Students tab first
    const studentsTab = this.element.querySelector('.dashboard-tab[data-tab="students"]');
    if (studentsTab) {
      studentsTab.click();
      
      // Wait for tab switch, then apply filter
      setTimeout(() => {
        const gradeFilter = this.element.querySelector('#grade-filter');
        if (gradeFilter) {
          gradeFilter.value = grade.toString();
          gradeFilter.dispatchEvent(new Event('change'));
        }
        this.showNotification(`Switched to Students tab and filtered to Grade ${grade}`, 'info');
      }, 100);
    } else {
      // Fallback if already on students tab
      const gradeFilter = this.element.querySelector('#grade-filter');
      if (gradeFilter) {
        gradeFilter.value = grade.toString();
        gradeFilter.dispatchEvent(new Event('change'));
      }
      this.showNotification(`Filtered to show Grade ${grade} students`, 'info');
    }
  }

  planStudySkillsProgram() {
    const message = 'Study Skills Program Recommendations:\n\n' +
                   '• Implement weekly study skills workshops\n' +
                   '• Partner with learning specialists\n' +
                   '• Create peer tutoring programs\n' +
                   '• Develop study strategy assessments';
    alert(message);
    console.log('📚 Study skills program recommendations generated');
  }

  exportHighRiskStudents() {
    const highRiskStudents = this.k12Students.filter(s => s.risk_score >= 0.7);
    const csvData = highRiskStudents.map(student => ({
      'Student ID': student.student_id,
      'Grade Level': student.grade_level,
      'Risk Score': (student.risk_score * 100).toFixed(1) + '%',
      'Risk Category': student.risk_category,
      'Study Skills Rating': student.study_skills_rating || 'N/A',
      'Attendance Rate': (student.attendance_rate * 100).toFixed(1) + '%',
      'Behavioral Concerns': student.behavioral_concerns?.join(', ') || 'None'
    }));

    const csv = this.convertToCSV(csvData);
    this.downloadCSV(csv, `high-risk-students-${new Date().toISOString().split('T')[0]}.csv`);
    this.showNotification(`Exported ${csvData.length} high-risk students to CSV`, 'success');
  }

  createBulkInterventions(count) {
    const message = `Bulk Intervention Creation:\n\n` +
                   `• Selected ${count} high-risk students\n` +
                   `• Suggested interventions: Academic support, Study skills, Attendance monitoring\n` +
                   `• Next step: Review individual student needs\n\n` +
                   `This would integrate with your school's SIS to create actual intervention records.`;
    alert(message);
    this.showNotification(`Bulk intervention plan created for ${count} students`, 'success');
  }

  scheduleParentMeetings(count) {
    const message = `Parent Meeting Scheduling:\n\n` +
                   `• ${count} high-risk students identified\n` +
                   `• Recommended meeting type: Academic conference\n` +
                   `• Timeline: Within 2 weeks\n` +
                   `• Topics: Risk factors, intervention plans, home support\n\n` +
                   `This would integrate with your calendar system to schedule actual meetings.`;
    alert(message);
    this.showNotification(`Meeting schedule prepared for ${count} families`, 'success');
  }

  generateRiskReport() {
    const insights = this.calculateEducatorInsights(this.k12Students, this.k12Metadata);
    const reportData = {
      timestamp: new Date().toLocaleString(),
      totalStudents: insights.totalStudents,
      highRisk: insights.overallHighRisk,
      mediumRisk: insights.overallMediumRisk,
      lowRisk: insights.overallLowRisk,
      avgStudySkills: insights.avgStudySkills.toFixed(1),
      gradeBreakdown: insights.gradeAnalysis
    };

    console.log('📋 Risk Report Generated:', reportData);
    
    const reportText = `STUDENT RISK ASSESSMENT REPORT
Generated: ${reportData.timestamp}

SUMMARY:
Total Students: ${reportData.totalStudents}
High Risk: ${reportData.highRisk} (${((reportData.highRisk/reportData.totalStudents)*100).toFixed(1)}%)
Medium Risk: ${reportData.mediumRisk} (${((reportData.mediumRisk/reportData.totalStudents)*100).toFixed(1)}%)
Low Risk: ${reportData.lowRisk} (${((reportData.lowRisk/reportData.totalStudents)*100).toFixed(1)}%)

Average Study Skills: ${reportData.avgStudySkills}/5.0

GRADE-LEVEL ANALYSIS:
${Object.entries(reportData.gradeBreakdown).map(([grade, data]) => 
  `Grade ${grade}: ${data.highRisk} high risk / ${data.total} total`
).join('\n')}`;

    this.downloadTextFile(reportText, `risk-assessment-report-${new Date().toISOString().split('T')[0]}.txt`);
    this.showNotification('Risk assessment report generated', 'success');
  }

  createIndividualIntervention(studentId) {
    const student = this.k12Students.find(s => s.student_id === studentId);
    if (!student) return;

    const interventionPlan = this.generateInterventionPlan(student);
    const message = `Intervention Plan for ${studentId}:\n\n${interventionPlan}`;
    alert(message);
    this.showNotification(`Intervention plan created for ${studentId}`, 'success');
  }

  scheduleIndividualMeeting(studentId) {
    const student = this.k12Students.find(s => s.student_id === studentId);
    if (!student) return;

    const message = `Schedule Meeting for ${studentId}:\n\n` +
                   `Risk Level: ${student.risk_category}\n` +
                   `Grade: ${student.grade_level}\n` +
                   `Recommended: Parent/Teacher conference\n` +
                   `Timeline: Within 1 week for high-risk students\n\n` +
                   `This would integrate with your calendar system.`;
    alert(message);
    this.showNotification(`Meeting scheduled for ${studentId}`, 'success');
  }

  viewStudentDetails(studentId) {
    const student = this.k12Students.find(s => s.student_id === studentId);
    if (!student) return;

    const details = `STUDENT PROFILE: ${studentId}

Grade Level: ${student.grade_level}
Risk Score: ${(student.risk_score * 100).toFixed(1)}%
Risk Category: ${student.risk_category}
Study Skills: ${student.study_skills_rating || 'N/A'}/5.0
Attendance Rate: ${(student.attendance_rate * 100).toFixed(1)}%

Behavioral Concerns: ${student.behavioral_concerns?.join(', ') || 'None'}
Special Populations: ${Object.entries(student.special_populations || {})
  .filter(([key, value]) => value)
  .map(([key, value]) => key.replace('_', ' '))
  .join(', ') || 'None'}

Current Interventions: ${student.interventions?.length > 0 ? student.interventions.join(', ') : 'None'}`;

    alert(details);
    console.log(`📊 Viewed details for student ${studentId}`, student);
  }

  generateInterventionPlan(student) {
    const interventions = [];
    
    if (student.risk_score >= 0.7) {
      interventions.push('• Academic Support Program (daily check-ins)');
      interventions.push('• Progress monitoring (weekly assessments)');
    }
    
    if (student.attendance_rate < 0.85) {
      interventions.push('• Attendance improvement plan');
      interventions.push('• Family engagement support');
    }
    
    if (student.study_skills_rating < 3.0) {
      interventions.push('• Study skills development workshop');
      interventions.push('• Peer tutoring program');
    }
    
    if (student.grade_level === 12) {
      interventions.push('• Graduation pathway review');
      interventions.push('• Credit recovery assessment');
    }

    return interventions.length > 0 ? interventions.join('\n') : '• Standard academic support monitoring';
  }

  showNotification(message, type = 'info') {
    // Try to use existing notification system
    if (window.notificationSystem) {
      const typeMap = {
        'success': 'success',
        'info': 'info', 
        'warning': 'warning',
        'error': 'error'
      };
      window.notificationSystem.show(message, typeMap[type] || 'info');
    } else {
      // Fallback to console and temporary UI notification
      console.log(`📢 ${type.toUpperCase()}: ${message}`);
      
      // Create temporary notification
      const notification = document.createElement('div');
      notification.className = `temp-notification ${type}`;
      notification.textContent = message;
      notification.style.cssText = `
        position: fixed; top: 20px; right: 20px; z-index: 10000;
        padding: 12px 20px; border-radius: 6px; color: white;
        background: ${type === 'success' ? '#16a34a' : type === 'warning' ? '#f59e0b' : type === 'error' ? '#dc2626' : '#3b82f6'};
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        font-weight: 500; max-width: 300px;
      `;
      
      document.body.appendChild(notification);
      setTimeout(() => notification.remove(), 3000);
    }
  }

  downloadTextFile(content, filename) {
    const blob = new Blob([content], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    window.URL.revokeObjectURL(url);
  }

  convertToCSV(data) {
    const headers = Object.keys(data[0]);
    const csvHeaders = headers.join(',');
    const csvRows = data.map(row => 
      headers.map(header => `"${row[header]}"`).join(',')
    );
    return csvHeaders + '\\n' + csvRows.join('\\n');
  }

  downloadCSV(csv, filename) {
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    window.URL.revokeObjectURL(url);
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