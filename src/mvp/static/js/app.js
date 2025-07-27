// MVP Student Success Predictor - Main JavaScript

class StudentSuccessApp {
    constructor() {
        this.students = [];
        this.filteredStudents = [];
        this.selectedStudent = null;
        this.currentFilter = 'all';
        this.interventions = new Map(); // Track interventions by student ID
        this.demoMode = false;
        this.demoInterval = null;
        this.feedItems = [];
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupDragAndDrop();
        this.setupTwoPanelLayout();
    }

    setupEventListeners() {
        // File input handling
        document.getElementById('file-input').addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.handleFileUpload(e.target.files[0]);
            }
        });

        // Sample data button
        document.getElementById('load-sample').addEventListener('click', () => {
            this.loadSampleData();
        });

        // Demo mode controls
        const demoToggle = document.getElementById('demo-toggle');
        const demoSimulate = document.getElementById('demo-simulate');
        const startDemoFromUpload = document.getElementById('start-demo-from-upload');
        
        if (demoToggle) {
            demoToggle.addEventListener('click', () => {
                this.toggleDemoMode();
            });
        }
        
        if (demoSimulate) {
            demoSimulate.addEventListener('click', () => {
                this.simulateNewStudent();
            });
        }
        
        if (startDemoFromUpload) {
            startDemoFromUpload.addEventListener('click', () => {
                this.startDemoFromUpload();
            });
        }
    }

    setupDragAndDrop() {
        const uploadArea = document.getElementById('upload-area');
        
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
            });
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            uploadArea.addEventListener(eventName, () => {
                uploadArea.classList.add('drag-over');
            });
        });

        ['dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, () => {
                uploadArea.classList.remove('drag-over');
            });
        });

        uploadArea.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleFileUpload(files[0]);
            }
        });
    }

    async handleFileUpload(file) {
        if (!file.name.endsWith('.csv')) {
            alert('Please upload a CSV file.');
            return;
        }

        this.showLoading(true);

        try {
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch('/api/mvp/analyze', {
                method: 'POST',
                headers: {
                    'Authorization': 'Bearer dev-key-change-me'
                },
                body: formData
            });

            if (!response.ok) {
                throw new Error('Failed to analyze student data');
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

    async loadSampleData() {
        this.showLoading(true);

        try {
            const response = await fetch('/api/mvp/sample', {
                headers: {
                    'Authorization': 'Bearer dev-key-change-me'
                }
            });
            if (!response.ok) {
                throw new Error('Failed to load sample data');
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

    displayResults(data) {
        // Ensure students array is properly set and normalized
        this.students = data.students || [];
        
        // Normalize student IDs for consistent access
        this.students = this.students.map(student => {
            // Ensure id_student exists for modal compatibility
            if (!student.id_student && student.id) {
                student.id_student = student.id;
            }
            if (!student.id_student && student.ID) {
                student.id_student = student.ID;
            }
            // Ensure numeric ID for consistent comparison
            if (student.id_student) {
                student.id_student = parseInt(student.id_student);
            }
            return student;
        });
        
        console.log('Processed students data:', this.students.length, 'students');
        console.log('Sample student:', this.students[0]);
        
        // Hide upload section and show results
        document.getElementById('upload-section').style.display = 'none';
        document.getElementById('results-section').classList.remove('hidden');
        document.getElementById('interventions-section').classList.remove('hidden');

        // Update summary stats
        this.updateSummaryStats(data.summary);

        // Display students using two-panel layout
        this.displayStudentsTwoPanel();

        // Display intervention tracking
        this.displayInterventionTracking();
    }

    updateSummaryStats(summary) {
        const statsHTML = `
            <div class="stat-card">
                <div class="stat-value stat-high">${summary.high_risk}</div>
                <div class="stat-label">High Risk</div>
            </div>
            <div class="stat-card">
                <div class="stat-value stat-medium">${summary.medium_risk}</div>
                <div class="stat-label">Medium Risk</div>
            </div>
            <div class="stat-card">
                <div class="stat-value stat-low">${summary.low_risk}</div>
                <div class="stat-label">Low Risk</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${summary.total}</div>
                <div class="stat-label">Total Students</div>
            </div>
        `;
        document.getElementById('summary-stats').innerHTML = statsHTML;
    }

    displayStudents() {
        // Show only high and medium risk students for MVP focus
        const atRiskStudents = this.students.filter(s => 
            s.risk_category === 'High Risk' || s.risk_category === 'Medium Risk'
        ).sort((a, b) => b.risk_score - a.risk_score);

        const studentsHTML = atRiskStudents.map(student => `
            <div class="student-card risk-${student.risk_category.toLowerCase().replace(' ', '-')}" onclick="app.showStudentDetail(${student.id_student})">
                <div class="student-header">
                    <div class="student-name">Student #${student.id_student}</div>
                    <div class="risk-badge risk-${student.risk_category.toLowerCase().replace(' ', '-')}">
                        ${student.risk_category} • ${Math.round(student.risk_score * 100)}%
                    </div>
                </div>
                
                <div class="student-details">
                    <div class="detail-item">
                        <div class="detail-value">${student.success_probability ? Math.round(student.success_probability * 100) : Math.round((1 - student.risk_score) * 100)}%</div>
                        <div class="detail-label">Success Probability</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-value">${student.early_avg_score ? Math.round(student.early_avg_score) : 'N/A'}</div>
                        <div class="detail-label">Assignment Score</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-value">${student.early_active_days || student.early_total_clicks || 0}</div>
                        <div class="detail-label">Engagement Level</div>
                    </div>
                </div>

                <div class="interventions-preview">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                        <h4 style="margin: 0; font-size: 14px; color: #374151; font-weight: 600;">🎯 Recommended Actions</h4>
                        <span style="font-size: 12px; color: #6b7280; background: #f3f4f6; padding: 2px 8px; border-radius: 10px;">AI-Powered</span>
                    </div>
                    ${this.getInterventionsPreview(student)}
                </div>
            </div>
        `).join('');

        document.getElementById('students-list').innerHTML = studentsHTML;
        
        // Enhance student cards with explainable AI buttons if available
        if (window.explainableUI && window.explainableUI.enhanceStudentCards) {
            setTimeout(() => {
                console.log('Enhancing student cards with AI features...');
                window.explainableUI.enhanceStudentCards();
            }, 200);
        } else {
            console.log('ExplainableUI not available yet');
        }
    }

    getInterventionsPreview(student) {
        const interventions = this.getRecommendedInterventions(student);
        const interventionItems = interventions.slice(0, 2).map(intervention => `
            <div class="intervention-item">
                <span class="intervention-text">${intervention.title}</span>
                <span class="intervention-status">Suggested</span>
            </div>
        `).join('');
        
        // Add the AI explanation button
        const explainButton = `
            <div class="intervention-item explain-button">
                <span class="intervention-text" onclick="window.explainableUI && window.explainableUI.showStudentExplanation(${student.id_student})" style="cursor: pointer; color: #2563eb; font-weight: 600;">
                    🔍 Explain AI Prediction
                </span>
                <span class="intervention-status available">AI Analysis</span>
            </div>
        `;
        
        return interventionItems + explainButton;
    }

    getRecommendedInterventions(student) {
        const interventions = [];
        
        if (student.risk_category === 'High Risk') {
            interventions.push(
                { title: "Schedule immediate 1-on-1 meeting", priority: "Critical", type: "Meeting", description: "Meet with student within 48 hours to assess current challenges and provide immediate support." },
                { title: "Connect with academic advisor", priority: "Critical", type: "Support", description: "Refer to academic advisor for comprehensive support plan and resource coordination." },
                { title: "Assess for learning difficulties", priority: "High", type: "Assessment", description: "Evaluate for potential learning challenges that may require additional accommodations." }
            );
        } else if (student.risk_category === 'Medium Risk') {
            interventions.push(
                { title: "Send check-in email this week", priority: "High", type: "Communication", description: "Proactive outreach to understand current situation and offer assistance." },
                { title: "Recommend study group participation", priority: "Medium", type: "Peer Support", description: "Connect with peer learning opportunities to improve engagement and understanding." },
                { title: "Share additional learning resources", priority: "Medium", type: "Resources", description: "Provide targeted materials and tools to support academic improvement." }
            );
        }

        // Add engagement-specific interventions
        if (student.early_total_clicks < 100) {
            interventions.push({
                title: "Address low online engagement",
                priority: "High",
                type: "Engagement",
                description: "Student shows low platform interaction. Schedule technology orientation and engagement strategies."
            });
        }

        // Add score-specific interventions
        if (student.early_avg_score < 60) {
            interventions.push({
                title: "Provide tutoring support",
                priority: "High", 
                type: "Academic",
                description: "Low assessment scores indicate need for additional academic support and skill development."
            });
        }

        return interventions;
    }

    showStudentDetail(studentId) {
        // Try multiple ways to find the student (for CSV upload compatibility)
        let student = this.students.find(s => s.id_student === studentId);
        
        // If not found, try different ID formats
        if (!student) {
            student = this.students.find(s => s.id === studentId);
        }
        if (!student) {
            student = this.students.find(s => s.ID === studentId);
        }
        if (!student) {
            // Try converting to string/number for comparison
            student = this.students.find(s => String(s.id_student) === String(studentId));
        }
        if (!student) {
            student = this.students.find(s => parseInt(s.id_student) === parseInt(studentId));
        }
        
        if (!student) {
            console.error('Student not found:', studentId, 'Available students:', this.students);
            alert('Student details not available. This might be due to a data format issue with CSV uploads.');
            return;
        }
        
        console.log('Found student:', student);

        const interventions = this.getRecommendedInterventions(student);
        
        const modalBody = `
            <div class="student-detail-content">
                <div class="student-overview">
                    <h4>Risk Assessment</h4>
                    <div class="risk-details">
                        <div class="risk-score-large">
                            <span class="risk-badge risk-${student.risk_category.toLowerCase().replace(' ', '-')}">
                                ${student.risk_category}
                            </span>
                            <div class="risk-percentage">${Math.round(student.risk_score * 100)}% Risk Score</div>
                        </div>
                    </div>
                </div>

                <div class="student-metrics">
                    <h4>Key Indicators</h4>
                    <div class="metrics-grid">
                        <div class="metric-item">
                            <label>Average Score:</label>
                            <span>${student.early_avg_score || 'Not available'}</span>
                        </div>
                        <div class="metric-item">
                            <label>Online Engagement:</label>
                            <span>${student.early_total_clicks || 0} clicks</span>
                        </div>
                        <div class="metric-item">
                            <label>Active Days:</label>
                            <span>${student.early_active_days || 0} days</span>
                        </div>
                        <div class="metric-item">
                            <label>Credits:</label>
                            <span>${student.studied_credits || 'Not available'}</span>
                        </div>
                    </div>
                </div>

                <div class="recommended-interventions">
                    <h4>Recommended Actions</h4>
                    <div class="interventions-list">
                        ${interventions.map((intervention, index) => `
                            <div class="intervention-detail">
                                <div class="intervention-header">
                                    <span class="intervention-title">${intervention.title}</span>
                                    <span class="intervention-priority priority-${intervention.priority.toLowerCase()}">${intervention.priority}</span>
                                </div>
                                <div class="intervention-actions">
                                    <button class="btn btn-small btn-secondary" onclick="app.markInterventionTried(${studentId}, ${index})">
                                        Mark as Tried
                                    </button>
                                    <button class="btn btn-small btn-primary" onclick="app.markInterventionSuccessful(${studentId}, ${index})">
                                        Mark as Successful
                                    </button>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;

        document.getElementById('modal-student-name').textContent = `Student #${studentId} - Detail View`;
        document.getElementById('modal-body').innerHTML = modalBody;
        document.getElementById('student-modal').classList.remove('hidden');
    }

    displayInterventionTracking() {
        const atRiskStudents = this.students.filter(s => 
            s.risk_category === 'High Risk' || s.risk_category === 'Medium Risk'
        );

        const trackingHTML = `
            <div class="intervention-summary">
                <h4>Action Summary</h4>
                <p>Track the interventions you've tried and their effectiveness:</p>
                
                <div class="tracking-stats">
                    <div class="stat-item">
                        <span class="stat-number">${atRiskStudents.length}</span>
                        <span class="stat-text">Students needing attention</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-number" id="actions-tried">0</span>
                        <span class="stat-text">Actions tried</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-number" id="actions-successful">0</span>
                        <span class="stat-text">Successful interventions</span>
                    </div>
                </div>
            </div>

            <div class="quick-actions">
                <h4>Quick Actions</h4>
                <div class="action-buttons">
                    <button class="btn btn-primary" onclick="app.exportStudentList()">
                        📋 Export Student List
                    </button>
                    <button class="btn btn-secondary" onclick="app.scheduleFollowUp()">
                        📅 Schedule Follow-up
                    </button>
                    <button class="btn btn-secondary" onclick="app.resetAnalysis()">
                        🔄 Analyze New Data
                    </button>
                </div>
            </div>
        `;

        document.getElementById('intervention-tracking').innerHTML = trackingHTML;
    }

    markInterventionTried(studentId, interventionIndex) {
        const key = `${studentId}-${interventionIndex}`;
        if (!this.interventions.has(key)) {
            this.interventions.set(key, { status: 'tried', timestamp: new Date() });
            this.updateInterventionStats();
            alert('Intervention marked as tried! 👍');
        }
    }

    markInterventionSuccessful(studentId, interventionIndex) {
        const key = `${studentId}-${interventionIndex}`;
        this.interventions.set(key, { status: 'successful', timestamp: new Date() });
        this.updateInterventionStats();
        alert('Great! Intervention marked as successful! 🎉');
    }

    updateInterventionStats() {
        const tried = Array.from(this.interventions.values()).length;
        const successful = Array.from(this.interventions.values()).filter(i => i.status === 'successful').length;
        
        document.getElementById('actions-tried').textContent = tried;
        document.getElementById('actions-successful').textContent = successful;
    }

    exportStudentList() {
        const atRiskStudents = this.students.filter(s => 
            s.risk_category === 'High Risk' || s.risk_category === 'Medium Risk'
        );

        const csv = this.generateCSV(atRiskStudents);
        this.downloadFile(csv, 'at-risk-students.csv', 'text/csv');
    }

    generateCSV(students) {
        const headers = ['Student_ID', 'Risk_Category', 'Risk_Score', 'Avg_Score', 'Engagement_Clicks', 'Recommended_Action'];
        const rows = students.map(student => {
            const interventions = this.getRecommendedInterventions(student);
            const topAction = interventions[0]?.title || 'General support needed';
            
            return [
                student.id_student,
                student.risk_category,
                Math.round(student.risk_score * 100) + '%',
                student.early_avg_score || 'N/A',
                student.early_total_clicks || 0,
                topAction
            ];
        });

        return [headers, ...rows].map(row => row.join(',')).join('\n');
    }

    downloadFile(content, filename, contentType) {
        const blob = new Blob([content], { type: contentType });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        link.click();
        window.URL.revokeObjectURL(url);
    }

    scheduleFollowUp() {
        alert('Follow-up reminder set! 📅\n\nYou\'ll be reminded to check on these students in 1 week.');
    }

    resetAnalysis() {
        if (confirm('Start over with new student data?')) {
            document.getElementById('upload-section').style.display = 'block';
            document.getElementById('results-section').classList.add('hidden');
            document.getElementById('interventions-section').classList.add('hidden');
            document.getElementById('file-input').value = '';
            this.students = [];
            this.interventions.clear();
        }
    }

    showLoading(show) {
        document.getElementById('loading-overlay').classList.toggle('hidden', !show);
    }

    // Two-Panel Layout Methods
    setupTwoPanelLayout() {
        // Setup search functionality
        const searchInput = document.getElementById('student-search');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.filterStudents(e.target.value, this.currentFilter);
            });
        }

        // Setup filter tabs
        const filterTabs = document.querySelectorAll('.filter-tab');
        filterTabs.forEach(tab => {
            tab.addEventListener('click', (e) => {
                // Update active tab
                filterTabs.forEach(t => t.classList.remove('active'));
                e.target.classList.add('active');
                
                // Update filter
                this.currentFilter = e.target.dataset.filter;
                const searchTerm = searchInput ? searchInput.value : '';
                this.filterStudents(searchTerm, this.currentFilter);
            });
        });
    }

    displayStudentsTwoPanel() {
        // Show all students (high, medium, low risk) for better navigation
        this.filteredStudents = this.students.slice().sort((a, b) => b.risk_score - a.risk_score);
        
        // Apply current filter
        const searchInput = document.getElementById('student-search');
        const searchTerm = searchInput ? searchInput.value : '';
        this.filterStudents(searchTerm, this.currentFilter);
        
        // Render compact list
        this.renderCompactStudentList();
        
        // Clear detail panel
        this.clearStudentDetail();
    }

    filterStudents(searchTerm, filter) {
        let filtered = this.students.slice();
        
        // Apply risk filter
        if (filter === 'high') {
            filtered = filtered.filter(s => s.risk_category === 'High Risk');
        } else if (filter === 'medium') {
            filtered = filtered.filter(s => s.risk_category === 'Medium Risk');
        } else if (filter === 'low') {
            filtered = filtered.filter(s => s.risk_category === 'Low Risk');
        }
        
        // Apply search filter
        if (searchTerm) {
            const term = searchTerm.toLowerCase();
            filtered = filtered.filter(s => 
                String(s.id_student).toLowerCase().includes(term) ||
                String(s.id || '').toLowerCase().includes(term)
            );
        }
        
        // Sort by risk score
        this.filteredStudents = filtered.sort((a, b) => b.risk_score - a.risk_score);
        
        // Re-render list
        this.renderCompactStudentList();
    }

    renderCompactStudentList() {
        const container = document.getElementById('student-list-compact');
        if (!container) return;
        
        if (this.filteredStudents.length === 0) {
            container.innerHTML = `
                <div style="padding: 40px 20px; text-align: center; color: #6b7280;">
                    <div style="font-size: 24px; margin-bottom: 8px;">🔍</div>
                    <p>No students match your search criteria.</p>
                </div>
            `;
            return;
        }
        
        const studentsHTML = this.filteredStudents.map(student => `
            <div class="compact-student-item" data-student-id="${student.id_student}" 
                 onclick="app.selectStudent(${student.id_student})">
                <div class="compact-student-header">
                    <div class="student-compact-id">Student #${student.id_student}</div>
                    <div class="risk-badge-compact risk-${student.risk_category.toLowerCase().replace(' ', '-')}">
                        ${student.risk_category.split(' ')[0]}
                    </div>
                </div>
                <div class="compact-student-metrics">
                    <span class="student-compact-score">Score: ${student.early_avg_score ? Math.round(student.early_avg_score) : 'N/A'}</span>
                    <span>Risk: ${Math.round(student.risk_score * 100)}%</span>
                </div>
            </div>
        `).join('');
        
        container.innerHTML = studentsHTML;
    }

    selectStudent(studentId) {
        // Update selected state in list
        document.querySelectorAll('.compact-student-item').forEach(item => {
            item.classList.remove('selected');
        });
        
        const selectedItem = document.querySelector(`[data-student-id="${studentId}"]`);
        if (selectedItem) {
            selectedItem.classList.add('selected');
        }
        
        // Find student data
        this.selectedStudent = this.students.find(s => 
            s.id_student === studentId || 
            String(s.id_student) === String(studentId) ||
            parseInt(s.id_student) === parseInt(studentId)
        );
        
        if (this.selectedStudent) {
            this.renderStudentDetail(this.selectedStudent);
        }
    }

    renderStudentDetail(student) {
        const container = document.getElementById('student-detail-content');
        if (!container) return;
        
        const interventions = this.getRecommendedInterventions(student);
        
        const detailHTML = `
            <div class="student-detail-view">
                <div class="detail-header">
                    <h2>Student #${student.id_student}</h2>
                    <div class="risk-badge risk-${student.risk_category.toLowerCase().replace(' ', '-')}">
                        ${student.risk_category} • ${Math.round(student.risk_score * 100)}% Risk
                    </div>
                </div>
                
                <div class="detail-metrics-grid">
                    <div class="metric-card">
                        <div class="metric-value">${student.success_probability ? Math.round(student.success_probability * 100) : Math.round((1 - student.risk_score) * 100)}%</div>
                        <div class="metric-label">Success Probability</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${student.early_avg_score ? Math.round(student.early_avg_score) : 'N/A'}</div>
                        <div class="metric-label">Average Score</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${student.early_active_days || 0}</div>
                        <div class="metric-label">Active Days</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${student.early_total_clicks || 0}</div>
                        <div class="metric-label">Platform Clicks</div>
                    </div>
                </div>
                
                <div class="detail-actions">
                    <button class="btn btn-primary" onclick="explainableUI.showStudentExplanation(${student.id_student})">
                        🔍 Explain AI Prediction
                    </button>
                    <button class="btn btn-secondary" onclick="app.showStudentDetail(${student.id_student})">
                        📊 Full Details
                    </button>
                </div>
                
                <div class="interventions-detail">
                    <h3>🎯 Recommended Interventions</h3>
                    <div class="interventions-list">
                        ${interventions.slice(0, 3).map(intervention => `
                            <div class="intervention-detail-item">
                                <div class="intervention-title">${intervention.title}</div>
                                <div class="intervention-description">${intervention.description}</div>
                                <div class="intervention-priority">Priority: ${intervention.priority}</div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
        
        container.innerHTML = detailHTML;
    }

    clearStudentDetail() {
        const container = document.getElementById('student-detail-content');
        if (container) {
            container.innerHTML = `
                <div class="no-student-selected">
                    <div class="placeholder-icon">👆</div>
                    <h3>Select a Student</h3>
                    <p>Click on any student from the list to view detailed analysis, risk factors, and AI-powered intervention recommendations.</p>
                </div>
            `;
        }
        
        // Clear selections
        document.querySelectorAll('.compact-student-item').forEach(item => {
            item.classList.remove('selected');
        });
        
        this.selectedStudent = null;
    }

    // Demo Mode Methods
    async toggleDemoMode() {
        const demoToggle = document.getElementById('demo-toggle');
        const demoSection = document.getElementById('demo-dashboard');
        
        if (!this.demoMode) {
            // Start demo mode
            this.demoMode = true;
            demoToggle.textContent = '⏹️ Stop Demo';
            demoToggle.classList.add('demo-pulse');
            
            // Show demo dashboard
            if (demoSection) {
                demoSection.classList.remove('hidden');
            }
            
            // Start live updates
            this.startDemoUpdates();
            
            // Load success stories
            await this.loadSuccessStories();
            
            this.addFeedItem('Demo mode activated - showing live university metrics', 'system');
            
        } else {
            // Stop demo mode
            this.demoMode = false;
            demoToggle.textContent = '🎬 Start Live Demo';
            demoToggle.classList.remove('demo-pulse');
            
            // Stop updates
            if (this.demoInterval) {
                clearInterval(this.demoInterval);
                this.demoInterval = null;
            }
            
            this.addFeedItem('Demo mode stopped', 'system');
        }
    }

    startDemoUpdates() {
        // Update metrics every 3 seconds
        this.demoInterval = setInterval(async () => {
            try {
                const response = await fetch('/api/mvp/demo/stats', {
                    headers: {
                        'Authorization': 'Bearer dev-key-change-me'
                    }
                });
                
                if (response.ok) {
                    const data = await response.json();
                    this.updateDemoMetrics(data);
                }
            } catch (error) {
                console.error('Demo update error:', error);
            }
        }, 3000);
        
        // Initial load
        this.updateDemoMetrics();
    }

    async updateDemoMetrics(data = null) {
        if (!data) {
            try {
                const response = await fetch('/api/mvp/demo/stats', {
                    headers: {
                        'Authorization': 'Bearer dev-key-change-me'
                    }
                });
                
                if (response.ok) {
                    data = await response.json();
                }
            } catch (error) {
                console.error('Failed to fetch demo stats:', error);
                return;
            }
        }

        if (data) {
            // Update institution info
            this.updateElement('institution-name', data.semester_info?.institution);
            this.updateElement('semester-name', data.semester_info?.name);
            this.updateElement('semester-week', `Week ${data.semester_info?.week}`);
            
            // Update metrics with animation
            this.animateNumber('total-students', data.student_metrics?.total_analyzed);
            this.updateElement('new-students', `+${data.student_metrics?.new_this_week} this week`);
            
            this.animateNumber('interventions-triggered', data.intervention_metrics?.interventions_triggered);
            this.updateElement('success-rate', `${Math.round(data.intervention_metrics?.success_rate * 100)}% success rate`);
            
            this.animateNumber('time-saved', data.time_savings?.hours_saved_per_week);
            this.updateElement('prevented-dropouts', `${data.time_savings?.prevented_dropouts} dropouts prevented`);
            
            this.animateNumber('students-helped', data.intervention_metrics?.students_helped);
            this.updateElement('avg-improvement', `+${data.intervention_metrics?.avg_improvement} avg improvement`);
        }
    }

    updateElement(id, value) {
        const element = document.getElementById(id);
        if (element && value !== undefined) {
            element.textContent = value;
        }
    }

    animateNumber(elementId, targetValue) {
        const element = document.getElementById(elementId);
        if (!element || targetValue === undefined) return;
        
        const currentValue = parseInt(element.textContent) || 0;
        const increment = Math.ceil((targetValue - currentValue) / 10);
        
        if (increment !== 0) {
            const timer = setInterval(() => {
                const current = parseInt(element.textContent) || 0;
                const newValue = current + increment;
                
                if ((increment > 0 && newValue >= targetValue) || (increment < 0 && newValue <= targetValue)) {
                    element.textContent = targetValue;
                    clearInterval(timer);
                } else {
                    element.textContent = newValue;
                }
            }, 50);
        }
    }

    async simulateNewStudent() {
        try {
            const response = await fetch('/api/mvp/demo/simulate-new-student', {
                headers: {
                    'Authorization': 'Bearer dev-key-change-me'
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                const student = data.new_student;
                
                // Add to feed
                this.addFeedItem(
                    `New student enrolled: #${student.id_student} - ${student.risk_category} (${Math.round(student.risk_score * 100)}% risk)`,
                    'new-student'
                );
                
                // Simulate intervention if high risk
                if (student.risk_category === 'High Risk') {
                    setTimeout(() => {
                        this.addFeedItem(
                            `Intervention triggered for student #${student.id_student} - Academic advisor assigned`,
                            'intervention'
                        );
                    }, 2000);
                }
                
            }
        } catch (error) {
            console.error('Failed to simulate new student:', error);
        }
    }

    addFeedItem(message, type = 'info') {
        const feedContainer = document.getElementById('feed-container');
        if (!feedContainer) return;
        
        const now = new Date();
        const timeStr = now.toLocaleTimeString('en-US', { 
            hour12: true, 
            hour: 'numeric', 
            minute: '2-digit' 
        });
        
        const feedItem = document.createElement('div');
        feedItem.className = `feed-item ${type}`;
        feedItem.innerHTML = `
            <span class="feed-time">${timeStr}</span>
            <span class="feed-message">${message}</span>
        `;
        
        // Add to top of feed
        feedContainer.insertBefore(feedItem, feedContainer.firstChild);
        
        // Keep only last 10 items
        while (feedContainer.children.length > 10) {
            feedContainer.removeChild(feedContainer.lastChild);
        }
    }

    async loadSuccessStories() {
        try {
            const response = await fetch('/api/mvp/demo/success-stories', {
                headers: {
                    'Authorization': 'Bearer dev-key-change-me'
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.displaySuccessStories(data.success_stories);
            }
        } catch (error) {
            console.error('Failed to load success stories:', error);
        }
    }

    displaySuccessStories(stories) {
        const container = document.getElementById('success-stories-grid');
        const section = document.getElementById('success-stories-section');
        
        if (!container || !section) return;
        
        const storiesHTML = stories.map(story => `
            <div class="success-story-card">
                <div class="success-story-header">
                    <div class="success-story-id">Student #${story.student_id}</div>
                    <div class="success-improvement">+${story.improvement} points</div>
                </div>
                <div class="success-story-quote">${story.quote}</div>
                <div class="success-story-details">
                    ${story.intervention} • ${story.timeframe} • ${story.before_score}→${story.after_score}
                </div>
            </div>
        `).join('');
        
        container.innerHTML = storiesHTML;
        section.style.display = 'block';
    }

    startDemoFromUpload() {
        // Hide upload section and show demo dashboard
        document.getElementById('upload-section').style.display = 'none';
        
        const demoSection = document.getElementById('demo-dashboard');
        if (demoSection) {
            demoSection.classList.remove('hidden');
        }
        
        // Auto-start demo mode
        this.toggleDemoMode();
    }
}

// Modal functions
function closeModal() {
    document.getElementById('student-modal').classList.add('hidden');
}

// Click outside modal to close
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal')) {
        closeModal();
    }
});

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new StudentSuccessApp();
});

// Add some CSS for the modal content that wasn't in the main CSS
const additionalCSS = `
<style>
.student-detail-content h4 {
    margin-bottom: 16px;
    color: var(--gray-900);
    font-weight: 600;
}

.risk-score-large {
    text-align: center;
    margin-bottom: 20px;
}

.risk-percentage {
    font-size: 24px;
    font-weight: 600;
    margin-top: 8px;
    color: var(--gray-900);
}

.metrics-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
}

.metric-item {
    display: flex;
    justify-content: space-between;
    padding: 8px 0;
    border-bottom: 1px solid var(--gray-200);
}

.metric-item label {
    font-weight: 500;
    color: var(--gray-600);
}

.intervention-detail {
    border: 1px solid var(--gray-200);
    border-radius: var(--border-radius);
    padding: 16px;
    margin-bottom: 12px;
}

.intervention-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
}

.intervention-title {
    font-weight: 500;
    color: var(--gray-900);
}

.intervention-priority {
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 11px;
    text-transform: uppercase;
    font-weight: 500;
}

.priority-critical {
    background: #fef2f2;
    color: var(--danger-color);
}

.priority-high {
    background: #fffbeb;
    color: var(--warning-color);
}

.priority-medium {
    background: #f0fdf4;
    color: var(--secondary-color);
}

.intervention-actions {
    display: flex;
    gap: 8px;
}

.tracking-stats {
    display: flex;
    gap: 32px;
    margin: 20px 0;
}

.stat-item {
    text-align: center;
}

.stat-number {
    display: block;
    font-size: 24px;
    font-weight: 700;
    color: var(--primary-color);
}

.stat-text {
    font-size: 12px;
    color: var(--gray-600);
    text-transform: uppercase;
}

.action-buttons {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
}
</style>
`;

document.head.insertAdjacentHTML('beforeend', additionalCSS);