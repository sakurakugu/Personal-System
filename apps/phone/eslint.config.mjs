import { 创建VueTsEslint配置 } from '../../configs/eslint.shared.mjs'

export default 创建VueTsEslint配置({
  ignores: ['android/**', 'dist/**', 'node_modules/**'],
  globals: {
    console: 'readonly',
    document: 'readonly',
    localStorage: 'readonly',
    window: 'readonly'
  }
})
