import path from 'node:path'
import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'
import { createFrontendAliasEntries, createFrontendServerConfig } from '../../configs/frontend/vite-shared'

export default defineConfig({
  resolve: {
    alias: createFrontendAliasEntries({
      appDir: __dirname,
    }),
  },
  plugins: [vue()],
  server: createFrontendServerConfig(path.resolve(__dirname, '../..')),
})
