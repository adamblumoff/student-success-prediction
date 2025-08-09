/**
 * Analysis Component
 * Manages student analysis, filtering, and detailed views
 */

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
        // Remove selected class from all cards
        this.studentList.querySelectorAll('.student-card').forEach(c => c.classList.remove('selected'));
        
        // Add selected class to clicked card
        e.currentTarget.classList.add('selected');
        
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
