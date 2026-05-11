import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import tseslint from 'typescript-eslint'
import { defineConfig, globalIgnores } from 'eslint/config'

import requireFontArabic from './eslint-rules/require-font-arabic.js'

// Local plugin namespace holding repo-specific rules. Adding the
// inline plugin object here (instead of publishing as a package)
// keeps the rule co-located with the code it guards.
const quranLocal = {
  rules: {
    'require-font-arabic': requireFontArabic,
  },
}

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    plugins: {
      'quran-local': quranLocal,
    },
    extends: [
      js.configs.recommended,
      tseslint.configs.recommended,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
    },
    rules: {
      // Religious-text safety net: every JSX element marked as
      // Arabic content (lang="ar" or dir="rtl") MUST carry the
      // font-arabic Tailwind class so Uthmani diacritics render
      // correctly. The rule walks className expressions (including
      // template literals and conditionals) and conservatively
      // skips truly dynamic className values. Wrapper elements
      // whose children handle the font can opt out with
      // `data-allow-no-font-arabic`.
      'quran-local/require-font-arabic': 'error',
    },
  },
])
