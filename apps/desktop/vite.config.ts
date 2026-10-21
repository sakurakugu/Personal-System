import path from 'node:path'
import vue from '@vitejs/plugin-vue'
import UnoCSS from 'unocss/vite'
import { defineConfig } from 'vite'
import unoConfig from '../../configs/uno.config'
import { createFrontendAliasEntries, createFrontendServerConfig } from '../../configs/frontend/vite-shared'

export default defineConfig({
  base: './',
  resolve: {
    alias: createFrontendAliasEntries({
      appDir: __dirname,
    }),
  },
  plugins: [vue(), UnoCSS(unoConfig)],
  build: {
    // 桌面端只打包小工具页面，输出 dist/widget.html 供 file:// 加载。
    rollupOptions: {
      input: {
        widget: path.resolve(__dirname, 'widget.html'),
      },
    },
  },
  server: createFrontendServerConfig(path.resolve(__dirname, '../..')),
})
