# Testing Infrastructure Documentation

## Overview

This project implements a comprehensive, evolutionary testing infrastructure designed to adapt and scale with the application's growth. The testing framework is built on Jest with a component-based architecture that mirrors the application structure.

## Quick Start

```bash
# Install dependencies
npm install

# Run all tests
npm test

# Run specific test categories
npm run test:unit          # Unit tests only
npm run test:integration   # Integration tests only
npm run test:component     # Component tests only

# Watch mode for development
npm run test:watch         # Watch all tests
npm run test:watch:unit    # Watch unit tests only

# Generate coverage report
npm run test:coverage

# Run CI pipeline
npm run test:ci

# Validate test structure
npm run test:validate
```

## Architecture

### Test Categories

Our testing framework organizes tests into six evolutionary categories:

1. **Unit Tests** (`tests/unit/`): Individual component and function testing
2. **Integration Tests** (`tests/integration/`): Component interaction testing
3. **Component Tests** (`tests/component/`): Full component with DOM interaction
4. **API Tests** (`tests/api/`): Backend endpoint testing
5. **E2E Tests** (`tests/e2e/`): End-to-end user workflows
6. **Performance Tests** (`tests/performance/`): Load and performance testing

### Core Utilities

#### Component Test Factory (`tests/utils/component-test-utils.js`)
```javascript
import { componentTestFactory } from '@test-utils/component-test-utils.js';

// Create component test context
const testContext = await componentTestFactory.createComponentTest(ComponentClass, {
  selector: '#component-container',
  initialState: { currentTab: 'upload' }
});

// Use in tests
const { component, appState, user } = testContext;
```

#### Test Helpers (`tests/utils/test-helpers.js`)
```javascript
import { 
  waitForAsyncOperations,
  createMockFile,
  fireEvent,
  expectAsyncError 
} from '@test-utils/test-helpers.js';

// Wait for async operations
await waitForAsyncOperations();

// Create mock files for upload testing
const csvFile = createMockFile('id,name\n1,Test', 'test.csv');

// Fire DOM events
fireEvent(element, 'click');
```

#### Test Fixtures (`tests/fixtures/student-data.js`)
```javascript
import { TestDataFactory } from '@test-utils/component-test-utils.js';

// Generate realistic test data
const students = TestDataFactory.createStudents(10, {
  riskDistribution: { high: 0.2, moderate: 0.3, low: 0.5 }
});
```

## Writing Tests

### Unit Test Example
```javascript
// tests/unit/components/tab-navigation.test.js
import { componentTestFactory } from '@test-utils/component-test-utils.js';

describe('TabNavigation Component', () => {
  let testContext;

  beforeEach(async () => {
    testContext = await componentTestFactory.createComponentTest(TabNavigation, {
      initialState: { currentTab: 'upload' }
    });
  });

  afterEach(() => {
    testContext.cleanup();
  });

  test('should handle tab clicks', async () => {
    const { user, container, appState } = testContext;
    
    const analyzeTab = container.querySelector('[data-tab="analyze"]');
    await user.click(analyzeTab);
    
    expect(appState.setState).toHaveBeenCalledWith({ currentTab: 'analyze' });
  });
});
```

### Integration Test Example
```javascript
// tests/integration/file-upload-workflow.test.js
describe('File Upload Workflow', () => {
  test('should handle complete upload workflow', async () => {
    // Set up multiple components
    const appState = createMockAppState();
    const fileUpload = new FileUpload('#upload', appState);
    const analysis = new Analysis('#analysis', appState);
    
    // Simulate file upload
    const csvFile = createMockFile('data', 'test.csv');
    await user.upload(fileInput, csvFile);
    
    // Verify cross-component communication
    expect(appState.setState).toHaveBeenCalledWith({
      students: expect.any(Array),
      currentTab: 'analyze'
    });
  });
});
```

## Evolutionary Testing Principles

### 1. Future-Proof Test Structure
Tests are designed to adapt to changing component architectures:

```javascript
// Dynamic imports support refactoring
const module = await import('../../../src/mvp/static/js/components/tab-navigation.js');
const TabNavigation = module.default || module.TabNavigation;
```

### 2. Adaptive Data Structures
Test fixtures evolve with data models:

```javascript
// Support both current and future data formats
const enhancedStudent = {
  ...baseStudent,
  // Future fields
  socialEmotionalData: { resilience: 0.8 },
  interventionHistory: []
};
```

### 3. Component Test Factory Pattern
Standardized component testing that scales with new component types:

```javascript
export class ComponentTestFactory {
  async createComponentTest(ComponentClass, options = {}) {
    // Automatically adapts to new component patterns
    const mockAppState = this.createMockAppState(options.initialState);
    const component = new ComponentClass(options.selector, mockAppState);
    
    return {
      component,
      appState: mockAppState,
      user: userEvent.setup(),
      cleanup: () => this.cleanup(component, mockAppState)
    };
  }
}
```

