import { 创建VueTsEslint配置 } from '../../configs/eslint.shared.mjs'

export default 创建VueTsEslint配置({
  ignores: ['dist/**', 'node_modules/**', 'build/**', 'python/**', 'python-runtime/**'],
  files: ['**/*.{ts,tsx,vue,mjs}'],
  globals: {
    __dirname: 'readonly',
    console: 'readonly',
    document: 'readonly',
    fetch: 'readonly',
    globalThis: 'readonly',
    localStorage: 'readonly',
    process: 'readonly',
    navigator: 'readonly',
    URL: 'readonly',
    window: 'readonly'
  }
})
