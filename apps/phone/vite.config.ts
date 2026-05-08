import path from 'node:path'
import vue from '@vitejs/plugin-vue'
import postcssCustomMedia from 'postcss-custom-media'
import { defineConfig } from 'vite'

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

  if (normalizedId.includes('/node_modules/@iconify/')) {
    return 'iconify'
  }

  if (normalizedId.includes('/node_modules/@fancyapps/')) {
    return 'fancyapps'
  }

  if (normalizedId.includes('/node_modules/@capacitor/')) {
    return 'capacitor'
  }

  const packageName = getNodeModulePackageName(normalizedId)
  if (packageName) {
    return `vendor-${packageName.replace('/', '-')}`
  }

  return undefined
}

export default defineConfig({
  resolve: {
    alias: [
      { find: '@', replacement: path.resolve(__dirname, './src') },
      { find: '@capacitor/core', replacement: path.resolve(__dirname, './node_modules/@capacitor/core/dist/index.js') },
      { find: '@element-plus/icons-vue', replacement: path.resolve(__dirname, './node_modules/@element-plus/icons-vue/dist/index.js') },
      { find: /^@fancyapps\/ui$/, replacement: path.resolve(__dirname, './node_modules/@fancyapps/ui/dist/index.js') },
      { find: '@fancyapps/ui/', replacement: `${path.resolve(__dirname, './node_modules/@fancyapps/ui').replace(/\\/g, '/')}/` },
      { find: '@iconify/vue', replacement: path.resolve(__dirname, './node_modules/@iconify/vue/dist/iconify.js') },
      { find: /^element-plus$/, replacement: path.resolve(__dirname, './node_modules/element-plus/es/index.mjs') },
      { find: 'axios', replacement: path.resolve(__dirname, './node_modules/axios/index.js') },
      { find: 'pinia', replacement: path.resolve(__dirname, './node_modules/pinia/dist/pinia.mjs') },
      { find: 'vue', replacement: path.resolve(__dirname, './node_modules/vue/dist/vue.runtime.esm-bundler.js') },
      { find: 'vue-router', replacement: path.resolve(__dirname, './node_modules/vue-router/dist/vue-router.esm-bundler.js') },
    ],
  },
  plugins: [vue()],
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
