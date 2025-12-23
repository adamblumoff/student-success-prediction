import { defineConfig } from 'vitest/config';
import { alias, coverageDefaults } from './vitest.shared';

export default defineConfig({
  root: '.',
  resolve: { alias },
  test: {
    name: 'integration',
    environment: 'node',
    setupFiles: ['./tests/setup.integration.ts'],
    include: ['./tests/integration/**/*.test.ts'],
    env: {
      NODE_ENV: 'test'
    },
    pool: 'threads',
    fileParallelism: false,
    poolOptions: {
      threads: {
        singleThread: true
      }
    },
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
