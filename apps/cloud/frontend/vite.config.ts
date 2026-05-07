import path from 'node:path'
import vue from '@vitejs/plugin-vue'
import postcssCustomMedia from 'postcss-custom-media'
import { defineConfig } from 'vite'

//
function getPathSegment(id: string, marker: string) {
  const normalizedId = id.replace(/\\/g, '/')
  const markerIndex = normalizedId.indexOf(marker)
  if (markerIndex === -1) {
    return null
  }

  const remainingPath = normalizedId.slice(markerIndex + marker.length)
  const [segment] = remainingPath.split('/')
  return segment || null
}

function getNodeModulePackageName(id: string) {
  const normalizedId = id.replace(/\\/g, '/')
  const marker = '/node_modules/'
  const markerIndex = normalizedId.indexOf(marker)
  if (markerIndex === -1) {
    return null
  }

  const remainingPath = normalizedId.slice(markerIndex + marker.length)
  const segments = remainingPath.split('/')
  if (!segments[0]) {
    return null
  }

  if (segments[0].startsWith('@') && segments[1]) {
    return `${segments[0]}/${segments[1]}`
  }

  return segments[0]
}

function resolveManualChunk(id: string) {
  const normalizedId = id.replace(/\\/g, '/')

  if (!normalizedId.includes('/node_modules/')) {
    return undefined
  }

  if (normalizedId.includes('/node_modules/@element-plus/icons-vue/')) {
    return 'element-plus-icons'
  }

  if (normalizedId.includes('/node_modules/element-plus/')) {
    const componentName = getPathSegment(normalizedId, '/node_modules/element-plus/es/components/')
    if (componentName) {
      return `element-plus-${componentName}`
    }

    const packagePart = getPathSegment(normalizedId, '/node_modules/element-plus/es/')
    if (packagePart && packagePart !== '_virtual') {
      return `element-plus-${packagePart}`
    }

    return 'element-plus-core'
  }

  if (normalizedId.includes('/node_modules/vue-echarts/')) {
    return 'vue-echarts'
  }

  if (normalizedId.includes('/node_modules/zrender/')) {
    return 'zrender'
  }

  if (normalizedId.includes('/node_modules/echarts/')) {
    const echartsEntry = getPathSegment(normalizedId, '/node_modules/echarts/')
    if (echartsEntry && ['charts.js', 'components.js', 'core.js', 'features.js', 'renderers.js'].includes(echartsEntry)) {
      return `echarts-${echartsEntry.replace('.js', '')}`
    }

    const echartsLibPart = getPathSegment(normalizedId, '/node_modules/echarts/lib/')
    if (echartsLibPart) {
      return `echarts-${echartsLibPart}`
    }

    return 'echarts-core'
  }

  if (normalizedId.includes('/node_modules/highlight.js/')) {
    return 'highlightjs'
  }

  if (normalizedId.includes('/node_modules/markdown-it/')) {
    return 'markdown-it'
  }

  const packageName = getNodeModulePackageName(normalizedId)
  if (packageName?.startsWith('markmap')) {
    return packageName
  }

  if (packageName?.startsWith('d3-')) {
    return packageName
  }

  return undefined
}

//
export default defineConfig({
  resolve: {
    alias: [
      { find: '@', replacement: path.resolve(__dirname, './src') },
      { find: '@capacitor/core', replacement: path.resolve(__dirname, './node_modules/@capacitor/core/dist/index.js') },
      { find: '@element-plus/icons-vue', replacement: path.resolve(__dirname, './node_modules/@element-plus/icons-vue/dist/index.js') },
      { find: /^@fancyapps\/ui$/, replacement: path.resolve(__dirname, './node_modules/@fancyapps/ui/dist/index.js') },
      { find: '@fancyapps/ui/', replacement: `${path.resolve(__dirname, './node_modules/@fancyapps/ui').replace(/\\/g, '/')}/` },
      { find: '@personal-system/app-core', replacement: path.resolve(__dirname, '../../../packages/app-core/src/index.ts') },
      { find: '@personal-system/api', replacement: path.resolve(__dirname, '../../../packages/api/src/index.ts') },
      { find: '@personal-system/domain/auth', replacement: path.resolve(__dirname, '../../../packages/domain/src/auth/index.ts') },
      { find: '@personal-system/domain/system', replacement: path.resolve(__dirname, '../../../packages/domain/src/system/index.ts') },
      { find: '@personal-system/domain/todos', replacement: path.resolve(__dirname, '../../../packages/domain/src/todos/index.ts') },
      { find: '@personal-system/modules/auth', replacement: path.resolve(__dirname, '../../../packages/modules/auth/src/index.ts') },
      { find: '@personal-system/modules/bills', replacement: path.resolve(__dirname, '../../../packages/modules/bills/src/index.ts') },
      { find: '@personal-system/modules/profile', replacement: path.resolve(__dirname, '../../../packages/modules/profile/src/index.ts') },
      { find: '@personal-system/modules/tools', replacement: path.resolve(__dirname, '../../../packages/modules/tools/src/index.ts') },
      { find: '@personal-system/modules/todos', replacement: path.resolve(__dirname, '../../../packages/modules/todos/src/index.ts') },
      { find: '@personal-system/theme', replacement: path.resolve(__dirname, '../../../packages/theme/src') },
      { find: '@personal-system/ui', replacement: path.resolve(__dirname, '../../../packages/ui/src') },
      { find: /^element-plus$/, replacement: path.resolve(__dirname, './node_modules/element-plus/es/index.mjs') },
      { find: 'axios', replacement: path.resolve(__dirname, './node_modules/axios/index.js') },
      { find: 'pinia', replacement: path.resolve(__dirname, './node_modules/pinia/dist/pinia.mjs') },
      { find: 'reading-time', replacement: path.resolve(__dirname, './node_modules/reading-time/lib/reading-time.js') },
      { find: 'vue', replacement: path.resolve(__dirname, './node_modules/vue/dist/vue.runtime.esm-bundler.js') },
      { find: 'vue-router', replacement: path.resolve(__dirname, './node_modules/vue-router/dist/vue-router.esm-bundler.js') },
    ],
  },
  plugins: [vue()],
  optimizeDeps: {
    include: ['reading-time'],
  },
  css: {
    postcss: {
      plugins: [
        postcssCustomMedia(),
      ],
    },
  },
  server: {
    fs: {
      allow: [
        path.resolve(__dirname, '../../..'),
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
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          return resolveManualChunk(id)
        },
      },
    },
  },
})
