/**
 * Jest Configuration for Student Success Prediction
 * Designed for evolutionary testing across multiple environments and test types
 */

module.exports = {
  // Test environment configuration
  testEnvironment: 'jsdom',
  
  // Test discovery patterns (designed to scale with new components)
  testMatch: [
    '**/tests/**/*.test.js',
    '**/tests/**/*.spec.js',
    '**/__tests__/**/*.js'
  ],
  
  // Setup files for different test types
  setupFilesAfterEnv: [
    '<rootDir>/tests/utils/test-setup.js'
  ],
  
  // Module name mapping (future-proofs import paths)
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/mvp/static/js/$1',
    '^@components/(.*)$': '<rootDir>/src/mvp/static/js/components/$1',
    '^@core/(.*)$': '<rootDir>/src/mvp/static/js/core/$1',
    '^@systems/(.*)$': '<rootDir>/src/mvp/static/js/systems/$1',
    '^@test-utils/(.*)$': '<rootDir>/tests/utils/$1',
    '^@fixtures/(.*)$': '<rootDir>/tests/fixtures/$1',
    '^@mocks/(.*)$': '<rootDir>/tests/mocks/$1'
  },
  
  // Coverage configuration (evolves with codebase)
  collectCoverageFrom: [
    'src/mvp/static/js/**/*.js',
    '!src/mvp/static/js/**/*.config.js',
    '!src/mvp/static/js/**/*.test.js'
  ],
  
  // Coverage thresholds (can be adjusted as codebase matures)
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 70,
      lines: 70,
      statements: 70
    },
    // Component-specific thresholds (add as needed)
    'src/mvp/static/js/core/': {
      branches: 85,
      functions: 85,
      lines: 85,
      statements: 85
    }
  },
  
  // Simplified test configuration
  // Note: Project-based configuration can be re-enabled later
  // projects: [...],
  
  // Transform configuration (using default Node.js transforms)
  transform: {},
  
  // Clear mocks between tests (prevents test pollution)
  clearMocks: true,
  restoreMocks: true,
  
  // Test timeout (can be adjusted for slower integration tests)
  testTimeout: 10000,
  
  // Reporters (basic setup, can add more later)
  reporters: ['default']
};