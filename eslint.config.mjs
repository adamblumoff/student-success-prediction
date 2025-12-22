import path from 'node:path';
import { fileURLToPath } from 'node:url';
import next from 'eslint-config-next';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const config = [
  {
    ignores: ['node_modules/**', 'apps/web/node_modules/**', 'apps/web/.next/**'],
    settings: {
      next: {
        rootDir: ['apps/web']
      }
    }
  },
  ...next,
  {
    files: ['apps/web/**/*.{js,jsx,ts,tsx}'],
    settings: {
      next: {
        rootDir: ['apps/web']
      }
    },
    languageOptions: {
      parserOptions: {
        project: path.join(__dirname, 'apps/web/tsconfig.json')
      }
    }
  }
];

export default config;
