import { defineConfig } from 'vitest/config';
import { alias, coverageDefaults } from './vitest.shared';

export default defineConfig({
  root: '.',
  resolve: { alias },
  test: {
    name: 'unit',
    environment: 'jsdom',
    setupFiles: ['./tests/setup.unit.ts'],
    include: ['./tests/unit/**/*.test.ts', './tests/unit/**/*.test.tsx'],
    coverage: {
      ...coverageDefaults,
      thresholds: {
        lines: 85,
        branches: 75,
        functions: 80,
        statements: 85
      }
    }
  }
});
