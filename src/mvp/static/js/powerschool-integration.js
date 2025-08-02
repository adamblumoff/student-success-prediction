/**
 * PowerSchool SIS Integration JavaScript
 * Handles PowerSchool API connection, school selection, and comprehensive data synchronization
 */

class PowerSchoolIntegration {
    constructor() {
        this.psUrl = '';
        this.psClientId = '';
        this.psClientSecret = '';
        this.selectedSchool = null;
        this.connectionStatus = false;
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadSavedCredentials();
    }

    bindEvents() {
        // Connection events
        document.getElementById('connect-powerschool')?.addEventListener('click', () => this.connectToPowerSchool());
        document.getElementById('show-powerschool-help')?.addEventListener('click', () => this.showPowerSchoolHelp());
        document.getElementById('close-powerschool-help')?.addEventListener('click', () => this.hidePowerSchoolHelp());
        
        // School selection events
        document.getElementById('refresh-schools')?.addEventListener('click', () => this.loadSchools());
        document.getElementById('select-different-school')?.addEventListener('click', () => this.showSchoolSelection());
        
        // Analysis events
        document.getElementById('sync-school')?.addEventListener('click', () => this.syncSchool());
        
        // Auto-save credentials
        document.getElementById('powerschool-url')?.addEventListener('blur', () => this.saveCredentials());
        document.getElementById('powerschool-client-id')?.addEventListener('blur', () => this.saveCredentials());
        document.getElementById('powerschool-client-secret')?.addEventListener('blur', () => this.saveCredentials());
    }

    loadSavedCredentials() {
        // Load from localStorage (for demo purposes - use secure storage in production)
        const savedUrl = localStorage.getItem('powerschool-url');
        const savedClientId = localStorage.getItem('powerschool-client-id');
        const savedClientSecret = localStorage.getItem('powerschool-client-secret');
        
        if (savedUrl) {
            document.getElementById('powerschool-url').value = savedUrl;
        }
        if (savedClientId) {
            document.getElementById('powerschool-client-id').value = savedClientId;
        }
        if (savedClientSecret) {
            document.getElementById('powerschool-client-secret').value = savedClientSecret;
        }
    }

    saveCredentials() {
        const url = document.getElementById('powerschool-url').value;
        const clientId = document.getElementById('powerschool-client-id').value;
        const clientSecret = document.getElementById('powerschool-client-secret').value;
        
        if (url) localStorage.setItem('powerschool-url', url);
        if (clientId) localStorage.setItem('powerschool-client-id', clientId);
        if (clientSecret) localStorage.setItem('powerschool-client-secret', clientSecret);
    }

    showPowerSchoolHelp() {
        document.getElementById('powerschool-help').classList.remove('hidden');
    }

    hidePowerSchoolHelp() {
        document.getElementById('powerschool-help').classList.add('hidden');
    }

