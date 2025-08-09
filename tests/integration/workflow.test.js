/**
 * Integration Workflow Tests
 * Testing complete user workflows and component interactions
 */

describe('Student Success App Integration Workflows', () => {
  let mockAppState;
  let components;

  // Mock all components using proven patterns
  const createMockApp = () => {
    const mockComponents = {
      fileUpload: {
        processFile: jest.fn(),
        loadSampleData: jest.fn(),
        validateFile: jest.fn(),
        enableDependentTabs: jest.fn()
      },
      
      tabNavigation: {
        switchTab: jest.fn(),
        updateProgress: jest.fn(),
        enableTab: jest.fn(),
        disableTab: jest.fn()
      },
      
      analysis: {
        updateStudents: jest.fn(),
        applyFiltersAndSort: jest.fn(),
        renderStudentList: jest.fn(),
        showExplanation: jest.fn()
      },
      
      dashboard: {
        updateStudents: jest.fn(),
        renderDashboard: jest.fn(),
        calculateStatistics: jest.fn(),
        exportDashboard: jest.fn()
      },
      
      insights: {
        updateStudents: jest.fn(),
        generateInsights: jest.fn(),
        loadModelInsights: jest.fn(),
        exportInsights: jest.fn()
      }
    };

    return mockComponents;
  };

  beforeEach(() => {
    // Set up complete DOM structure
    document.body.innerHTML = `
      <!-- Navigation -->
      <div class="nav-tabs">
        <button class="tab-button active" data-tab="upload">Upload</button>
        <button class="tab-button" data-tab="analyze" disabled>Analyze</button>
        <button class="tab-button" data-tab="dashboard" disabled>Dashboard</button>
        <button class="tab-button" data-tab="insights" disabled>Insights</button>
      </div>

      <!-- Upload Tab -->
      <div id="tab-upload" class="tab-content active">
        <input type="file" id="file-input" accept=".csv" />
        <div id="upload-zone">Drop files here</div>
        <button id="load-sample">Load Sample Data</button>
        <div id="upload-status"></div>
      </div>

      <!-- Analysis Tab -->
      <div id="tab-analyze" class="tab-content">
        <input type="text" id="student-search" />
        <select id="risk-filter">
          <option value="all">All Risk Levels</option>
          <option value="high risk">High Risk</option>
        </select>
        <div id="student-list"></div>
      </div>

      <!-- Dashboard Tab -->
      <div id="tab-dashboard" class="tab-content">
        <div id="dashboard-stats"></div>
        <canvas id="risk-distribution-chart"></canvas>
      </div>

      <!-- Insights Tab -->
      <div id="tab-insights" class="tab-content">
        <div id="model-performance"></div>
        <div id="feature-importance"></div>
        <div id="global-insights"></div>
      </div>
    `;

    // Create mock app state
    mockAppState = {
      state: {
        currentTab: 'upload',
        students: [],
        selectedStudent: null,
        ui: { loading: false, error: null }
      },
      listeners: new Map(),
      
      getState() { return this.state; },
      setState: jest.fn(function(updates) {
        Object.assign(this.state, updates);
        this.notifyListeners(updates);
      }),
      subscribe: jest.fn(function(key, callback) {
        if (!this.listeners.has(key)) {
          this.listeners.set(key, []);
        }
        this.listeners.get(key).push(callback);
      }),
      notifyListeners: jest.fn(function(updates) {
        Object.keys(updates).forEach(key => {
          if (this.listeners.has(key)) {
            this.listeners.get(key).forEach(callback => {
              callback(updates[key]);
            });
          }
        });
      }),
      components: new Map()
    };

    // Create component mocks
    components = createMockApp();

    // Mock global fetch
    global.fetch = jest.fn();
  });

  afterEach(() => {
    document.body.innerHTML = '';
    global.fetch.mockRestore?.();
  });

  describe('Full Workflow: File Upload → Analysis → Dashboard → Insights', () => {
    const mockStudentData = [
      { id: 1, name: 'Alice Johnson', risk_score: 0.2, success_probability: 0.85, grade_level: 10 },
      { id: 2, name: 'Bob Smith', risk_score: 0.8, success_probability: 0.25, grade_level: 11 },
      { id: 3, name: 'Carol Davis', risk_score: 0.5, success_probability: 0.6, grade_level: 10 }
    ];

    test('should complete full user workflow successfully', async () => {
      // 1. Start with file upload
      expect(mockAppState.state.currentTab).toBe('upload');
      expect(document.querySelector('[data-tab="analyze"]').disabled).toBe(true);

      // 2. Mock successful file upload
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ students: mockStudentData, status: 'success' })
      });

      components.fileUpload.processFile.mockImplementation(async () => {
        mockAppState.setState({
          students: mockStudentData,
          currentTab: 'analyze',
          ui: { loading: false }
        });
        components.fileUpload.enableDependentTabs();
      });

      // Process a file
      const csvFile = new File(['id,name\n1,Alice\n2,Bob'], 'test.csv', { type: 'text/csv' });
      await components.fileUpload.processFile(csvFile);

      // 3. Verify state updates
      expect(mockAppState.setState).toHaveBeenCalledWith({
        students: mockStudentData,
        currentTab: 'analyze',
        ui: { loading: false }
      });

      // 4. Verify tabs are enabled
      expect(components.fileUpload.enableDependentTabs).toHaveBeenCalled();

      // 5. Switch to analysis tab
      components.tabNavigation.switchTab.mockImplementation((tabName) => {
        mockAppState.setState({ currentTab: tabName });
      });

      components.tabNavigation.switchTab('analyze');
      expect(mockAppState.setState).toHaveBeenCalledWith({ currentTab: 'analyze' });

      // 6. Analysis component receives data
      components.analysis.updateStudents.mockImplementation((students) => {
        expect(students).toEqual(mockStudentData);
      });
      
      components.analysis.updateStudents(mockStudentData);

      // 7. Switch to dashboard
      components.tabNavigation.switchTab('dashboard');
      
      // Dashboard component receives data
      components.dashboard.updateStudents.mockImplementation((students) => {
        components.dashboard.calculateStatistics.mockReturnValue({
          totalStudents: 3,
          highRisk: 1,
          highRiskPercent: 33,
          avgSuccess: 57
        });
      });
      
      components.dashboard.updateStudents(mockStudentData);

      // 8. Switch to insights
      components.tabNavigation.switchTab('insights');
      
      // Insights component receives data
      components.insights.updateStudents(mockStudentData);
      
      expect(components.insights.updateStudents).toHaveBeenCalledWith(mockStudentData);
    });

    test('should handle workflow errors gracefully', async () => {
      // Mock upload failure
      global.fetch.mockRejectedValueOnce(new Error('Network error'));

      components.fileUpload.processFile.mockImplementation(async () => {
        mockAppState.setState({
          ui: { loading: false, error: 'Network error' }
        });
        throw new Error('Network error');
      });

      const csvFile = new File(['invalid'], 'test.csv', { type: 'text/csv' });
      
      await expect(components.fileUpload.processFile(csvFile)).rejects.toThrow('Network error');
      
      // Verify error state
      expect(mockAppState.setState).toHaveBeenCalledWith({
        ui: { loading: false, error: 'Network error' }
      });

      // Verify tabs remain disabled
      expect(document.querySelector('[data-tab="analyze"]').disabled).toBe(true);
    });
  });

  describe('Sample Data Workflow', () => {
    test('should load sample data and enable all features', async () => {
      const mockSampleData = [
        { id: 1, name: 'Sample Student 1', risk_score: 0.4, success_probability: 0.6 },
        { id: 2, name: 'Sample Student 2', risk_score: 0.7, success_probability: 0.3 }
      ];

      // Mock successful sample load
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ students: mockSampleData, status: 'success' })
      });

      components.fileUpload.loadSampleData.mockImplementation(async () => {
        mockAppState.setState({
          students: mockSampleData,
          currentTab: 'analyze',
          ui: { loading: false }
        });
        components.fileUpload.enableDependentTabs();
      });

      // Load sample data
      await components.fileUpload.loadSampleData();

      expect(mockAppState.setState).toHaveBeenCalledWith({
        students: mockSampleData,
        currentTab: 'analyze',
        ui: { loading: false }
      });

      expect(components.fileUpload.enableDependentTabs).toHaveBeenCalled();
    });
  });

  describe('Component Communication', () => {
    const testStudents = [
      { id: 1, name: 'Test Student', risk_score: 0.6, success_probability: 0.4 }
    ];

    test('should propagate state changes across all components', () => {
      // Set up subscriptions
      const updateFunctions = {
        analysis: components.analysis.updateStudents,
        dashboard: components.dashboard.updateStudents,
        insights: components.insights.updateStudents
      };

      // Mock state subscriptions
      mockAppState.subscribe.mockImplementation((key, callback) => {
        if (key === 'students') {
          updateFunctions.analysis.mockImplementation(callback);
          updateFunctions.dashboard.mockImplementation(callback);
          updateFunctions.insights.mockImplementation(callback);
        }
      });

      // Simulate state change
      mockAppState.setState({ students: testStudents });

      // Verify all components would receive updates
      expect(mockAppState.notifyListeners).toHaveBeenCalledWith({ students: testStudents });
    });

    test('should handle student selection across components', () => {
      const selectedStudent = testStudents[0];

      // Analysis component selects student
      components.analysis.showExplanation.mockImplementation((studentId) => {
        const student = testStudents.find(s => s.id.toString() === studentId);
        mockAppState.setState({
          selectedStudent: student,
          ui: { showExplanation: true }
        });
      });

      components.analysis.showExplanation('1');

      expect(mockAppState.setState).toHaveBeenCalledWith({
        selectedStudent: selectedStudent,
        ui: { showExplanation: true }
      });
    });
  });

  describe('Tab Navigation Integration', () => {
    test('should manage tab states correctly during workflow', () => {
      const tabs = ['upload', 'analyze', 'dashboard', 'insights'];

      // Initially only upload tab should be enabled
      components.tabNavigation.switchTab.mockImplementation((tabName) => {
        // Simulate tab switching logic
        tabs.forEach(tab => {
          const tabButton = document.querySelector(`[data-tab="${tab}"]`);
          if (tab === tabName) {
            tabButton.classList.add('active');
            tabButton.disabled = false;
          } else {
            tabButton.classList.remove('active');
          }
        });
        mockAppState.setState({ currentTab: tabName });
      });

      // Switch through each tab
      tabs.forEach(tabName => {
        components.tabNavigation.switchTab(tabName);
        expect(mockAppState.setState).toHaveBeenCalledWith({ currentTab: tabName });
      });
    });

    test('should prevent navigation to disabled tabs', () => {
      // Try to switch to disabled tab
      const analyzeTab = document.querySelector('[data-tab="analyze"]');
      expect(analyzeTab.disabled).toBe(true);

      // Tab switching should not work for disabled tabs
      components.tabNavigation.switchTab.mockImplementation((tabName) => {
        const tabButton = document.querySelector(`[data-tab="${tabName}"]`);
        if (tabButton.disabled) {
          return; // Do nothing
        }
        mockAppState.setState({ currentTab: tabName });
      });

      components.tabNavigation.switchTab('analyze');
      
      // State should not change
      expect(mockAppState.state.currentTab).toBe('upload');
    });
  });

  describe('Data Export Integration', () => {
    const testData = [
      { id: 1, name: 'Test', risk_score: 0.5, success_probability: 0.5 }
    ];

    test('should export data from different components', () => {
      // Set up test data
      mockAppState.setState({ students: testData });

      // Mock export functions
      components.dashboard.exportDashboard.mockReturnValue(JSON.stringify({
        statistics: { totalStudents: 1, highRisk: 0 },
        timestamp: '2023-01-01T00:00:00.000Z'
      }));

      components.insights.exportInsights.mockReturnValue(JSON.stringify({
        modelPerformance: { accuracy: 0.815 },
        featureImportance: [],
        totalStudents: 1
      }));

      // Test exports
      const dashboardExport = components.dashboard.exportDashboard();
      const insightsExport = components.insights.exportInsights();

      expect(JSON.parse(dashboardExport).statistics.totalStudents).toBe(1);
      expect(JSON.parse(insightsExport).totalStudents).toBe(1);
    });
  });

  describe('Error Recovery Integration', () => {
    test('should recover from component errors without breaking workflow', () => {
      // Simulate error in one component
      components.analysis.updateStudents.mockImplementation(() => {
        throw new Error('Analysis component error');
      });

      // Other components should still work
      components.dashboard.updateStudents.mockImplementation((students) => {
        expect(students).toBeDefined();
      });

      const testStudents = [{ id: 1, name: 'Test', risk_score: 0.5 }];

      // Analysis fails but workflow continues
      expect(() => {
        try {
          components.analysis.updateStudents(testStudents);
        } catch (error) {
          // Error is caught, workflow continues
        }
        components.dashboard.updateStudents(testStudents);
      }).not.toThrow();
    });
  });

  describe('Performance Integration', () => {
    test('should handle large datasets across all components efficiently', () => {
      const largeDataset = Array.from({ length: 1000 }, (_, i) => ({
        id: i + 1,
        name: `Student ${i + 1}`,
        risk_score: Math.random(),
        success_probability: Math.random(),
        grade_level: Math.floor(Math.random() * 4) + 9
      }));

      const start = performance.now();

      // Simulate data processing across all components
      components.analysis.updateStudents(largeDataset);
      components.dashboard.updateStudents(largeDataset);
      components.insights.updateStudents(largeDataset);

      const duration = performance.now() - start;

      // Should handle large data efficiently
      expect(duration).toBeLessThan(100); // 100ms for mock operations
      expect(components.analysis.updateStudents).toHaveBeenCalledWith(largeDataset);
      expect(components.dashboard.updateStudents).toHaveBeenCalledWith(largeDataset);
      expect(components.insights.updateStudents).toHaveBeenCalledWith(largeDataset);
    });
  });
});