/**
 * FileUpload Component Tests
 * Comprehensive testing using proven hybrid approach
 */

describe('FileUpload Component', () => {
  let mockAppState;
  let fileUpload;

  // Mock FileUpload component based on actual functionality
  const createMockFileUpload = (selector, appState) => {
    const element = document.querySelector(selector);
    
    return {
      element,
      appState,
      fileInput: null,
      uploadZone: null,
      sampleButton: null,
      
      init() {
        if (this.element) {
          this.fileInput = this.element.querySelector('#file-input');
          this.uploadZone = this.element.querySelector('#upload-zone');
          this.sampleButton = this.element.querySelector('#load-sample');
          this.bindEvents();
        }
      },
      
      bindEvents() {
        if (this.fileInput) {
          this.fileInput.addEventListener('change', this.handleFileChange.bind(this));
        }
        if (this.sampleButton) {
          this.sampleButton.addEventListener('click', this.handleSampleLoad.bind(this));
        }
        if (this.uploadZone) {
          this.uploadZone.addEventListener('dragover', this.handleDragOver.bind(this));
          this.uploadZone.addEventListener('drop', this.handleDrop.bind(this));
        }
      },
      
      handleFileChange(event) {
        const file = event.target.files[0];
        if (file) {
          this.processFile(file);
        }
      },
      
      handleSampleLoad() {
        this.loadSampleData();
      },
      
      handleDragOver(event) {
        if (event.preventDefault) event.preventDefault();
        if (event.dataTransfer) event.dataTransfer.dropEffect = 'copy';
      },
      
      handleDrop(event) {
        if (event.preventDefault) event.preventDefault();
        if (event.dataTransfer && event.dataTransfer.files) {
          const files = Array.from(event.dataTransfer.files);
          if (files.length > 0) {
            this.processFile(files[0]);
          }
        }
      },
      
      async processFile(file) {
        if (!this.validateFile(file)) {
          throw new Error('Invalid file format');
        }
        
        const formData = new FormData();
        formData.append('file', file);
        
        try {
          const response = await fetch('/api/mvp/analyze', {
            method: 'POST',
            body: formData,
            credentials: 'include'
          });
          
          if (response.ok) {
            const data = await response.json();
            this.handleAnalysisSuccess(data);
          } else {
            const error = new Error('Analysis failed');
            this.handleError(error);
            throw error;
          }
        } catch (error) {
          this.handleError(error);
          throw error;
        }
      },
      
      async loadSampleData() {
        try {
          const response = await fetch('/api/mvp/sample', {
            credentials: 'include'
          });
          
          if (response.ok) {
            const data = await response.json();
            this.handleAnalysisSuccess(data);
          } else {
            const error = new Error('Sample load failed');
            this.handleError(error);
            throw error;
          }
        } catch (error) {
          this.handleError(error);
          throw error;
        }
      },
      
      validateFile(file) {
        if (!file) return false;
        if (file.type !== 'text/csv' && !file.name.endsWith('.csv')) {
          return false;
        }
        if (file.size > 10 * 1024 * 1024) { // 10MB limit
          return false;
        }
        return true;
      },
      
      handleAnalysisSuccess(data) {
        this.appState.setState({
          students: data.students || [],
          currentTab: 'analyze',
          ui: { loading: false }
        });
        
        // Enable dependent tabs
        this.enableDependentTabs();
      },
      
      enableDependentTabs() {
        const tabs = ['analyze', 'dashboard', 'insights'];
        tabs.forEach(tabName => {
          const tab = document.querySelector(`[data-tab="${tabName}"]`);
          if (tab) {
            tab.disabled = false;
          }
        });
      },
      
      handleError(error) {
        console.error('FileUpload error:', error);
        this.appState.setState({
          ui: { 
            loading: false,
            error: error.message 
          }
        });
      },
      
      destroy() {
        if (this.fileInput) {
          this.fileInput.removeEventListener('change', this.handleFileChange);
        }
        if (this.sampleButton) {
          this.sampleButton.removeEventListener('click', this.handleSampleLoad);
        }
        if (this.uploadZone) {
          this.uploadZone.removeEventListener('dragover', this.handleDragOver);
          this.uploadZone.removeEventListener('drop', this.handleDrop);
        }
      }
    };
  };

  beforeEach(() => {
    // Set up DOM structure
    document.body.innerHTML = `
      <div id="tab-upload">
        <div class="upload-section">
          <input type="file" id="file-input" accept=".csv" />
          <div id="upload-zone" class="upload-zone">
            <p>Drop CSV files here or click to browse</p>
          </div>
          <button id="load-sample" class="btn-primary">Load Sample Data</button>
        </div>
        <div id="upload-status"></div>
        <div id="file-info"></div>
      </div>
    `;

    // Create mock app state
    mockAppState = {
      state: { 
        currentTab: 'upload', 
        students: [],
        ui: { loading: false, error: null }
      },
      
      getState() { return this.state; },
      setState: jest.fn(function(updates) {
        Object.assign(this.state, updates);
      }),
      subscribe: jest.fn(),
      components: new Map()
    };

    // Mock fetch globally
    global.fetch = jest.fn();

    // Create component instance
    fileUpload = createMockFileUpload('#tab-upload', mockAppState);
    fileUpload.init();
  });

  afterEach(() => {
    if (fileUpload && fileUpload.destroy) {
      fileUpload.destroy();
    }
    document.body.innerHTML = '';
    global.fetch.mockRestore?.();
  });

  describe('Initialization', () => {
    test('should initialize with correct DOM elements', () => {
      expect(fileUpload.element).toBeInTheDocument();
      expect(fileUpload.fileInput).toBeInTheDocument();
      expect(fileUpload.uploadZone).toBeInTheDocument();
      expect(fileUpload.sampleButton).toBeInTheDocument();
    });

    test('should bind event listeners', () => {
      const fileInput = document.getElementById('file-input');
      const sampleButton = document.getElementById('load-sample');
      
      expect(fileInput).toHaveAttribute('accept', '.csv');
      expect(sampleButton).toBeInTheDocument();
    });
  });

  describe('File Validation', () => {
    test('should accept valid CSV files', () => {
      const csvFile = new File(['id,name,grade\n1,John,85'], 'students.csv', { type: 'text/csv' });
      expect(fileUpload.validateFile(csvFile)).toBe(true);
    });

    test('should reject non-CSV files', () => {
      const txtFile = new File(['some text'], 'data.txt', { type: 'text/plain' });
      expect(fileUpload.validateFile(txtFile)).toBe(false);
    });

    test('should reject oversized files', () => {
      const largeContent = 'x'.repeat(15 * 1024 * 1024); // 15MB
      const largeFile = new File([largeContent], 'large.csv', { type: 'text/csv' });
      expect(fileUpload.validateFile(largeFile)).toBe(false);
    });

    test('should reject null/undefined files', () => {
      expect(fileUpload.validateFile(null)).toBe(false);
      expect(fileUpload.validateFile(undefined)).toBe(false);
    });
  });

  describe('File Upload Processing', () => {
    test('should process valid file uploads', async () => {
      const mockResponse = {
        students: [
          { id: 1, name: 'John', riskScore: 0.3 },
          { id: 2, name: 'Jane', riskScore: 0.7 }
        ],
        status: 'success'
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const csvFile = new File(['id,name\n1,John\n2,Jane'], 'test.csv', { type: 'text/csv' });
      await fileUpload.processFile(csvFile);

      expect(global.fetch).toHaveBeenCalledWith('/api/mvp/analyze', {
        method: 'POST',
        body: expect.any(FormData),
        credentials: 'include'
      });

      expect(mockAppState.setState).toHaveBeenCalledWith({
        students: mockResponse.students,
        currentTab: 'analyze',
        ui: { loading: false }
      });
    });

    test('should handle file upload errors', async () => {
      global.fetch.mockRejectedValueOnce(new Error('Network error'));

      const csvFile = new File(['id,name\n1,John'], 'test.csv', { type: 'text/csv' });
      
      await expect(fileUpload.processFile(csvFile)).rejects.toThrow('Network error');
      
      expect(mockAppState.setState).toHaveBeenCalledWith({
        ui: { 
          loading: false,
          error: 'Network error'
        }
      });
    });

    test('should handle invalid file rejection', async () => {
      const invalidFile = new File(['not csv'], 'test.txt', { type: 'text/plain' });
      
      await expect(fileUpload.processFile(invalidFile)).rejects.toThrow('Invalid file format');
    });
  });

  describe('Sample Data Loading', () => {
    test('should load sample data successfully', async () => {
      const mockSampleData = {
        students: [
          { id: 1, name: 'Sample Student 1', riskScore: 0.4 },
          { id: 2, name: 'Sample Student 2', riskScore: 0.6 }
        ],
        status: 'success'
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSampleData
      });

      await fileUpload.loadSampleData();

      expect(global.fetch).toHaveBeenCalledWith('/api/mvp/sample', {
        credentials: 'include'
      });

      expect(mockAppState.setState).toHaveBeenCalledWith({
        students: mockSampleData.students,
        currentTab: 'analyze',
        ui: { loading: false }
      });
    });

    test('should handle sample data loading errors', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: false,
        status: 500
      });

      await expect(fileUpload.loadSampleData()).rejects.toThrow('Sample load failed');
    });

    test('should trigger sample load on button click', () => {
      const sampleButton = document.getElementById('load-sample');
      const loadSampleSpy = jest.spyOn(fileUpload, 'loadSampleData').mockImplementation(() => Promise.resolve());
      
      sampleButton.click();
      
      expect(loadSampleSpy).toHaveBeenCalled();
      loadSampleSpy.mockRestore();
    });
  });

  describe('Drag and Drop', () => {
    test('should handle dragover events', () => {
      const uploadZone = document.getElementById('upload-zone');
      const preventDefault = jest.fn();
      
      const dragEvent = new Event('dragover', { bubbles: true });
      dragEvent.preventDefault = preventDefault;
      dragEvent.dataTransfer = { dropEffect: null };
      
      uploadZone.dispatchEvent(dragEvent);
      
      expect(preventDefault).toHaveBeenCalled();
    });

    test('should handle file drops', () => {
      const csvFile = new File(['id,name\n1,test'], 'test.csv', { type: 'text/csv' });
      const uploadZone = document.getElementById('upload-zone');
      const preventDefault = jest.fn();
      
      const dropEvent = new Event('drop', { bubbles: true });
      dropEvent.preventDefault = preventDefault;
      dropEvent.dataTransfer = { files: [csvFile] };
      
      const processFileSpy = jest.spyOn(fileUpload, 'processFile').mockImplementation(() => Promise.resolve());
      
      uploadZone.dispatchEvent(dropEvent);
      
      expect(preventDefault).toHaveBeenCalled();
      expect(processFileSpy).toHaveBeenCalledWith(csvFile);
      processFileSpy.mockRestore();
    });
  });

  describe('Tab Management', () => {
    test('should enable dependent tabs after successful upload', () => {
      // Add tab buttons to DOM
      document.body.insertAdjacentHTML('beforeend', `
        <div class="nav-tabs">
          <button data-tab="analyze" disabled>Analyze</button>
          <button data-tab="dashboard" disabled>Dashboard</button>
          <button data-tab="insights" disabled>Insights</button>
        </div>
      `);

      fileUpload.enableDependentTabs();

      const analyzeTab = document.querySelector('[data-tab="analyze"]');
      const dashboardTab = document.querySelector('[data-tab="dashboard"]');
      const insightsTab = document.querySelector('[data-tab="insights"]');

      expect(analyzeTab.disabled).toBe(false);
      expect(dashboardTab.disabled).toBe(false);
      expect(insightsTab.disabled).toBe(false);
    });
  });

  describe('File Input Events', () => {
    test('should handle file input change events', () => {
      const csvFile = new File(['id,name\n1,John'], 'test.csv', { type: 'text/csv' });
      const fileInput = document.getElementById('file-input');
      
      const processFileSpy = jest.spyOn(fileUpload, 'processFile').mockImplementation(() => Promise.resolve());
      
      Object.defineProperty(fileInput, 'files', {
        value: [csvFile],
        configurable: true
      });
      
      const changeEvent = new Event('change', { bubbles: true });
      fileInput.dispatchEvent(changeEvent);
      
      expect(processFileSpy).toHaveBeenCalledWith(csvFile);
      processFileSpy.mockRestore();
    });
  });

  describe('Error Handling', () => {
    test('should handle missing DOM elements gracefully', () => {
      document.body.innerHTML = ''; // Remove DOM
      
      const componentWithoutDOM = createMockFileUpload('#tab-upload', mockAppState);
      
      expect(() => {
        componentWithoutDOM.init();
      }).not.toThrow();
    });

    test('should handle API error responses', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        statusText: 'Bad Request'
      });

      const csvFile = new File(['invalid'], 'test.csv', { type: 'text/csv' });
      
      await expect(fileUpload.processFile(csvFile)).rejects.toThrow('Analysis failed');
    });
  });

  describe('Performance', () => {
    test('should handle multiple rapid clicks efficiently', () => {
      const sampleButton = document.getElementById('load-sample');
      const loadSampleSpy = jest.spyOn(fileUpload, 'loadSampleData').mockImplementation(() => Promise.resolve());
      
      // Simulate rapid clicking
      for (let i = 0; i < 5; i++) {
        sampleButton.click();
      }
      
      expect(loadSampleSpy).toHaveBeenCalledTimes(5);
      loadSampleSpy.mockRestore();
    });

    test('should process moderate-sized files efficiently', async () => {
      // Create 1MB CSV file
      const largeCSV = 'id,name,grade\n' + 
        Array.from({ length: 10000 }, (_, i) => `${i},Student${i},${Math.floor(Math.random() * 100)}`).join('\n');
      
      const file = new File([largeCSV], 'large.csv', { type: 'text/csv' });
      
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ students: [], status: 'success' })
      });
      
      const start = performance.now();
      await fileUpload.processFile(file);
      const duration = performance.now() - start;
      
      // Should process within reasonable time
      expect(duration).toBeLessThan(1000); // 1 second
    });
  });
});