    async connectToPowerSchool() {
        const urlInput = document.getElementById('powerschool-url');
        const clientIdInput = document.getElementById('powerschool-client-id');
        const clientSecretInput = document.getElementById('powerschool-client-secret');
        
        this.psUrl = urlInput.value.trim();
        this.psClientId = clientIdInput.value.trim();
        this.psClientSecret = clientSecretInput.value.trim();
        
        if (!this.psUrl || !this.psClientId || !this.psClientSecret) {
            this.showError('Please enter PowerSchool URL, Client ID, and Client Secret');
            return;
        }
        
        // Normalize URL
        if (!this.psUrl.startsWith('http')) {
            this.psUrl = 'https://' + this.psUrl;
        }
        this.psUrl = this.psUrl.replace(/\/$/, ''); // Remove trailing slash
        
        const connectBtn = document.getElementById('connect-powerschool');
        const originalText = connectBtn.textContent;
        
        try {
            connectBtn.textContent = '🔗 Connecting...';
            connectBtn.disabled = true;
            
            const response = await fetch('/api/sis/powerschool/connect', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getApiKey()}`
                },
                body: JSON.stringify({
                    base_url: this.psUrl,
                    client_id: this.psClientId,
                    client_secret: this.psClientSecret
                })
            });
            
            const result = await response.json();
            
            if (result.status === 'success') {
                this.connectionStatus = true;
                this.showConnectionSuccess(result.district_info);
                await this.loadSchools();
                this.saveCredentials();
            } else {
                throw new Error(result.error || 'Connection failed');
            }
            
        } catch (error) {
            console.error('PowerSchool connection error:', error);
            this.showError(`Connection failed: ${error.message}`);
        } finally {
            connectBtn.textContent = originalText;
            connectBtn.disabled = false;
        }
    }

    showConnectionSuccess(districtInfo) {
        // Hide connection form
        document.getElementById('sis-connection').style.display = 'none';
        
        // Show connection status
        const statusDiv = document.getElementById('sis-connection-status');
        statusDiv.classList.remove('hidden');
        
        // Update connection info
        document.getElementById('district-name').textContent = districtInfo.name || 'Unknown District';
        document.getElementById('students-accessible').textContent = districtInfo.accessible_students ? 'Yes' : 'No';
        document.getElementById('sis-rate-limit').textContent = districtInfo.rate_limit_remaining || 0;
        
        const expiresIn = districtInfo.token_expires_in || 0;
        const expiresText = expiresIn > 0 ? `${Math.floor(expiresIn / 60)} minutes` : 'Unknown';
        document.getElementById('token-expires').textContent = expiresText;
        
        this.showSuccess('Successfully connected to PowerSchool SIS!');
    }

    async loadSchools() {
        if (!this.connectionStatus) {
            this.showError('Please connect to PowerSchool first');
            return;
        }

        try {
            const response = await fetch('/api/sis/powerschool/schools', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getApiKey()}`
                },
                body: JSON.stringify({
                    base_url: this.psUrl,
                    client_id: this.psClientId,
                    client_secret: this.psClientSecret
                })
            });
            
            const result = await response.json();
            
            if (result.status === 'success') {
                this.displaySchools(result.schools);
                this.showSchoolSelection();
            } else {
                throw new Error(result.error || 'Failed to load schools');
            }
            
        } catch (error) {
            console.error('Error loading schools:', error);
            this.showError(`Failed to load schools: ${error.message}`);
        }
    }

    displaySchools(schools) {
        const schoolList = document.getElementById('school-list');
        schoolList.innerHTML = '';
        
        if (schools.length === 0) {
            schoolList.innerHTML = '<p class="no-schools">No schools found. Check PowerSchool permissions and district configuration.</p>';
            return;
        }
        
        schools.forEach(school => {
            const schoolCard = document.createElement('div');
            schoolCard.className = 'school-card';
            schoolCard.innerHTML = `
                <div class="school-info">
                    <h5>${school.name}</h5>
                    <p class="school-code">School #${school.school_number}</p>
                    <div class="school-meta">
                        <span>📚 Grades ${school.low_grade}-${school.high_grade}</span>
                        <span>👥 ${school.student_count} students</span>
                        <span class="school-status ${school.active ? 'active' : 'inactive'}">
                            ${school.active ? '✅ Active' : '⏸️ Inactive'}
                        </span>
                    </div>
                </div>
                <button class="btn btn-primary select-school-btn" data-school-id="${school.id}">
                    Select School
                </button>
            `;
            
            schoolCard.querySelector('.select-school-btn').addEventListener('click', () => {
                this.selectSchool(school);
            });
            
            schoolList.appendChild(schoolCard);
        });
    }

    selectSchool(school) {
        this.selectedSchool = school;
        
        // Update UI
        document.getElementById('selected-school-name').textContent = school.name;
        document.getElementById('selected-school-grades').textContent = `${school.low_grade}-${school.high_grade}`;
        document.getElementById('selected-school-students').textContent = school.student_count;
        
        // Show analysis section
        this.showSchoolAnalysis();
    }

    showSchoolSelection() {
        document.getElementById('school-selection').classList.remove('hidden');
        document.getElementById('school-analysis').classList.add('hidden');
    }

    showSchoolAnalysis() {
        document.getElementById('school-selection').classList.add('hidden');
        document.getElementById('school-analysis').classList.remove('hidden');
    }

    getSelectedGradeLevels() {
        const checkboxes = document.querySelectorAll('.grade-checkboxes input[type="checkbox"]:checked');
        return Array.from(checkboxes).map(cb => parseInt(cb.value));
    }

    async syncSchool() {
        if (!this.selectedSchool) {
            this.showError('Please select a school first');
            return;
        }

        const syncBtn = document.getElementById('sync-school');
        const originalText = syncBtn.textContent;
        const progressDiv = document.getElementById('sis-sync-progress');
        const progressFill = document.getElementById('sis-progress-fill');
        const progressText = document.getElementById('sis-progress-text');
        
        try {
            syncBtn.disabled = true;
            syncBtn.textContent = '📊 Syncing...';
            progressDiv.classList.remove('hidden');
            
            // Get selected grade levels
            const gradeLevels = this.getSelectedGradeLevels();
            
            // Animate progress
            this.animateProgress(progressFill, progressText, [
                { progress: 15, text: 'Authenticating with PowerSchool...' },
                { progress: 30, text: 'Fetching student demographics...' },
                { progress: 45, text: 'Processing attendance data...' },
                { progress: 60, text: 'Analyzing discipline records...' },
                { progress: 75, text: 'Extracting grade history...' },
                { progress: 90, text: 'Generating enhanced predictions...' },
                { progress: 100, text: 'Analysis complete!' }
            ]);
            
            const response = await fetch('/api/sis/powerschool/sync', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getApiKey()}`
                },
                body: JSON.stringify({
                    base_url: this.psUrl,
                    client_id: this.psClientId,
                    client_secret: this.psClientSecret,
                    school_id: this.selectedSchool.id,
                    grade_levels: gradeLevels.length > 0 ? gradeLevels : null
                })
            });
            
            const result = await response.json();
            
            if (result.status === 'success') {
                // Hide PowerSchool interface and show results
                document.getElementById('sis-section').style.display = 'none';
                
                // Display results in the main results section
                this.displayPowerSchoolResults(result);
                
                const gradeText = gradeLevels.length > 0 ? ` (Grades ${gradeLevels.join(', ')})` : '';
                this.showSuccess(`✅ Successfully analyzed ${result.students_processed} students from ${this.selectedSchool.name}${gradeText} with enhanced PowerSchool data`);
            } else {
                throw new Error(result.error || 'Sync failed');
            }
            
        } catch (error) {
            console.error('PowerSchool sync error:', error);
            this.showError(`Sync failed: ${error.message}`);
            progressFill.style.width = '0%';
            progressText.textContent = 'Sync failed';
        } finally {
            syncBtn.disabled = false;
            syncBtn.textContent = originalText;
            setTimeout(() => {
                progressDiv.classList.add('hidden');
            }, 2000);
        }
    }

    displayPowerSchoolResults(result) {
        // Show results section
        const resultsSection = document.getElementById('results-section');
        const summarySection = document.getElementById('summary-section');
        
        if (resultsSection) {
            resultsSection.classList.remove('hidden');
            resultsSection.scrollIntoView({ behavior: 'smooth' });
        }
        
        // Update summary with PowerSchool data
        if (result.summary && summarySection) {
            this.updateSummarySection(result.summary, result.school_id);
        }
        
        // Display predictions
        if (result.predictions && window.displayResults) {
            // Enhance prediction display with SIS data
            this.enhancePredictionDisplay(result.predictions);
            window.displayResults(result.predictions);
        }
        
        // Add PowerSchool-specific information
        this.addPowerSchoolMetadata(result);
    }

    enhancePredictionDisplay(predictions) {
        // Add SIS-specific data to predictions for enhanced display
        predictions.forEach(prediction => {
            if (prediction.sis_risk_factors && prediction.sis_risk_factors.length > 0) {
                prediction.enhanced_risk_factors = prediction.sis_risk_factors;
            }
            if (prediction.sis_protective_factors && prediction.sis_protective_factors.length > 0) {
                prediction.enhanced_protective_factors = prediction.sis_protective_factors;
            }
        });
    }

    updateSummarySection(summary, schoolId) {
        const summarySection = document.getElementById('summary-section');
        if (!summarySection) return;
        
        const enhancedData = summary.enhanced_data_coverage || {};
        
        summarySection.innerHTML = `
            <div class="card">
                <div class="step-header">
                    <span class="step-number">🏫</span>
                    <h2>PowerSchool SIS Analysis Summary</h2>
                    <p>Comprehensive analysis from ${this.selectedSchool.name}</p>
                </div>
                
                <div class="summary-grid">
                    <div class="summary-card">
                        <div class="summary-icon">👥</div>
                        <div class="summary-content">
                            <h3>${summary.total_students}</h3>
                            <p>Total Students</p>
                        </div>
                    </div>
                    
                    <div class="summary-card risk-high">
                        <div class="summary-icon">⚠️</div>
                        <div class="summary-content">
                            <h3>${summary.risk_distribution.high_risk}</h3>
                            <p>High Risk</p>
                        </div>
                    </div>
                    
                    <div class="summary-card risk-moderate">
                        <div class="summary-icon">⚡</div>
                        <div class="summary-content">
                            <h3>${summary.risk_distribution.moderate_risk}</h3>
                            <p>Moderate Risk</p>
                        </div>
                    </div>
                    
                    <div class="summary-card risk-low">
                        <div class="summary-icon">✅</div>
                        <div class="summary-content">
                            <h3>${summary.risk_distribution.low_risk}</h3>
                            <p>Low Risk</p>
                        </div>
                    </div>
                </div>
                
                <div class="enhanced-data-quality">
                    <h4>📊 Enhanced Data Coverage</h4>
                    <div class="data-quality-grid">
                        <div class="quality-item ${enhancedData.attendance_data ? 'available' : 'unavailable'}">
                            <span class="quality-icon">${enhancedData.attendance_data ? '✅' : '❌'}</span>
                            <span>Attendance Records</span>
                            <small>(${enhancedData.attendance_data || 0} students)</small>
                        </div>
                        <div class="quality-item ${enhancedData.discipline_data ? 'available' : 'unavailable'}">
                            <span class="quality-icon">${enhancedData.discipline_data ? '✅' : '❌'}</span>
                            <span>Discipline Data</span>
                            <small>(${enhancedData.discipline_data || 0} students)</small>
                        </div>
                        <div class="quality-item ${enhancedData.demographics_data ? 'available' : 'unavailable'}">
                            <span class="quality-icon">${enhancedData.demographics_data ? '✅' : '❌'}</span>
                            <span>Demographics</span>
                            <small>(${enhancedData.demographics_data || 0} students)</small>
                        </div>
                        <div class="quality-item ${enhancedData.special_programs_data ? 'available' : 'unavailable'}">
                            <span class="quality-icon">${enhancedData.special_programs_data ? '✅' : '❌'}</span>
                            <span>Special Programs</span>
                            <small>(${enhancedData.special_programs_data || 0} students)</small>
                        </div>
                    </div>
                </div>
                
                <div class="powerschool-info">
                    <p><strong>School:</strong> ${this.selectedSchool.name}</p>
                    <p><strong>Data Source:</strong> PowerSchool SIS (Comprehensive)</p>
                    <p><strong>Last Sync:</strong> ${new Date().toLocaleString()}</p>
                </div>
            </div>
        `;
        
        summarySection.classList.remove('hidden');
    }

    addPowerSchoolMetadata(result) {
        // Add a note about PowerSchool data source
        const metadataDiv = document.createElement('div');
        metadataDiv.className = 'powerschool-metadata';
        metadataDiv.innerHTML = `
            <div class="card">
                <h4>🏫 PowerSchool SIS Integration</h4>
                <p>This analysis was generated from comprehensive PowerSchool SIS data:</p>
                <ul>
                    <li><strong>School:</strong> ${this.selectedSchool.name} (#${this.selectedSchool.school_number})</li>
                    <li><strong>Students Analyzed:</strong> ${result.students_processed}</li>
                    <li><strong>Data Sources:</strong> Demographics, Attendance, Grades, Discipline, Special Programs</li>
                    <li><strong>Enhanced Features:</strong> Multi-year trends, risk factors, protective factors</li>
                    <li><strong>Sync Time:</strong> ${new Date().toLocaleString()}</li>
                </ul>
                <div class="data-advantage">
                    <h5>📈 PowerSchool Advantage</h5>
                    <p>Unlike CSV uploads or LMS data, PowerSchool provides:</p>
                    <div class="advantage-tags">
                        <span class="advantage-tag">📅 Official attendance records</span>
                        <span class="advantage-tag">⚠️ Discipline incident history</span>
                        <span class="advantage-tag">👥 Complete demographics</span>
                        <span class="advantage-tag">🎯 IEP, 504, ELL status</span>
                        <span class="advantage-tag">📊 Multi-year academic trends</span>
                        <span class="advantage-tag">💰 Economic disadvantage indicators</span>
                    </div>
                </div>
                <p class="note">💡 <strong>Next Steps:</strong> Use these enhanced predictions with comprehensive risk factors for targeted interventions.</p>
            </div>
        `;
        
        const resultsSection = document.getElementById('results-section');
        if (resultsSection) {
            resultsSection.appendChild(metadataDiv);
        }
    }

    animateProgress(progressFill, progressText, steps) {
        let currentStep = 0;
        
        const animate = () => {
            if (currentStep < steps.length) {
                const step = steps[currentStep];
                progressFill.style.width = step.progress + '%';
                progressText.textContent = step.text;
                currentStep++;
                setTimeout(animate, 1000); // Slower for PowerSchool (more data processing)
            }
        };
        
        animate();
    }

    getApiKey() {
        // Get API key from localStorage or use default
        return localStorage.getItem('api-key') || 'dev-key-change-me';
    }

    showError(message) {
        // Create or update error message
        let errorDiv = document.getElementById('powerschool-error');
        if (!errorDiv) {
            errorDiv = document.createElement('div');
            errorDiv.id = 'powerschool-error';
            errorDiv.className = 'error-message';
            document.getElementById('sis-section').appendChild(errorDiv);
        }
        
        errorDiv.innerHTML = `
            <div class="error-content">
                <span class="error-icon">❌</span>
                <span class="error-text">${message}</span>
                <button class="error-close" onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
        `;
        
        errorDiv.style.display = 'block';
        
        // Auto-hide after 7 seconds (longer for PowerSchool errors)
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.remove();
            }
        }, 7000);
    }

    showSuccess(message) {
        // Create or update success message
        let successDiv = document.getElementById('powerschool-success');
        if (!successDiv) {
            successDiv = document.createElement('div');
            successDiv.id = 'powerschool-success';
            successDiv.className = 'success-message';
            document.getElementById('sis-section').appendChild(successDiv);
        }
        
        successDiv.innerHTML = `
            <div class="success-content">
                <span class="success-icon">✅</span>
                <span class="success-text">${message}</span>
                <button class="success-close" onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
        `;
        
        successDiv.style.display = 'block';
        
        // Auto-hide after 7 seconds
        setTimeout(() => {
            if (successDiv.parentNode) {
                successDiv.remove();
            }
        }, 7000);
    }
}

// Initialize PowerSchool integration when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.powerSchoolIntegration = new PowerSchoolIntegration();
});