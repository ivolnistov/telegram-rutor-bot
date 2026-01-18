import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import tseslint from 'typescript-eslint'
import betterTailwindcss from 'eslint-plugin-better-tailwindcss'
import importPlugin from 'eslint-plugin-import'
import { defineConfig, globalIgnores } from 'eslint/config'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      js.configs.recommended,
      tseslint.configs.strictTypeChecked,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
      parserOptions: {
        projectService: true,
        tsconfigRootDir: import.meta.dirname,
      },
    },
    plugins: {
      'better-tailwindcss': betterTailwindcss,
      import: importPlugin,
    },
    rules: {
      // Enforce arrow functions for consistency
      'func-style': ['error', 'expression'],
      '@typescript-eslint/no-floating-promises': 'error',
      '@typescript-eslint/only-throw-error': 'error',
      'better-tailwindcss/enforce-consistent-important-position': ['error', { position: 'recommended' }],
      'better-tailwindcss/enforce-consistent-variable-syntax': 'error',
      'better-tailwindcss/enforce-shorthand-classes': 'error',
      'better-tailwindcss/no-deprecated-classes': 'error',
      'import/no-useless-path-segments': ['error', { noUselessIndex: true }],
      'no-restricted-imports': [
        'warn',
        {
          patterns: [
            {
              group: ['../*'],
              message: 'Use path alias instead of relative imports',
            },
            {
              group: ['**/index'],
              message: 'Import can be shortened by removing /index',
            },
          ],
        },
      ],
    },
  },
])
