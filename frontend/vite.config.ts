import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import postcssCustomMedia from 'postcss-custom-media'

export default defineConfig({
  plugins: [vue()],
  css: {
    postcss: {
      plugins: [
        postcssCustomMedia(),
      ],
    },
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('element-plus') || id.includes('@element-plus/icons-vue')) return 'element-plus'
          if (id.includes('echarts') || id.includes('vue-echarts')) return 'echarts'
          if (id.includes('highlight.js') || id.includes('markdown-it')) return 'highlight'
        },
      },
    },
  },
})
