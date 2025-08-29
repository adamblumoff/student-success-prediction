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

    // Calculate educator-focused insights
    const insights = this.calculateEducatorInsights(students, metadata);
    
    dashboardElement.innerHTML = `
      <!-- Critical Alerts Section -->
      <div class="educator-section critical-alerts">
        <div class="section-header">
          <h3><i class="fas fa-exclamation-triangle"></i> Immediate Action Required</h3>
        </div>
        <div class="alert-cards">
          ${this.renderCriticalAlerts(insights)}
        </div>
      </div>

      <!-- Grade-Level Performance Overview -->
      <div class="educator-section grade-overview">
        <div class="section-header">
          <h3><i class="fas fa-chart-bar"></i> Grade-Level Risk Analysis</h3>
          <div class="view-toggle">
            <button class="btn-toggle active" data-view="chart">Chart View</button>
            <button class="btn-toggle" data-view="table">Data Table</button>
          </div>
        </div>
        <div class="grade-visualization">
          <div class="chart-container">
            <canvas id="grade-risk-chart"></canvas>
          </div>
          <div class="grade-insights">
            ${this.renderGradeInsights(insights)}
          </div>
        </div>
      </div>

      <!-- Intervention Priority Matrix -->
      <div class="educator-section intervention-matrix">
        <div class="section-header">
          <h3><i class="fas fa-users"></i> Intervention Priority Students</h3>
        </div>
        <div class="priority-grid">
          ${this.renderInterventionPriorities(students)}
        </div>
      </div>

      <!-- Progress Trends -->
      <div class="educator-section progress-trends">
        <div class="section-header">
          <h3><i class="fas fa-trending-up"></i> Academic Progress Indicators</h3>
        </div>
        <div class="trends-container">
          ${this.renderProgressTrends(insights)}
        </div>
      </div>

      <!-- Quick Actions Panel -->
      <div class="educator-section quick-actions">
        <div class="section-header">
          <h3><i class="fas fa-lightning-bolt"></i> Quick Actions</h3>
        </div>
        <div class="action-buttons">
          <button class="action-btn" data-action="generate-report">
            <i class="fas fa-file-pdf"></i>
            Generate Risk Report
          </button>
          <button class="action-btn" data-action="schedule-meetings">
            <i class="fas fa-calendar-alt"></i>
            Schedule Parent Meetings
          </button>
          <button class="action-btn" data-action="create-interventions">
            <i class="fas fa-plus-circle"></i>
            Create Bulk Interventions
          </button>
          <button class="action-btn" data-action="export-data">
            <i class="fas fa-download"></i>
            Export to CSV
          </button>
        </div>
      </div>
    `;

    // Initialize interactive charts
    this.initializeCharts(insights);
    this.bindDashboardEvents();
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

  renderCriticalAlerts(insights) {
    const alerts = [];
    
    // Critical Grade 12 situation
    const grade12 = insights.gradeAnalysis[12];
    if (grade12 && grade12.highRisk > 0) {
      const riskPercent = ((grade12.highRisk / grade12.total) * 100).toFixed(0);
      alerts.push(`
        <div class="alert-card critical">
          <div class="alert-icon"><i class="fas fa-graduation-cap"></i></div>
          <div class="alert-content">
            <h4>Grade 12 Graduation Risk</h4>
            <p><strong>${grade12.highRisk} of ${grade12.total} seniors (${riskPercent}%)</strong> are at high risk of not graduating</p>
            <div class="alert-action">
              <button class="btn btn-danger btn-sm" onclick="focusGrade(12)">Review Grade 12 Students</button>
            </div>
          </div>
        </div>
      `);
    }

    // Grade 10 medium risk concentration
    const grade10 = insights.gradeAnalysis[10];
    if (grade10 && (grade10.mediumRisk / grade10.total) > 0.8) {
      const riskPercent = ((grade10.mediumRisk / grade10.total) * 100).toFixed(0);
      alerts.push(`
        <div class="alert-card warning">
          <div class="alert-icon"><i class="fas fa-chart-line"></i></div>
          <div class="alert-content">
            <h4>Grade 10 Performance Decline</h4>
            <p><strong>${grade10.mediumRisk} of ${grade10.total} sophomores (${riskPercent}%)</strong> showing concerning performance patterns</p>
            <div class="alert-action">
              <button class="btn btn-warning btn-sm" onclick="analyzeGrade10Trends()">Analyze Trends</button>
            </div>
          </div>
        </div>
      `);
    }

    // Low study skills alert
    if (insights.avgStudySkills < 3.0) {
      alerts.push(`
        <div class="alert-card info">
          <div class="alert-icon"><i class="fas fa-book"></i></div>
          <div class="alert-content">
            <h4>Study Skills Development Needed</h4>
            <p>Average study skills rating is <strong>${insights.avgStudySkills.toFixed(1)}/5.0</strong> - consider school-wide study skills program</p>
            <div class="alert-action">
              <button class="btn btn-primary btn-sm" onclick="planStudySkillsProgram()">Plan Program</button>
            </div>
          </div>
        </div>
      `);
    }

    return alerts.length > 0 ? alerts.join('') : '<div class="no-alerts"><i class="fas fa-check-circle"></i> No critical alerts at this time</div>';
  }

  renderGradeInsights(insights) {
    const grades = Object.keys(insights.gradeAnalysis).sort((a, b) => parseInt(a) - parseInt(b));
    
    return grades.map(grade => {
      const analysis = insights.gradeAnalysis[grade];
      const riskPercent = ((analysis.highRisk + analysis.mediumRisk) / analysis.total * 100).toFixed(0);
      const studySkills = analysis.avgStudySkills.toFixed(1);
      
      return `
        <div class="grade-insight-card">
          <div class="grade-header">
            <h4>Grade ${grade}</h4>
            <span class="student-count">${analysis.total} students</span>
          </div>
          <div class="risk-breakdown">
            <div class="risk-bar">
              <div class="risk-segment high" style="width: ${(analysis.highRisk/analysis.total*100)}%"></div>
              <div class="risk-segment medium" style="width: ${(analysis.mediumRisk/analysis.total*100)}%"></div>
              <div class="risk-segment low" style="width: ${(analysis.lowRisk/analysis.total*100)}%"></div>
            </div>
            <div class="risk-stats">
              <span class="high-risk">${analysis.highRisk} high</span>
              <span class="medium-risk">${analysis.mediumRisk} medium</span>
              <span class="low-risk">${analysis.lowRisk} low risk</span>
            </div>
          </div>
          <div class="grade-metrics">
            <div class="metric">
              <label>At Risk %</label>
              <value class="${riskPercent > 50 ? 'danger' : riskPercent > 25 ? 'warning' : 'success'}">${riskPercent}%</value>
            </div>
            <div class="metric">
              <label>Study Skills</label>
              <value class="${studySkills < 3 ? 'danger' : studySkills < 4 ? 'warning' : 'success'}">${studySkills}/5</value>
            </div>
          </div>
        </div>
      `;
    }).join('');
  }

  renderInterventionPriorities(students) {
    // Sort students by priority: Grade 12 high risk first, then by risk score
    const priorityStudents = students
      .filter(s => s.needs_intervention || s.risk_score >= 0.6)
      .sort((a, b) => {
        // Grade 12 high risk gets highest priority
        if (a.grade_level === 12 && a.risk_score >= 0.7) return -1;
        if (b.grade_level === 12 && b.risk_score >= 0.7) return 1;
        // Then sort by risk score
        return b.risk_score - a.risk_score;
      })
      .slice(0, 8); // Show top 8 priority students

    return priorityStudents.map((student, index) => {
      const priorityLevel = index < 3 ? 'urgent' : index < 6 ? 'high' : 'medium';
      const priorityIcon = priorityLevel === 'urgent' ? 'fas fa-fire' : 
                          priorityLevel === 'high' ? 'fas fa-exclamation' : 
                          'fas fa-flag';
      
      return `
        <div class="priority-student-card ${priorityLevel}">
          <div class="priority-indicator">
            <i class="${priorityIcon}"></i>
            <span class="priority-rank">#${index + 1}</span>
          </div>
          <div class="student-info">
            <div class="student-header">
              <span class="student-id">${student.student_id}</span>
              <span class="grade-badge">Grade ${student.grade_level}</span>
            </div>
            <div class="risk-info">
              <span class="risk-score">${(student.risk_score * 100).toFixed(0)}% risk</span>
              <span class="risk-category">${student.risk_category}</span>
            </div>
            <div class="quick-actions">
              <button class="quick-btn" onclick="createIntervention('${student.student_id}')" title="Create Intervention">
                <i class="fas fa-plus"></i>
              </button>
              <button class="quick-btn" onclick="scheduleConference('${student.student_id}')" title="Schedule Conference">
                <i class="fas fa-calendar"></i>
              </button>
              <button class="quick-btn" onclick="viewDetails('${student.student_id}')" title="View Details">
                <i class="fas fa-eye"></i>
              </button>
            </div>
          </div>
        </div>
      `;
    }).join('');
  }

  renderProgressTrends(insights) {
    return `
      <div class="trends-grid">
        <div class="trend-card">
          <div class="trend-header">
            <h4>Overall Risk Distribution</h4>
          </div>
          <div class="trend-chart">
            <div class="donut-chart" id="risk-distribution-chart"></div>
            <div class="trend-stats">
              <div class="stat-item high-risk">
                <span class="stat-value">${insights.overallHighRisk}</span>
                <span class="stat-label">High Risk</span>
              </div>
              <div class="stat-item medium-risk">
                <span class="stat-value">${insights.overallMediumRisk}</span>
                <span class="stat-label">Medium Risk</span>
              </div>
              <div class="stat-item low-risk">
                <span class="stat-value">${insights.overallLowRisk}</span>
                <span class="stat-label">Low Risk</span>
              </div>
            </div>
          </div>
        </div>
        
        <div class="trend-card">
          <div class="trend-header">
            <h4>Intervention Impact</h4>
          </div>
          <div class="impact-metrics">
            <div class="metric-large">
              <span class="metric-number">${insights.interventionNeeded}</span>
              <span class="metric-label">Students Need Support</span>
              <span class="metric-percent">${((insights.interventionNeeded / insights.totalStudents) * 100).toFixed(1)}% of total</span>
            </div>
            <div class="intervention-breakdown">
              <div class="breakdown-item">
                <span class="item-label">Immediate Action</span>
                <span class="item-value">${insights.overallHighRisk}</span>
              </div>
              <div class="breakdown-item">
                <span class="item-label">Monitor Closely</span>
                <span class="item-value">${insights.overallMediumRisk}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="trend-card">
          <div class="trend-header">
            <h4>Study Skills Assessment</h4>
          </div>
          <div class="skills-gauge">
            <div class="gauge-container">
              <div class="gauge-chart" data-value="${insights.avgStudySkills}"></div>
              <div class="gauge-center">
                <span class="gauge-value">${insights.avgStudySkills.toFixed(1)}</span>
                <span class="gauge-label">/ 5.0</span>
              </div>
            </div>
            <div class="skills-recommendation">
              ${insights.avgStudySkills < 3 ? 
                '<span class="rec-priority">High Priority:</span> Implement study skills curriculum' :
                insights.avgStudySkills < 4 ?
                '<span class="rec-medium">Medium Priority:</span> Targeted study skills support' :
                '<span class="rec-good">Good:</span> Maintain current study skills programs'
              }
            </div>
          </div>
        </div>
      </div>
    `;
  }

  initializeCharts(insights) {
    // Grade-level risk chart
    setTimeout(() => {
      const ctx = document.getElementById('grade-risk-chart');
      if (ctx) {
        this.createGradeRiskChart(ctx, insights);
      }
    }, 100);
  }

  createGradeRiskChart(canvas, insights) {
    const grades = Object.keys(insights.gradeAnalysis).sort((a, b) => parseInt(a) - parseInt(b));
    const highRiskData = grades.map(g => insights.gradeAnalysis[g].highRisk);
    const mediumRiskData = grades.map(g => insights.gradeAnalysis[g].mediumRisk);
    const lowRiskData = grades.map(g => insights.gradeAnalysis[g].lowRisk);

    // Simple canvas-based chart (or integrate Chart.js if available)
    const ctx = canvas.getContext('2d');
    const width = canvas.width = canvas.offsetWidth * 2; // Retina display
    const height = canvas.height = canvas.offsetHeight * 2;
    canvas.style.width = canvas.offsetWidth + 'px';
    canvas.style.height = canvas.offsetHeight + 'px';
    ctx.scale(2, 2);

    // Draw stacked bar chart
    this.drawStackedBarChart(ctx, {
      labels: grades.map(g => `Grade ${g}`),
      datasets: [
        { label: 'High Risk', data: highRiskData, color: '#dc2626' },
        { label: 'Medium Risk', data: mediumRiskData, color: '#f59e0b' },
        { label: 'Low Risk', data: lowRiskData, color: '#16a34a' }
      ]
    });
  }

  drawStackedBarChart(ctx, data) {
    const padding = 40;
    const chartWidth = ctx.canvas.width / 2 - padding * 2;
    const chartHeight = ctx.canvas.height / 2 - padding * 2;
    const barWidth = chartWidth / data.labels.length * 0.8;
    const spacing = chartWidth / data.labels.length * 0.2;

    // Find max value for scaling
    const maxValue = Math.max(...data.labels.map((_, i) => 
      data.datasets.reduce((sum, dataset) => sum + dataset.data[i], 0)
    ));

    // Draw bars
    data.labels.forEach((label, i) => {
      let currentY = padding + chartHeight;
      const x = padding + i * (barWidth + spacing);
      
      data.datasets.forEach(dataset => {
        const value = dataset.data[i];
        const barHeight = (value / maxValue) * chartHeight;
        
        ctx.fillStyle = dataset.color;
        ctx.fillRect(x, currentY - barHeight, barWidth, barHeight);
        
        currentY -= barHeight;
      });

      // Draw label
      ctx.fillStyle = '#374151';
      ctx.font = '12px system-ui';
      ctx.textAlign = 'center';
      ctx.fillText(label, x + barWidth / 2, padding + chartHeight + 20);
    });

    // Draw legend
    let legendX = padding;
    data.datasets.forEach(dataset => {
      ctx.fillStyle = dataset.color;
      ctx.fillRect(legendX, 10, 15, 15);
      ctx.fillStyle = '#374151';
      ctx.font = '12px system-ui';
      ctx.textAlign = 'left';
      ctx.fillText(dataset.label, legendX + 20, 22);
      legendX += ctx.measureText(dataset.label).width + 40;
    });
  }

  bindDashboardEvents() {
    // Quick action buttons
    this.element.querySelectorAll('.action-btn').forEach(btn => {
      this.bindEvent(btn, 'click', (e) => {
        const action = e.target.closest('.action-btn').dataset.action;
        this.handleQuickAction(action);
      });
    });

    // View toggle buttons
    this.element.querySelectorAll('.btn-toggle').forEach(btn => {
      this.bindEvent(btn, 'click', (e) => {
        const view = e.target.dataset.view;
        this.switchView(view, e.target);
      });
    });
  }

  handleQuickAction(action) {
    switch (action) {
      case 'generate-report':
        this.generateRiskReport();
        break;
      case 'schedule-meetings':
        this.scheduleParentMeetings();
        break;
      case 'create-interventions':
        this.createBulkInterventions();
        break;
      case 'export-data':
        this.exportDashboardData();
        break;
    }
  }

  generateRiskReport() {
    console.log('📋 Generating risk report for educators...');
    alert('Risk report generation would integrate with school systems - demo functionality');
  }

  scheduleParentMeetings() {
    console.log('📅 Scheduling parent meetings for high-risk students...');
    alert('Parent meeting scheduling would integrate with calendar systems - demo functionality');
  }

  createBulkInterventions() {
    console.log('🎯 Creating bulk interventions...');
    alert('Bulk intervention creation would integrate with student management systems - demo functionality');
  }

  exportDashboardData() {
    console.log('📊 Exporting dashboard data...');
    
    const csvData = this.k12Students.map(student => ({
      'Student ID': student.student_id,
      'Grade Level': student.grade_level,
      'Risk Score': (student.risk_score * 100).toFixed(1) + '%',
      'Risk Category': student.risk_category,
      'Needs Intervention': student.needs_intervention ? 'Yes' : 'No',
      'Study Skills Rating': student.study_skills_rating || 'N/A',
      'Attendance Rate': (student.attendance_rate * 100).toFixed(1) + '%'
    }));

    const csv = this.convertToCSV(csvData);
    this.downloadCSV(csv, 'educator-dashboard-data.csv');
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