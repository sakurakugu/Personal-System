import path from 'node:path'
import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

export default defineConfig({
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@capacitor/core': path.resolve(__dirname, './node_modules/@capacitor/core/dist/index.js'),
      '@personal-system/api': path.resolve(__dirname, '../../packages/api/src/index.ts'),
      '@personal-system/domain/auth': path.resolve(__dirname, '../../packages/domain/src/auth/index.ts'),
      '@personal-system/domain/system': path.resolve(__dirname, '../../packages/domain/src/system/index.ts'),
      '@personal-system/domain/todos': path.resolve(__dirname, '../../packages/domain/src/todos/index.ts'),
      '@personal-system/theme': path.resolve(__dirname, '../../packages/theme/src/index.ts'),
      '@personal-system/ui': path.resolve(__dirname, '../../packages/ui/src/index.ts'),
      'axios': path.resolve(__dirname, './node_modules/axios/index.js'),
      'pinia': path.resolve(__dirname, './node_modules/pinia/dist/pinia.mjs'),
      'vue': path.resolve(__dirname, './node_modules/vue/dist/vue.runtime.esm-bundler.js'),
    },
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
