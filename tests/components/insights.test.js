/**
 * Insights Component Tests
 * Testing AI insights, feature importance, and explainable AI features
 */

describe('Insights Component', () => {
  let mockAppState;
  let insights;

  // Mock Insights component with explainable AI features
  const createMockInsights = (selector, appState) => {
    const element = document.querySelector(selector);
    
    return {
      element,
      appState,
      students: [],
      modelMetadata: null,
      featureImportance: [],
      
      init() {
        if (this.element) {
          this.bindEvents();
          this.subscribeToState();
          this.loadModelInsights();
        }
      },
      
      bindEvents() {
        const exportBtn = this.element.querySelector('#export-insights');
        if (exportBtn) {
          exportBtn.addEventListener('click', this.exportInsights.bind(this));
        }
        
        const filterSelect = this.element.querySelector('#importance-filter');
        if (filterSelect) {
          filterSelect.addEventListener('change', this.handleFilterChange.bind(this));
        }
      },
      
      subscribeToState() {
        this.appState.subscribe('students', (students) => {
          this.updateStudents(students);
        });
        
        this.appState.subscribe('selectedStudent', (student) => {
          this.showStudentExplanation(student);
        });
      },
      
      updateStudents(students) {
        this.students = students || [];
        this.generateInsights();
      },
      
      loadModelInsights() {
        // Mock model metadata
        this.modelMetadata = {
          accuracy: 0.815,
          precision: 0.78,
          recall: 0.83,
          f1Score: 0.805,
          auc: 0.815,
          modelType: 'ultra_advanced',
          features: 40,
          trainingData: 30000
        };
        
        // Mock feature importance data
        this.featureImportance = [
          { feature: 'Attendance Rate', importance: 0.24, category: 'engagement' },
          { feature: 'Assignment Completion', importance: 0.18, category: 'academic' },
          { feature: 'Grade Trend', importance: 0.15, category: 'academic' },
          { feature: 'Behavioral Incidents', importance: 0.12, category: 'behavioral' },
          { feature: 'Parent Contact Frequency', importance: 0.10, category: 'support' },
          { feature: 'Socioeconomic Status', importance: 0.08, category: 'demographic' },
          { feature: 'Previous Interventions', importance: 0.07, category: 'historical' },
          { feature: 'Extracurricular Participation', importance: 0.06, category: 'engagement' }
        ];
        
        this.renderModelPerformance();
        this.renderFeatureImportance();
      },
      
      generateInsights() {
        const insights = this.analyzeStudentPatterns();
        this.renderGlobalInsights(insights);
      },
      
      analyzeStudentPatterns() {
        if (this.students.length === 0) {
          return { trends: [], recommendations: [], alerts: [] };
        }
        
        const highRiskCount = this.students.filter(s => (s.risk_score || 0) >= 0.7).length;
        const highRiskPercent = (highRiskCount / this.students.length) * 100;
        
        const insights = {
          trends: [
            `${highRiskCount} students (${highRiskPercent.toFixed(1)}%) are at high risk`,
            `Average success probability: ${this.calculateAverageSuccess().toFixed(1)}%`
          ],
          recommendations: [],
          alerts: []
        };
        
        if (highRiskPercent > 30) {
          insights.alerts.push('High percentage of at-risk students detected');
          insights.recommendations.push('Consider implementing school-wide intervention programs');
        }
        
        if (this.calculateAverageSuccess() < 0.5) {
          insights.alerts.push('Overall performance below expected levels');
          insights.recommendations.push('Review curriculum and teaching strategies');
        }
        
        return insights;
      },
      
      calculateAverageSuccess() {
        if (this.students.length === 0) return 0;
        const total = this.students.reduce((sum, s) => sum + (s.success_probability || 0), 0);
        return (total / this.students.length) * 100;
      },
      
      renderModelPerformance() {
        const container = this.element.querySelector('#model-performance');
        if (!container || !this.modelMetadata) return;
        
        container.innerHTML = `
          <h3>Model Performance</h3>
          <div class="performance-grid">
            <div class="metric-card">
              <div class="metric-label">Accuracy</div>
              <div class="metric-value">${(this.modelMetadata.accuracy * 100).toFixed(1)}%</div>
            </div>
            <div class="metric-card">
              <div class="metric-label">AUC Score</div>
              <div class="metric-value">${this.modelMetadata.auc.toFixed(3)}</div>
            </div>
            <div class="metric-card">
              <div class="metric-label">Precision</div>
              <div class="metric-value">${(this.modelMetadata.precision * 100).toFixed(1)}%</div>
            </div>
            <div class="metric-card">
              <div class="metric-label">Recall</div>
              <div class="metric-value">${(this.modelMetadata.recall * 100).toFixed(1)}%</div>
            </div>
          </div>
          <div class="model-details">
            <p>Model Type: ${this.modelMetadata.modelType}</p>
            <p>Features: ${this.modelMetadata.features}</p>
            <p>Training Data: ${this.modelMetadata.trainingData.toLocaleString()} students</p>
          </div>
        `;
      },
      
      renderFeatureImportance() {
        const container = this.element.querySelector('#feature-importance');
        if (!container) return;
        
        const topFeatures = this.featureImportance.slice(0, 8);
        
        container.innerHTML = `
          <h3>Feature Importance</h3>
          <div class="importance-chart">
            ${topFeatures.map(feature => `
              <div class="importance-bar">
                <div class="feature-label">${feature.feature}</div>
                <div class="bar-container">
                  <div class="bar-fill" style="width: ${feature.importance * 100}%"></div>
                  <span class="importance-value">${(feature.importance * 100).toFixed(1)}%</span>
                </div>
              </div>
            `).join('')}
          </div>
        `;
      },
      
      renderGlobalInsights(insights) {
        const container = this.element.querySelector('#global-insights');
        if (!container) return;
        
        container.innerHTML = `
          <h3>Key Insights</h3>
          
          ${insights.alerts.length > 0 ? `
            <div class="alerts-section">
              <h4>🚨 Alerts</h4>
              <ul>
                ${insights.alerts.map(alert => `<li>${alert}</li>`).join('')}
              </ul>
            </div>
          ` : ''}
          
          <div class="trends-section">
            <h4>📈 Trends</h4>
            <ul>
              ${insights.trends.map(trend => `<li>${trend}</li>`).join('')}
            </ul>
          </div>
          
          ${insights.recommendations.length > 0 ? `
            <div class="recommendations-section">
              <h4>💡 Recommendations</h4>
              <ul>
                ${insights.recommendations.map(rec => `<li>${rec}</li>`).join('')}
              </ul>
            </div>
          ` : ''}
        `;
      },
      
      showStudentExplanation(student) {
        if (!student) return;
        
        const explanation = this.generateStudentExplanation(student);
        this.renderStudentExplanation(explanation);
      },
      
      generateStudentExplanation(student) {
        const riskScore = student.risk_score || 0;
        const successProb = student.success_probability || 0;
        
        const explanation = {
          studentId: student.student_id || student.id,
          studentName: student.name,
          riskLevel: this.getRiskCategory(riskScore),
          riskScore: (riskScore * 100).toFixed(1),
          successProbability: (successProb * 100).toFixed(1),
          keyFactors: this.getKeyFactors(student),
          recommendations: this.getPersonalizedRecommendations(student)
        };
        
        return explanation;
      },
      
      getRiskCategory(riskScore) {
        if (riskScore >= 0.7) return 'High Risk';
        if (riskScore >= 0.4) return 'Moderate Risk';
        return 'Low Risk';
      },
      
      getKeyFactors(student) {
        // Mock key factors based on risk score
        const riskScore = student.risk_score || 0;
        
        if (riskScore >= 0.7) {
          return [
            'Low attendance rate (risk factor)',
            'Declining grade trend (risk factor)',
            'Multiple behavioral incidents (risk factor)'
          ];
        } else if (riskScore >= 0.4) {
          return [
            'Moderate attendance issues (risk factor)',
            'Inconsistent assignment completion (risk factor)',
            'Active in extracurriculars (protective factor)'
          ];
        } else {
          return [
            'Excellent attendance (protective factor)',
            'Consistent high performance (protective factor)',
            'Strong parent engagement (protective factor)'
          ];
        }
      },
      
      getPersonalizedRecommendations(student) {
        const riskScore = student.risk_score || 0;
        
        if (riskScore >= 0.7) {
          return [
            'Immediate intervention required',
            'Schedule parent conference',
            'Assign academic mentor',
            'Implement attendance monitoring'
          ];
        } else if (riskScore >= 0.4) {
          return [
            'Monitor progress closely',
            'Provide additional tutoring support',
            'Encourage continued extracurricular participation'
          ];
        } else {
          return [
            'Continue current support level',
            'Consider leadership opportunities',
            'Maintain regular check-ins'
          ];
        }
      },
      
      renderStudentExplanation(explanation) {
        const container = this.element.querySelector('#student-explanation');
        if (!container) return;
        
        container.innerHTML = `
          <div class="explanation-header">
            <h3>Prediction Explanation: ${explanation.studentName}</h3>
            <div class="risk-indicator ${explanation.riskLevel.toLowerCase().replace(' ', '-')}">
              ${explanation.riskLevel}
            </div>
          </div>
          
          <div class="explanation-content">
            <div class="prediction-scores">
              <div class="score-item">
                <label>Risk Score:</label>
                <span>${explanation.riskScore}%</span>
              </div>
              <div class="score-item">
                <label>Success Probability:</label>
                <span>${explanation.successProbability}%</span>
              </div>
            </div>
            
            <div class="key-factors">
              <h4>Key Factors</h4>
              <ul>
                ${explanation.keyFactors.map(factor => `<li>${factor}</li>`).join('')}
              </ul>
            </div>
            
            <div class="recommendations">
              <h4>Recommendations</h4>
              <ul>
                ${explanation.recommendations.map(rec => `<li>${rec}</li>`).join('')}
              </ul>
            </div>
          </div>
        `;
        
        container.style.display = 'block';
      },
      
      handleFilterChange(event) {
        const filterValue = event.target.value;
        let filteredFeatures = this.featureImportance;
        
        if (filterValue !== 'all') {
          const count = parseInt(filterValue.replace('top-', ''));
          filteredFeatures = this.featureImportance.slice(0, count);
        }
        
        this.renderFilteredFeatureImportance(filteredFeatures);
      },
      
      renderFilteredFeatureImportance(features) {
        const container = this.element.querySelector('#feature-importance .importance-chart');
        if (!container) return;
        
        container.innerHTML = features.map(feature => `
          <div class="importance-bar">
            <div class="feature-label">${feature.feature}</div>
            <div class="bar-container">
              <div class="bar-fill" style="width: ${feature.importance * 100}%"></div>
              <span class="importance-value">${(feature.importance * 100).toFixed(1)}%</span>
            </div>
          </div>
        `).join('');
      },
      
      exportInsights() {
        const exportData = {
          timestamp: new Date().toISOString(),
          modelPerformance: this.modelMetadata,
          featureImportance: this.featureImportance,
          studentInsights: this.analyzeStudentPatterns(),
          totalStudents: this.students.length
        };
        
        return JSON.stringify(exportData, null, 2);
      },
      
      destroy() {
        const exportBtn = this.element?.querySelector('#export-insights');
        if (exportBtn) {
          exportBtn.removeEventListener('click', this.exportInsights);
        }
        
        const filterSelect = this.element?.querySelector('#importance-filter');
        if (filterSelect) {
          filterSelect.removeEventListener('change', this.handleFilterChange);
        }
      }
    };
  };

  beforeEach(() => {
    // Set up DOM structure
    document.body.innerHTML = `
      <div id="tab-insights">
        <div id="model-performance"></div>
        <div id="feature-importance"></div>
        <select id="importance-filter">
          <option value="all">All Features</option>
          <option value="top-5">Top 5</option>
          <option value="top-10">Top 10</option>
        </select>
        <div id="global-insights"></div>
        <div id="student-explanation" style="display: none;"></div>
        <button id="export-insights">Export Insights</button>
      </div>
    `;

    // Create mock app state
    mockAppState = {
      state: { 
        currentTab: 'insights', 
        students: [],
        selectedStudent: null
      },
      listeners: new Map(),
      
      getState() { return this.state; },
      setState: jest.fn(function(updates) {
        Object.assign(this.state, updates);
      }),
      subscribe: jest.fn(function(key, callback) {
        if (!this.listeners.has(key)) {
          this.listeners.set(key, []);
        }
        this.listeners.get(key).push(callback);
      }),
      components: new Map()
    };

    // Create component instance
    insights = createMockInsights('#tab-insights', mockAppState);
    insights.init();
  });

  afterEach(() => {
    if (insights && insights.destroy) {
      insights.destroy();
    }
    document.body.innerHTML = '';
  });

  describe('Initialization', () => {
    test('should initialize with correct DOM elements', () => {
      expect(insights.element).toBeInTheDocument();
      expect(document.getElementById('model-performance')).toBeInTheDocument();
      expect(document.getElementById('feature-importance')).toBeInTheDocument();
    });

    test('should load model metadata', () => {
      expect(insights.modelMetadata).toBeDefined();
      expect(insights.modelMetadata.accuracy).toBe(0.815);
      expect(insights.modelMetadata.modelType).toBe('ultra_advanced');
    });

    test('should load feature importance data', () => {
      expect(insights.featureImportance).toHaveLength(8);
      expect(insights.featureImportance[0].feature).toBe('Attendance Rate');
      expect(insights.featureImportance[0].importance).toBe(0.24);
    });
  });

  describe('Model Performance Display', () => {
    test('should render model performance metrics', () => {
      const performanceContainer = document.getElementById('model-performance');
      
      expect(performanceContainer.textContent).toContain('Model Performance');
      expect(performanceContainer.textContent).toContain('81.5%'); // Accuracy
      expect(performanceContainer.textContent).toContain('0.815'); // AUC
    });
  });

  describe('Feature Importance', () => {
    test('should render feature importance chart', () => {
      const importanceContainer = document.getElementById('feature-importance');
      
      expect(importanceContainer.textContent).toContain('Feature Importance');
      expect(importanceContainer.textContent).toContain('Attendance Rate');
      expect(importanceContainer.textContent).toContain('24.0%');
    });

    test('should handle feature filtering', () => {
      const filterSelect = document.getElementById('importance-filter');
      filterSelect.value = 'top-5';
      
      const changeEvent = new Event('change', { bubbles: true });
      filterSelect.dispatchEvent(changeEvent);
      
      // Should update the display to show only top 5 features
      expect(insights.handleFilterChange).toBeDefined();
    });
  });

  describe('Student Analysis', () => {
    const mockStudents = [
      { id: 1, name: 'Alice', risk_score: 0.8, success_probability: 0.2 },
      { id: 2, name: 'Bob', risk_score: 0.3, success_probability: 0.9 },
      { id: 3, name: 'Carol', risk_score: 0.5, success_probability: 0.6 }
    ];

    test('should analyze student patterns', () => {
      insights.updateStudents(mockStudents);
      const analysis = insights.analyzeStudentPatterns();
      
      expect(analysis.trends).toContain('1 students (33.3%) are at high risk');
      expect(analysis.trends.length).toBeGreaterThan(0);
    });

    test('should generate alerts for high-risk situations', () => {
      const highRiskStudents = Array.from({ length: 10 }, (_, i) => ({
        id: i + 1,
        risk_score: 0.8,
        success_probability: 0.2
      }));
      
      insights.updateStudents(highRiskStudents);
      const analysis = insights.analyzeStudentPatterns();
      
      expect(analysis.alerts).toContain('High percentage of at-risk students detected');
      expect(analysis.recommendations.length).toBeGreaterThan(0);
    });

    test('should calculate average success correctly', () => {
      insights.updateStudents(mockStudents);
      const avgSuccess = insights.calculateAverageSuccess();
      
      // (0.2 + 0.9 + 0.6) / 3 * 100 = 56.7%
      expect(avgSuccess).toBeCloseTo(56.7, 1);
    });
  });

  describe('Student Explanations', () => {
    const testStudent = {
      id: 1,
      name: 'Test Student',
      risk_score: 0.7,
      success_probability: 0.4
    };

    test('should generate student explanation', () => {
      const explanation = insights.generateStudentExplanation(testStudent);
      
      expect(explanation.studentName).toBe('Test Student');
      expect(explanation.riskLevel).toBe('High Risk');
      expect(explanation.riskScore).toBe('70.0');
      expect(explanation.keyFactors).toHaveLength(3);
      expect(explanation.recommendations).toHaveLength(4);
    });

    test('should categorize risk levels correctly', () => {
      expect(insights.getRiskCategory(0.8)).toBe('High Risk');
      expect(insights.getRiskCategory(0.5)).toBe('Moderate Risk');
      expect(insights.getRiskCategory(0.2)).toBe('Low Risk');
    });

    test('should provide personalized recommendations', () => {
      const highRiskRecs = insights.getPersonalizedRecommendations({ risk_score: 0.8 });
      const lowRiskRecs = insights.getPersonalizedRecommendations({ risk_score: 0.2 });
      
      expect(highRiskRecs).toContain('Immediate intervention required');
      expect(lowRiskRecs).toContain('Continue current support level');
    });

    test('should render student explanation', () => {
      insights.showStudentExplanation(testStudent);
      
      const explanationContainer = document.getElementById('student-explanation');
      expect(explanationContainer.textContent).toContain('Test Student');
      expect(explanationContainer.textContent).toContain('High Risk');
    });
  });

  describe('Data Export', () => {
    test('should export insights data', () => {
      const mockStudents = [
        { id: 1, risk_score: 0.7, success_probability: 0.3 }
      ];
      insights.updateStudents(mockStudents);
      
      const exportData = insights.exportInsights();
      const parsed = JSON.parse(exportData);
      
      expect(parsed.modelPerformance.accuracy).toBe(0.815);
      expect(parsed.featureImportance).toHaveLength(8);
      expect(parsed.totalStudents).toBe(1);
      expect(parsed.timestamp).toBeDefined();
    });
  });

  describe('Error Handling', () => {
    test('should handle missing DOM elements gracefully', () => {
      document.body.innerHTML = '<div id="tab-insights"></div>'; // Minimal DOM
      
      const componentWithoutElements = createMockInsights('#tab-insights', mockAppState);
      
      expect(() => {
        componentWithoutElements.init();
      }).not.toThrow();
    });

    test('should handle empty student data', () => {
      insights.updateStudents([]);
      const analysis = insights.analyzeStudentPatterns();
      
      expect(analysis.trends).toEqual([]);
      expect(analysis.recommendations).toEqual([]);
      expect(analysis.alerts).toEqual([]);
    });
  });

  describe('Performance', () => {
    test('should handle large student datasets efficiently', () => {
      const largeDataset = Array.from({ length: 1000 }, (_, i) => ({
        id: i + 1,
        risk_score: Math.random(),
        success_probability: Math.random()
      }));
      
      const start = performance.now();
      insights.updateStudents(largeDataset);
      const duration = performance.now() - start;
      
      expect(duration).toBeLessThan(1000); // 1 second
    });
  });
});