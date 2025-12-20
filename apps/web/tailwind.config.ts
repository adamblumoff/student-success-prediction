import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './app/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './lib/**/*.{ts,tsx}'
  ],
  theme: {
    extend: {
      fontFamily: {
        display: ['var(--font-display)', 'ui-sans-serif', 'system-ui'],
        body: ['var(--font-body)', 'ui-sans-serif', 'system-ui']
      },
      colors: {
        ink: {
          50: '#f7f7f2',
          100: '#e9e7dd',
          200: '#cfcbb8',
          300: '#b2ac93',
          400: '#8c846f',
          500: '#6f6655',
          600: '#544d41',
          700: '#3e3a33',
          800: '#2a2824',
          900: '#191816',
          950: '#0b0f14'
        },
        sage: {
          50: '#f3f7f4',
          100: '#dce8df',
          200: '#b8d1c0',
          300: '#92b9a0',
          400: '#6ca182',
          500: '#4e8567',
          600: '#3a684f',
          700: '#2b4f3c',
          800: '#1f362a',
          900: '#14251c'
        },
        amber: {
          50: '#fff6e6',
          100: '#ffe7c2',
          200: '#ffd18f',
          300: '#fcb85d',
          400: '#f39c3d',
          500: '#e37c20',
          600: '#c25f15',
          700: '#9a4615',
          800: '#6f3214',
          900: '#45200d'
        },
        rose: {
          50: '#fff3f5',
          100: '#ffe0e7',
          200: '#ffc0cf',
          300: '#ff95b1',
          400: '#ff648f',
          500: '#f83c6e',
          600: '#d91f55',
          700: '#b01644',
          800: '#7f1234',
          900: '#4d0c22'
        }
      }
    }
  },
  plugins: []
};

export default config;
