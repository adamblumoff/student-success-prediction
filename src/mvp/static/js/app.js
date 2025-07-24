// MVP Student Success Predictor - Main JavaScript

class StudentSuccessApp {
    constructor() {
        this.students = [];
        this.interventions = new Map(); // Track interventions by student ID
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupDragAndDrop();
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
        this.students = data.students;
        
        // Hide upload section and show results
        document.getElementById('upload-section').style.display = 'none';
        document.getElementById('results-section').classList.remove('hidden');
        document.getElementById('interventions-section').classList.remove('hidden');

        // Update summary stats
        this.updateSummaryStats(data.summary);

        // Display students
        this.displayStudents();

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
            <div class="student-card" onclick="app.showStudentDetail(${student.id_student})">
                <div class="student-header">
                    <div class="student-name">Student #${student.id_student}</div>
                    <div class="risk-badge risk-${student.risk_category.toLowerCase().replace(' ', '-')}">
                        ${student.risk_category}
                    </div>
                </div>
                
                <div class="student-details">
                    <div class="detail-item">
                        <div class="detail-value">${Math.round(student.risk_score * 100)}%</div>
                        <div class="detail-label">Risk Score</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-value">${student.early_avg_score || 'N/A'}</div>
                        <div class="detail-label">Avg Score</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-value">${student.early_total_clicks || 0}</div>
                        <div class="detail-label">Engagement</div>
                    </div>
                </div>

                <div class="interventions-preview">
                    ${this.getInterventionsPreview(student)}
                </div>
            </div>
        `).join('');

        document.getElementById('students-list').innerHTML = studentsHTML;
    }

    getInterventionsPreview(student) {
        const interventions = this.getRecommendedInterventions(student);
        return interventions.slice(0, 2).map(intervention => `
            <div class="intervention-item">
                <span class="intervention-text">${intervention.title}</span>
                <span class="intervention-status">Suggested</span>
            </div>
        `).join('');
    }

    getRecommendedInterventions(student) {
        const interventions = [];
        
        if (student.risk_category === 'High Risk') {
            interventions.push(
                { title: "Schedule immediate 1-on-1 meeting", priority: "Critical", type: "Meeting" },
                { title: "Connect with academic advisor", priority: "Critical", type: "Support" },
                { title: "Assess for learning difficulties", priority: "High", type: "Assessment" }
            );
        } else if (student.risk_category === 'Medium Risk') {
            interventions.push(
                { title: "Send check-in email this week", priority: "High", type: "Communication" },
                { title: "Recommend study group participation", priority: "Medium", type: "Peer Support" },
                { title: "Share additional learning resources", priority: "Medium", type: "Resources" }
            );
        }

        // Add engagement-specific interventions
        if (student.early_total_clicks < 100) {
            interventions.push({
                title: "Address low online engagement",
                priority: "High",
                type: "Engagement"
            });
        }

        // Add score-specific interventions
        if (student.early_avg_score < 60) {
            interventions.push({
                title: "Provide tutoring support",
                priority: "High", 
                type: "Academic"
            });
        }

        return interventions;
    }

    showStudentDetail(studentId) {
        const student = this.students.find(s => s.id_student === studentId);
        if (!student) return;

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