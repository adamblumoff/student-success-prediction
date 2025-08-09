/**
 * Global Test Setup
 * Provides foundation utilities available to all test types
 */

require('@testing-library/jest-dom');
const { TextEncoder, TextDecoder } = require('util');

// Polyfills for jsdom environment
global.TextEncoder = TextEncoder;
global.TextDecoder = TextDecoder;

// Global fetch mock (evolves with API changes)
global.fetch = jest.fn();

// Global DOM utilities
global.createMockElement = (tag, attributes = {}) => {
  const element = document.createElement(tag);
  Object.entries(attributes).forEach(([key, value]) => {
    element.setAttribute(key, value);
  });
  return element;
};

// Clean up after each test
afterEach(() => {
  // Clear all mocks
  jest.clearAllMocks();
  
  // Clean up DOM
  document.body.innerHTML = '';
  document.head.innerHTML = '';
  
  // Clear any global state
  if (window.modernApp) {
    delete window.modernApp;
  }
  
  // Clear event listeners
  window.removeEventListener = jest.fn();
  window.addEventListener = jest.fn();
});

// Error handling for tests
const originalConsoleError = console.error;
console.error = (...args) => {
  // Suppress known React/testing warnings in development
  if (
    args[0]?.includes?.('Warning:') ||
    args[0]?.includes?.('validateDOMNesting')
  ) {
    return;
  }
  originalConsoleError.call(console, ...args);
};

// Test environment indicators
global.isTestEnvironment = true;
global.testStartTime = Date.now();