import { app } from 'electron'
import path from 'node:path'

const electronRoot = path.resolve(import.meta.dirname, '..')
const appRoot = path.resolve(electronRoot, '..')
const distDir = path.join(appRoot, 'dist')
const devServerUrl = 'http://localhost:5175'
const isDev = !app.isPackaged
const preloadPath = path.join(electronRoot, 'preload.mjs')

function resolveRendererUrl(relativePath = '/') {
  if (isDev) {
    return new URL(relativePath, `${devServerUrl}/`).toString()
  }

  return path.join(distDir, relativePath === '/' ? 'index.html' : relativePath)
}

async function loadWindow(window, relativePath = '/') {
  if (isDev) {
    await window.loadURL(resolveRendererUrl(relativePath))
    return
  }

  await window.loadFile(resolveRendererUrl(relativePath))
}

export {
  appRoot,
  devServerUrl,
  distDir,
  isDev,
  loadWindow,
  preloadPath,
  resolveRendererUrl,
}
