import { 创建VueTsEslint配置 } from '../../../configs/eslint.shared.mjs'

export default 创建VueTsEslint配置({
  ignores: ['dist', 'node_modules', 'android', 'scripts'],
  globals: {
    window: 'readonly',
    document: 'readonly',
    navigator: 'readonly',
    FormData: 'readonly',
    localStorage: 'readonly',
    CustomEvent: 'readonly',
    console: 'readonly',
    setTimeout: 'readonly',
    confirm: 'readonly'
  },
  rules: {
    'no-empty': 'off',
    'vue/no-v-html': 'off'
  }
})
