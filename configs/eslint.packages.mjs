import { 创建VueTsEslint配置 } from './eslint.shared.mjs'

export default 创建VueTsEslint配置({
  ignores: ['packages/**/dist/**', 'packages/**/node_modules/**'],
  files: ['packages/**/*.{ts,tsx,vue,d.ts}'],
  parserOptions: {
    ecmaVersion: 'latest'
  },
  rules: {
    'no-undef': 'off',
    'no-empty': 'off',
    'vue/no-mutating-props': 'off',
    'vue/no-v-html': 'off',
    'vue/attributes-order': 'off'
  }
})
