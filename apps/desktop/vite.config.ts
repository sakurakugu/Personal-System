import fs from 'node:fs'
import path from 'node:path'
import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

const localNodeModules = path.resolve(__dirname, './node_modules')
const workspaceNodeModules = path.resolve(__dirname, '../../node_modules')

function resolveNodeModulePath(...segments: string[]) {
  const localPath = path.resolve(localNodeModules, ...segments)
  if (fs.existsSync(localPath)) {
    return localPath
  }

  return path.resolve(workspaceNodeModules, ...segments)
}

function resolveNodeModuleDir(...segments: string[]) {
  return `${resolveNodeModulePath(...segments).replace(/\\/g, '/')}/`
}

export default defineConfig({
  resolve: {
    alias: [
      { find: '@', replacement: path.resolve(__dirname, './src') },
      { find: /^@capacitor\/core$/, replacement: resolveNodeModulePath('@capacitor', 'core', 'dist', 'index.js') },
      { find: /^@element-plus\/icons-vue$/, replacement: resolveNodeModulePath('@element-plus', 'icons-vue', 'dist', 'index.js') },
      { find: /^@fancyapps\/ui$/, replacement: resolveNodeModulePath('@fancyapps', 'ui', 'dist', 'index.js') },
      { find: '@fancyapps/ui/', replacement: resolveNodeModuleDir('@fancyapps', 'ui') },
      { find: /^@iconify\/vue$/, replacement: resolveNodeModulePath('@iconify', 'vue', 'dist', 'iconify.js') },
      { find: '@codemirror/', replacement: resolveNodeModuleDir('@codemirror') },
      { find: '@personal-system/app-core', replacement: path.resolve(__dirname, '../../packages/app-core/src/index.ts') },
      { find: '@personal-system/api', replacement: path.resolve(__dirname, '../../packages/api/src/index.ts') },
      { find: '@personal-system/domain/auth', replacement: path.resolve(__dirname, '../../packages/domain/src/auth/index.ts') },
      { find: '@personal-system/domain/system', replacement: path.resolve(__dirname, '../../packages/domain/src/system/index.ts') },
      { find: '@personal-system/domain/todos', replacement: path.resolve(__dirname, '../../packages/domain/src/todos/index.ts') },
      { find: '@personal-system/modules/articles', replacement: path.resolve(__dirname, '../../packages/modules/articles/src/index.ts') },
      { find: '@personal-system/modules/auth', replacement: path.resolve(__dirname, '../../packages/modules/auth/src/index.ts') },
      { find: '@personal-system/modules/bills', replacement: path.resolve(__dirname, '../../packages/modules/bills/src/index.ts') },
      { find: '@personal-system/modules/moments', replacement: path.resolve(__dirname, '../../packages/modules/moments/src/index.ts') },
      { find: '@personal-system/modules/profile', replacement: path.resolve(__dirname, '../../packages/modules/profile/src/index.ts') },
      { find: '@personal-system/modules/tools', replacement: path.resolve(__dirname, '../../packages/modules/tools/src/index.ts') },
      { find: '@personal-system/modules/todos', replacement: path.resolve(__dirname, '../../packages/modules/todos/src/index.ts') },
      { find: '@personal-system/theme', replacement: path.resolve(__dirname, '../../packages/theme/src') },
      { find: '@personal-system/ui', replacement: path.resolve(__dirname, '../../packages/ui/src') },
      { find: '@vscode/markdown-it-katex', replacement: resolveNodeModulePath('@vscode', 'markdown-it-katex') },
      { find: /^element-plus$/, replacement: resolveNodeModulePath('element-plus', 'es', 'index.mjs') },
      { find: /^axios$/, replacement: resolveNodeModulePath('axios', 'index.js') },
      { find: 'highlight.js/', replacement: resolveNodeModuleDir('highlight.js') },
      { find: /^highlight\.js$/, replacement: resolveNodeModulePath('highlight.js') },
      { find: /^katex$/, replacement: resolveNodeModulePath('katex') },
      { find: 'katex/', replacement: resolveNodeModuleDir('katex') },
      { find: /^markdown-it$/, replacement: resolveNodeModulePath('markdown-it') },
      { find: /^markdown-it-abbr$/, replacement: resolveNodeModulePath('markdown-it-abbr') },
      { find: /^markdown-it-emoji$/, replacement: resolveNodeModulePath('markdown-it-emoji') },
      { find: /^markdown-it-footnote$/, replacement: resolveNodeModulePath('markdown-it-footnote') },
      { find: /^markdown-it-mark$/, replacement: resolveNodeModulePath('markdown-it-mark') },
      { find: /^markdown-it-task-lists$/, replacement: resolveNodeModulePath('markdown-it-task-lists') },
      { find: /^markmap-lib$/, replacement: resolveNodeModulePath('markmap-lib') },
      { find: /^markmap-view$/, replacement: resolveNodeModulePath('markmap-view') },
      { find: /^md-editor-v3$/, replacement: resolveNodeModulePath('md-editor-v3') },
      { find: 'md-editor-v3/', replacement: resolveNodeModuleDir('md-editor-v3') },
      { find: /^pinia$/, replacement: resolveNodeModulePath('pinia', 'dist', 'pinia.mjs') },
      { find: /^vue$/, replacement: resolveNodeModulePath('vue', 'dist', 'vue.runtime.esm-bundler.js') },
      { find: /^vue-router$/, replacement: resolveNodeModulePath('vue-router', 'dist', 'vue-router.esm-bundler.js') },
    ],
  },
  plugins: [vue()],
  server: {
    fs: {
      allow: [
        path.resolve(__dirname, '../..'),
      ],
    },
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/files': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
