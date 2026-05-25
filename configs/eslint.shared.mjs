import js from '@eslint/js'
import eslintConfigPrettier from 'eslint-config-prettier'
import vue from 'eslint-plugin-vue'
import tseslint from 'typescript-eslint'

const 共享规则 = {
  '@typescript-eslint/no-explicit-any': 'off',
  '@typescript-eslint/no-unused-vars': 'off',
  'vue/max-attributes-per-line': 'off',
  'vue/singleline-html-element-content-newline': 'off',
  'vue/multi-word-component-names': 'off'
}

export function 创建VueTsEslint配置({
  ignores = [],
  files = ['**/*.{ts,tsx,vue}'],
  globals = {},
  parserOptions = {},
  rules = {}
} = {}) {
  const languageOptions = {
    parserOptions: {
      parser: tseslint.parser,
      sourceType: 'module',
      ...parserOptions
    }
  }

  if (Object.keys(globals).length > 0) {
    languageOptions.globals = globals
  }

  return [
    {
      ignores
    },
    js.configs.recommended,
    ...tseslint.configs.recommended,
    ...vue.configs['flat/recommended'],
    {
      files,
      languageOptions,
      rules: {
        ...共享规则,
        ...rules
      }
    },
    eslintConfigPrettier
  ]
}
