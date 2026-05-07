import path from 'node:path'
import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

export default defineConfig({
  resolve: {
    alias: [
      { find: '@', replacement: path.resolve(__dirname, './src') },
      { find: '@capacitor/core', replacement: path.resolve(__dirname, './node_modules/@capacitor/core/dist/index.js') },
      { find: '@element-plus/icons-vue', replacement: path.resolve(__dirname, './node_modules/@element-plus/icons-vue/dist/index.js') },
      { find: /^@fancyapps\/ui$/, replacement: path.resolve(__dirname, './node_modules/@fancyapps/ui/dist/index.js') },
      { find: '@fancyapps/ui/', replacement: `${path.resolve(__dirname, './node_modules/@fancyapps/ui').replace(/\\/g, '/')}/` },
      { find: '@iconify/vue', replacement: path.resolve(__dirname, './node_modules/@iconify/vue/dist/iconify.js') },
      { find: '@personal-system/app-core', replacement: path.resolve(__dirname, '../../packages/app-core/src/index.ts') },
      { find: '@personal-system/api', replacement: path.resolve(__dirname, '../../packages/api/src/index.ts') },
      { find: '@personal-system/domain/auth', replacement: path.resolve(__dirname, '../../packages/domain/src/auth/index.ts') },
      { find: '@personal-system/domain/system', replacement: path.resolve(__dirname, '../../packages/domain/src/system/index.ts') },
      { find: '@personal-system/domain/todos', replacement: path.resolve(__dirname, '../../packages/domain/src/todos/index.ts') },
      { find: '@personal-system/modules/auth', replacement: path.resolve(__dirname, '../../packages/modules/auth/src/index.ts') },
      { find: '@personal-system/modules/bills', replacement: path.resolve(__dirname, '../../packages/modules/bills/src/index.ts') },
      { find: '@personal-system/modules/moments', replacement: path.resolve(__dirname, '../../packages/modules/moments/src/index.ts') },
      { find: '@personal-system/modules/profile', replacement: path.resolve(__dirname, '../../packages/modules/profile/src/index.ts') },
      { find: '@personal-system/modules/tools', replacement: path.resolve(__dirname, '../../packages/modules/tools/src/index.ts') },
      { find: '@personal-system/modules/todos', replacement: path.resolve(__dirname, '../../packages/modules/todos/src/index.ts') },
      { find: '@personal-system/theme', replacement: path.resolve(__dirname, '../../packages/theme/src') },
      { find: '@personal-system/ui', replacement: path.resolve(__dirname, '../../packages/ui/src') },
      { find: /^element-plus$/, replacement: path.resolve(__dirname, './node_modules/element-plus/es/index.mjs') },
      { find: 'axios', replacement: path.resolve(__dirname, './node_modules/axios/index.js') },
      { find: 'pinia', replacement: path.resolve(__dirname, './node_modules/pinia/dist/pinia.mjs') },
      { find: 'vue', replacement: path.resolve(__dirname, './node_modules/vue/dist/vue.runtime.esm-bundler.js') },
      { find: 'vue-router', replacement: path.resolve(__dirname, './node_modules/vue-router/dist/vue-router.esm-bundler.js') },
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
