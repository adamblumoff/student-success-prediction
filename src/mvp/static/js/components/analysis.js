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
    
    // Make this component globally accessible for onclick handlers
    window.analysisComponent = this;
    
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
    const databaseId = student.id || student.database_id || studentId; // Use database ID for selections
    const risk = student.risk_score || student.success_probability || 0;
    const riskLevel = risk >= 0.7 ? 'high' : risk >= 0.4 ? 'medium' : 'low';
    const riskColor = riskLevel === 'high' ? 'var(--danger-500)' : 
                     riskLevel === 'medium' ? 'var(--warning-500)' : 
                     'var(--success-500)';
    
    const displayName = student.name || `Student ${studentId}`;
    
    return `
      <div class="student-card" data-student-id="${databaseId}" data-display-id="${studentId}">
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

  async updateStudentDetail(student) {
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
    this.loadStudentInterventions(student);
    
    // Check for cached Quick AI Insights
    const studentId = student.student_id || student.id || 'Unknown';
    const risk = student.risk_score || student.success_probability || 0;
    const riskLevel = risk >= 0.7 ? 'High Risk' : risk >= 0.4 ? 'Medium Risk' : 'Low Risk';
    await this.checkCachedInsights(studentId, riskLevel);
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
          <div class="detail-section gpt-insights" id="gpt-insights-${studentId}">
            <h4><i class="fas fa-lightbulb"></i> Quick AI Insights</h4>
            <div class="gpt-insights-content">
              <div class="loading-placeholder">
                <button class="btn btn-primary btn-small" onclick="window.analysisComponent?.loadQuickInsights('${studentId}', '${riskLevel}')" 
                        style="background: linear-gradient(135deg, #87ceeb 0%, #4fc3f7 100%); 
                               border: 1px solid #4fc3f7; 
                               color: white; 
                               box-shadow: 0 2px 4px rgba(79, 195, 247, 0.3);">
                  <i class="fas fa-brain"></i>
                  Generate Quick Insights
                </button>
              </div>
            </div>
          </div>
          
          <div class="detail-section">
            <h4><i class="fas fa-hands-helping"></i> Interventions</h4>
            <div class="interventions-header">
              <button class="btn btn-success btn-small" onclick="createIntervention('${student.id || student.student_id}')">
                <i class="fas fa-plus"></i>
                Create Intervention
              </button>
            </div>
            <div id="interventions-list-${studentId}" class="interventions-list">
              <div class="loading-spinner">Loading interventions...</div>
            </div>
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

  async loadStudentInterventions(student) {
    const studentId = student.id || student.student_id;
    const listContainer = document.getElementById(`interventions-list-${studentId}`);
    
    if (!listContainer) return;
    
    try {
      // Get authentication token
      const token = localStorage.getItem('auth_token');
      const response = await fetch(`/api/interventions/student/${studentId}`, {
        headers: {
          'Authorization': token ? `Bearer ${token}` : '',
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const interventions = await response.json();
        this.renderInterventions(interventions, listContainer);
      } else {
        listContainer.innerHTML = '<p class="text-muted">No interventions found</p>';
      }
    } catch (error) {
      console.error('Error loading interventions:', error);
      listContainer.innerHTML = '<p class="text-danger">Error loading interventions</p>';
    }
  }

  renderInterventions(interventions, container) {
    if (interventions.length === 0) {
      container.innerHTML = '<p class="text-muted">No interventions created yet</p>';
      return;
    }
    
    const html = interventions.map(intervention => this.renderInterventionCard(intervention)).join('');
    container.innerHTML = html;
  }

  renderInterventionCard(intervention) {
    const priorityColor = {
      'low': 'var(--success-500)',
      'medium': 'var(--warning-500)', 
      'high': 'var(--danger-500)',
      'critical': 'var(--danger-700)'
    }[intervention.priority] || 'var(--neutral-500)';
    
    const statusColor = {
      'pending': 'var(--warning-500)',
      'in_progress': 'var(--primary-500)',
      'completed': 'var(--success-500)',
      'cancelled': 'var(--neutral-500)'
    }[intervention.status] || 'var(--neutral-500)';
    
    const dueDateText = intervention.due_date ? 
      `Due: ${new Date(intervention.due_date).toLocaleDateString()}` : '';
    
    return `
      <div class="intervention-card" data-intervention-id="${intervention.id}">
        <div class="intervention-header">
          <h5 class="intervention-title">${intervention.title}</h5>
          <div class="intervention-badges">
            <span class="badge" style="background-color: ${priorityColor}">${intervention.priority}</span>
            <span class="badge" style="background-color: ${statusColor}">${intervention.status.replace('_', ' ')}</span>
          </div>
        </div>
        <div class="intervention-body">
          <p class="intervention-type"><strong>${this.formatInterventionType(intervention.intervention_type)}</strong></p>
          ${intervention.description ? `<p class="intervention-description">${intervention.description}</p>` : ''}
          ${intervention.assigned_to ? `<p class="intervention-assigned">Assigned to: ${intervention.assigned_to}</p>` : ''}
          ${dueDateText ? `<p class="intervention-due">${dueDateText}</p>` : ''}
        </div>
        <div class="intervention-actions">
          <button class="btn btn-sm btn-outline" onclick="updateInterventionStatus(${intervention.id}, '${intervention.status}')">
            <i class="fas fa-edit"></i>
            Update Status
          </button>
          <button class="btn btn-sm btn-outline" onclick="viewInterventionDetails(${intervention.id})">
            <i class="fas fa-eye"></i>
            Details
          </button>
        </div>
      </div>
    `;
  }

  formatInterventionType(type) {
    const types = {
      'academic_support': 'Academic Support',
      'attendance_support': 'Attendance Support',
      'behavioral_support': 'Behavioral Support',
      'engagement_support': 'Engagement Support',
      'family_engagement': 'Family Engagement',
      'college_career': 'College & Career',
      'health_wellness': 'Health & Wellness',
      'technology_support': 'Technology Support'
    };
    return types[type] || type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
  }

  async checkCachedInsights(studentId, riskLevel) {
    const container = document.getElementById(`gpt-insights-${studentId}`);
    if (!container) return;
    
    const contentDiv = container.querySelector('.gpt-insights-content');
    if (!contentDiv) return;
    
    // Generate data hash for cache invalidation
    const currentStudent = this.appState.getState().selectedStudent;
    const dataHash = await this.generateDataHash(studentId, currentStudent);
    
    // Check if we have cached insights with current data
    const cacheKey = `quick-insights-${studentId}-${riskLevel}-${dataHash}`;
    const cached = sessionStorage.getItem(cacheKey);
    
    // Clean old cache entries for this student (different data hashes)
    this.cleanOldCacheEntries(studentId, riskLevel, dataHash);
    
    if (cached) {
      console.log('✅ Displaying cached insights for student', studentId);
      const data = JSON.parse(cached);
      
      // Use formatted recommendations if available, otherwise fall back to raw insights
      const displayContent = data.formattedRecommendations || data.insights;
      
      contentDiv.innerHTML = `
        <div class="gpt-quick-insights" style="
          background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
          border-left: 3px solid #0ea5e9;
          padding: 15px;
          border-radius: 6px;
          margin-top: 10px;
        ">
          <div class="insights-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <div style="display: flex; align-items: center; gap: 8px;">
              <span style="font-weight: 600; color: #0369a1; font-size: 13px;">
                <i class="fas fa-lightbulb"></i> Quick AI Recommendations
              </span>
              <span style="
                background: #0ea5e9;
                color: white;
                font-size: 10px;
                padding: 2px 6px;
                border-radius: 10px;
                font-weight: 500;
              ">Personalized</span>
            </div>
            <button class="btn btn-outline btn-small" onclick="window.analysisComponent?.loadQuickInsights('${studentId}', '${riskLevel}')" 
                    style="font-size: 11px; padding: 2px 8px; border-color: #0ea5e9; color: #0ea5e9;">
              <i class="fas fa-sync-alt"></i> Refresh
            </button>
          </div>
          <div class="insights-content" style="
            font-size: 14px;
            line-height: 1.6;
            color: #0d0d0eff;
          ">
            ${displayContent}
          </div>
        </div>
      `;
    }
    // If no cached insights, keep the button (default HTML already shows button)
  }

  async generateDataHash(studentId, currentStudent) {
    // Get comprehensive student data including interventions
    const studentData = await this.getComprehensiveStudentData(studentId, 'Medium Risk'); // Risk level doesn't affect data hash
    
    // Create hash based on data that affects AI insights
    const relevantData = {
      interventions_count: studentData.interventions_count || 0,
      active_interventions_count: studentData.active_interventions_count || 0,
      recent_intervention_types: studentData.recent_intervention_types || '',
      recent_intervention_statuses: studentData.recent_intervention_statuses || '',
      gpa: studentData.gpa || 0,
      attendance_rate: studentData.attendance_rate || 0,
      behavioral_incidents: studentData.behavioral_incidents || 0,
      risk_score: studentData.risk_score || 0
    };
    
    // Simple hash function (you could use a more sophisticated one)
    const dataString = JSON.stringify(relevantData);
    let hash = 0;
    for (let i = 0; i < dataString.length; i++) {
      const char = dataString.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    return Math.abs(hash).toString(16);
  }
  
  formatGPTRecommendations(rawText) {
    // Clean and structure the GPT response
    const lines = rawText.split('\n').map(line => line.trim()).filter(line => line);
    
    let formattedHTML = '';
    let currentRecommendation = null;
    let recommendationCount = 0;
    
    for (const line of lines) {
      // Check if this line starts a new recommendation (numbered)
      const numberedMatch = line.match(/^(\d+)\.\s*(.+)/);
      
      if (numberedMatch) {
        // Close previous recommendation if exists
        if (currentRecommendation) {
          formattedHTML += '</div></div>';
        }
        
        recommendationCount++;
        const recommendationText = numberedMatch[2];
        
        // Start new recommendation card
        formattedHTML += `
          <div class="recommendation-card" style="
            background: white;
            border: 1px solid #e0f2fe;
            border-radius: 6px;
            padding: 16px;
            margin-bottom: 12px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
          ">
            <div class="recommendation-header" style="
              display: flex;
              align-items: flex-start;
              margin-bottom: 10px;
            ">
              <div class="recommendation-number" style="
                background: #0ea5e9;
                color: white;
                width: 24px;
                height: 24px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 12px;
                font-weight: 600;
                margin-right: 10px;
                flex-shrink: 0;
              ">
                ${recommendationCount}
              </div>
              <div class="recommendation-title" style="
                font-weight: 600;
                color: #0369a1;
                font-size: 14px;
                line-height: 1.3;
              ">
                ${recommendationText}
              </div>
            </div>
            <div class="recommendation-details" style="margin-left: 34px;">
        `;
        
        currentRecommendation = recommendationCount;
      } else if (currentRecommendation && line.startsWith('-') || line.startsWith('•')) {
        // Format bullet points
        const bulletText = line.replace(/^[-•]\s*/, '');
        formattedHTML += `
          <div class="recommendation-bullet" style="
            display: flex;
            align-items: flex-start;
            margin-bottom: 6px;
          ">
            <div style="
              color: #0ea5e9;
              margin-right: 8px;
              font-weight: bold;
              margin-top: 2px;
            ">•</div>
            <span style="color: #4b5563; font-size: 13px; line-height: 1.4;">
              ${bulletText}
            </span>
          </div>
        `;
      } else if (currentRecommendation && line.length > 0) {
        // Regular text within a recommendation
        formattedHTML += `
          <p style="
            color: #4b5563;
            font-size: 13px;
            line-height: 1.5;
            margin: 8px 0;
          ">
            ${line}
          </p>
        `;
      }
    }
    
    // Close the last recommendation
    if (currentRecommendation) {
      formattedHTML += '</div></div>';
    }
    
    // If no structured recommendations found, display as simple formatted text
    if (recommendationCount === 0) {
      formattedHTML = `
        <div class="simple-recommendations" style="
          background: white;
          border: 1px solid #e0f2fe;
          border-radius: 6px;
          padding: 16px;
        ">
          ${rawText.split('\n').map(line => 
            line.trim() ? `<p style="margin-bottom: 8px; color: #4b5563; line-height: 1.5;">${line.trim()}</p>` : ''
          ).join('')}
        </div>
      `;
    }
    
    return formattedHTML;
  }

  async buildPersonalizedPrompt(studentId, riskLevel) {
    // Get comprehensive student data to analyze their specific situation
    const studentData = await this.getComprehensiveStudentData(studentId, riskLevel);
    
    // Analyze student's specific needs and existing interventions
    const hasInterventions = studentData.interventions_count > 0;
    const hasActiveInterventions = studentData.active_interventions_count > 0;
    const lowGPA = (studentData.gpa || 0) < 2.5;
    const lowAttendance = (studentData.attendance_rate || 0) < 0.85;
    const highBehavioralIssues = (studentData.behavioral_incidents || 0) > 2;
    const highRisk = studentData.risk_score >= 0.7;
    
    // Build context-aware prompt
    let prompt = `STUDENT ANALYSIS REQUEST for ${riskLevel} student (ID: ${studentId}):

