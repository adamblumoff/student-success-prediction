import path from 'path';

export const coverageDefaults = {
  provider: 'v8' as const,
  reporter: ['text', 'lcov'],
  exclude: [
    '**/node_modules/**',
    '**/.next/**',
    '**/public/**',
    '**/db/migrations/**',
    '**/tests/**',
    '**/app/**/page.tsx',
    '**/app/**/layout.tsx',
    '**/app/**/globals.css'
  ] as string[]
};

export const alias = {
  '@': path.resolve(__dirname, '.')
};