## Test Environment Configuration

### Jest Configuration (`jest.config.js`)
```javascript
module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: [
    '<rootDir>/tests/setup/test-setup.js'
  ],
  projects: [
    {
      displayName: 'unit',
      testMatch: ['<rootDir>/tests/unit/**/*.test.js']
    },
    {
      displayName: 'integration', 
      testMatch: ['<rootDir>/tests/integration/**/*.test.js']
    }
  ]
};
```

### Test Setup Files
- `tests/setup/test-setup.js`: Global test configuration
- `tests/setup/unit-setup.js`: Unit test specific setup
- `tests/setup/integration-setup.js`: Integration test setup
- `tests/setup/component-setup.js`: Component test DOM setup

## CI/CD Integration

### GitHub Actions Example
```yaml
- name: Run Test Suite
  run: npm run test:ci

- name: Generate Test Report  
  run: npm run test:report

- name: Validate Test Structure
  run: npm run test:validate
```

### Test Scripts
```bash
# CI-optimized test runner
npm run test:ci

# Generate comprehensive test report
npm run test:report

# Validate test file organization
npm run test:validate

# Run full test suite with coverage
npm run test:all
```

## Performance Testing

### Component Performance
```javascript
import { measureComponentRenderTime } from '@test-utils/test-helpers.js';

test('should render component efficiently', async () => {
  const { component, renderTime } = await measureComponentRenderTime(() => 
    new ComponentClass('#container', mockAppState)
  );
  
  expect(renderTime).toBeLessThan(100); // 100ms threshold
});
```

### Large Dataset Testing
```javascript
test('should handle large datasets', async () => {
  const largeDataset = TestDataFactory.createStudents(1000);
  
  const start = performance.now();
  appState.setState({ students: largeDataset });
  const duration = performance.now() - start;
  
  expect(duration).toBeLessThan(2000); // 2 second threshold
});
```

## Debugging Tests

### Debug Individual Tests
```bash
# Run specific test file
npx jest tests/unit/components/tab-navigation.test.js

# Run with verbose output
npx jest --verbose tests/unit/

# Debug with Node inspector
node --inspect-brk node_modules/.bin/jest --runInBand
```

### Memory Leak Detection
```javascript
import { detectMemoryLeaks } from '@test-utils/test-cleanup.js';

afterEach(() => {
  const warnings = detectMemoryLeaks();
  if (warnings.length > 0) {
    console.warn('Memory leak warnings:', warnings);
  }
});
```

## Best Practices

### 1. Test Isolation
- Each test should be completely independent
- Use `beforeEach`/`afterEach` for setup/cleanup
- Clear global state between tests

### 2. Realistic Test Data
- Use TestDataFactory for consistent, realistic data
- Test with various data distributions (high/moderate/low risk)
- Include edge cases and boundary conditions

### 3. Future-Proof Tests
- Use dynamic imports for component loading
- Design tests to handle new data fields gracefully
- Write adaptive tests that evolve with the application

### 4. Performance Awareness
- Set reasonable performance thresholds
- Test with large datasets
- Monitor test execution time

### 5. Clear Test Structure
- Descriptive test names that explain the scenario
- Group related tests in describe blocks
- Use consistent naming conventions

## Troubleshooting

### Common Issues

**Import Errors**
```bash
# Ensure module path mapping is correct
npm run test:validate
```

**DOM Not Available**
```javascript
// Check jsdom environment in jest.config.js
testEnvironment: 'jsdom'
```

**Async Test Failures**
```javascript
// Always await async operations
await waitForAsyncOperations();
```

**Memory Leaks**
```javascript
// Use proper cleanup in afterEach
afterEach(() => {
  testContext.cleanup();
});
```

## Future Enhancements

The testing infrastructure is designed to evolve with these potential additions:

1. **Visual Regression Testing**: Screenshot comparison for UI components
2. **Accessibility Testing**: Automated a11y checks
3. **Cross-Browser Testing**: Multi-browser compatibility
4. **API Contract Testing**: Schema validation for backend integration
5. **Load Testing**: Stress testing for high user volumes
6. **Mobile Testing**: Touch interaction and responsive design

## Contributing

When adding new tests:

1. Follow the established patterns in existing tests
2. Use the ComponentTestFactory for component tests
3. Add appropriate fixtures to `tests/fixtures/`
4. Update this documentation if adding new patterns
5. Run `npm run test:validate` to ensure proper structure

---

This testing infrastructure provides a solid foundation that will evolve with your application, ensuring comprehensive test coverage while maintaining developer productivity and code quality.