CURRENT SITUATION ANALYSIS:`;

    if (hasInterventions) {
      prompt += `
- EXISTING INTERVENTIONS: ${studentData.recent_intervention_details || 'Details not available'}
- ACTIVE INTERVENTIONS: ${studentData.active_interventions_count || 0}
- INTERVENTION STATUS: ${studentData.recent_intervention_statuses || 'Unknown'}`;
    } else {
      prompt += `
- NO CURRENT INTERVENTIONS - Fresh start needed`;
    }

    prompt += `
- ACADEMIC STATUS: GPA ${studentData.gpa || 'Unknown'}, Attendance ${((studentData.attendance_rate || 0) * 100).toFixed(0)}%`;
    
    if (studentData.behavioral_incidents) {
      prompt += `
- BEHAVIORAL: ${studentData.behavioral_incidents} incidents recorded`;
    }

    // Tailored instruction based on student profile
    prompt += `

TASK: Provide exactly 3 PERSONALIZED, actionable recommendations for THIS specific student.`;

    if (hasActiveInterventions) {
      prompt += ` DO NOT duplicate existing active interventions. Build upon or complement current efforts.`;
    }

    // Specific guidance based on student needs
    if (lowGPA && lowAttendance) {
      prompt += ` Focus on both academic recovery AND attendance improvement strategies.`;
    } else if (lowGPA) {
      prompt += ` Prioritize academic skill-building and learning support strategies.`;
    } else if (lowAttendance) {
      prompt += ` Focus on engagement, connection, and attendance motivation strategies.`;
    } else if (highBehavioralIssues) {
      prompt += ` Include behavioral support and self-regulation strategies.`;
    } else if (highRisk) {
      prompt += ` Focus on early intervention and prevention strategies.`;
    }

    prompt += `

FORMAT: Start directly with numbered recommendations. Each should include:
- What to do (specific action)
- Why it's needed for THIS student
- How to implement (2-3 concrete steps)
- Timeline (this week/next 2 weeks)

Make each recommendation unique to this student's specific data and situation.`;

    return prompt;
  }

  async getComprehensiveStudentData(studentId, riskLevel) {
    // Get basic student data from app state
    const currentStudent = this.appState.getState().selectedStudent;
    const risk = currentStudent?.risk_score || currentStudent?.success_probability || 0.5;
    
    // Fetch current interventions for this student
    let interventions = [];
    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch(`/api/interventions/student/${studentId}`, {
        headers: {
          'Authorization': token ? `Bearer ${token}` : '',
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        interventions = await response.json();
      }
    } catch (error) {
      console.warn('Could not fetch interventions for GPT context:', error);
    }
    
    // Build comprehensive student data object
    const studentData = {
      student_id: studentId,
      grade_level: currentStudent?.grade_level || 9,
      risk_category: riskLevel,
      risk_score: risk,
      success_probability: currentStudent?.success_probability || (1 - risk),
      needs_intervention: currentStudent?.needs_intervention || risk > 0.5,
      name: currentStudent?.name || `Student ${studentId}`,
      // Academic metrics
      gpa: currentStudent?.gpa,
      attendance_rate: currentStudent?.attendance_rate,
      behavioral_incidents: currentStudent?.behavioral_incidents,
      socioeconomic_status: currentStudent?.socioeconomic_status,
      special_programs: currentStudent?.special_programs,
      // Intervention details
      interventions_count: interventions.length,
    };
    
    // Add detailed intervention context if available
    if (interventions.length > 0) {
      const activeInterventions = interventions.filter(i => i.status !== 'completed');
      const recentInterventions = interventions.slice(0, 5); // Last 5 interventions
      
      studentData.active_interventions_count = activeInterventions.length;
      studentData.recent_intervention_types = recentInterventions.map(i => i.intervention_type || i.title).join(', ');
      studentData.recent_intervention_statuses = recentInterventions.map(i => i.status).join(', ');
      
      // Include intervention descriptions for context
      if (recentInterventions.length > 0) {
        studentData.recent_intervention_details = recentInterventions.map(i => 
          `${i.intervention_type || i.title}: ${i.status} - ${i.description || 'No details'}`
        ).join('; ');
      }
    }
    
    return studentData;
  }

  cleanOldCacheEntries(studentId, riskLevel, currentDataHash) {
    // Remove old cache entries for this student with different data hashes
    const keysToRemove = [];
    for (let i = 0; i < sessionStorage.length; i++) {
      const key = sessionStorage.key(i);
      if (key && key.startsWith(`quick-insights-${studentId}-${riskLevel}-`) && 
          !key.endsWith(`-${currentDataHash}`)) {
        keysToRemove.push(key);
      }
    }
    
    keysToRemove.forEach(key => {
      sessionStorage.removeItem(key);
      console.log('🗑️ Removed outdated cache entry:', key);
    });
  }

  async loadQuickInsights(studentId, riskLevel) {
    const container = document.getElementById(`gpt-insights-${studentId}`);
    if (!container) {
      console.error('❌ Container not found:', `gpt-insights-${studentId}`);
      return;
    }
    
    const contentDiv = container.querySelector('.gpt-insights-content');
    if (!contentDiv) {
      console.error('❌ Content div not found in container');
      return;
    }
    
    // Generate data hash for current student state
    const currentStudent = this.appState.getState().selectedStudent;
    const dataHash = await this.generateDataHash(studentId, currentStudent);
    const cacheKey = `quick-insights-${studentId}-${riskLevel}-${dataHash}`;
    
    // Show loading state
    contentDiv.innerHTML = `
      <div class="loading-state" style="text-align: center; padding: 20px;">
        <div class="spinner" style="
          border: 3px solid #f3f3f3;
          border-top: 3px solid #3498db;
          border-radius: 50%;
          width: 30px;
          height: 30px;
          animation: spin 1s linear infinite;
          margin: 0 auto 15px;
        "></div>
        <div style="color: #666; font-size: 14px;">🧠 Generating quick insights...</div>
      </div>
    `;
    
    try {
      const response = await fetch('/api/gpt/quick-insight', {
        method: 'POST',
        headers: {
          'Authorization': 'Bearer 0dUHi4QroC1GfgnbibLbqowUnv2YFWIe',
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          student_data: await this.getComprehensiveStudentData(studentId, riskLevel),
          question: await this.buildPersonalizedPrompt(studentId, riskLevel)
        })
      });

      if (response.ok) {
        const result = await response.json();
        const insights = result.insight || 'No insights available';
        
        // Format GPT response into structured recommendations
        const formattedRecommendations = this.formatGPTRecommendations(insights);
        
        contentDiv.innerHTML = `
          <div class="gpt-quick-insights" style="
            background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
            border-left: 3px solid #0ea5e9;
            padding: 20px;
            border-radius: 8px;
            margin-top: 10px;
            box-shadow: 0 2px 8px rgba(14, 165, 233, 0.1);
          ">
            <div class="insights-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
              <span style="font-weight: 600; color: #0369a1; font-size: 14px;">
                <i class="fas fa-lightbulb" style="margin-right: 8px; color: #f59e0b;"></i> Personalized AI Recommendations
              </span>
              <div style="display: flex; gap: 8px; align-items: center;">
                <span style="background: #10b981; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: 500;">
                  🎯 Personalized
                </span>
                <span style="background: #0ea5e9; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px;">
                  ⚡ ${result.processing_time_seconds?.toFixed(1)}s
                </span>
                <button class="btn btn-outline btn-small" onclick="window.analysisComponent?.loadQuickInsights('${studentId}', '${riskLevel}')" 
                        style="font-size: 11px; padding: 2px 8px; border-color: #0ea5e9; color: #0ea5e9;">
                  <i class="fas fa-sync-alt"></i> Refresh
                </button>
              </div>
            </div>
            <div class="insights-content" style="
              font-size: 14px;
              line-height: 1.6;
              color: #0d0d0eff;
            ">
              ${formattedRecommendations}
            </div>
          </div>
        `;
        
        // Cache the result
        sessionStorage.setItem(cacheKey, JSON.stringify({
          insights: formattedRecommendations,
          timestamp: Date.now()
        }));
        
        console.log('✅ Quick insights loaded and cached for student', studentId);
      } else {
        throw new Error('Failed to get insights');
      }
    } catch (error) {
      console.error('❌ Error loading quick insights:', error);
      contentDiv.innerHTML = `
        <div style="padding: 15px; color: #666; font-size: 14px; text-align: center;">
          <i class="fas fa-exclamation-triangle"></i>
          Quick insights temporarily unavailable. Try the detailed explanation button above.
        </div>
      `;
    }
  }
}
