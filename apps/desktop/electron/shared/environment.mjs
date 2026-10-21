import { app } from 'electron'
import path from 'node:path'

const electronRoot = path.resolve(import.meta.dirname, '..')
const appRoot = path.resolve(electronRoot, '..')
const distDir = path.join(appRoot, 'dist')
const devServerUrl = 'http://localhost:5175'
const isDev = !app.isPackaged
const preloadPath = path.join(electronRoot, 'preload.mjs')

/** 开发环境网页后台地址。 */
const DEV_WEB_CONSOLE_URL = 'http://localhost:5173/dashboard'

/** 打包后网页后台地址（裸域会 301 到 www，直接使用 www 地址）。 */
const PRODUCTION_WEB_CONSOLE_URL = 'https://www.sakurakugu.com/dashboard'

/**
 * 获取网页后台地址：开发环境指向本地 5173，打包后指向线上地址。
 * 地址只在主进程维护，渲染层通过 IPC 打开，避免在多处硬编码。
 * @returns {string}
 */
function getWebConsoleUrl() {
  return isDev ? DEV_WEB_CONSOLE_URL : PRODUCTION_WEB_CONSOLE_URL
}

function resolveRendererUrl(relativePath = '/') {
  if (isDev) {
    return new URL(relativePath, `${devServerUrl}/`).toString()
  }

  return path.join(distDir, relativePath === '/' ? 'widget.html' : relativePath)
}

async function loadWindow(window, relativePath = '/widget.html') {
  if (isDev) {
    await window.loadURL(resolveRendererUrl(relativePath))
    return
  }

  await window.loadFile(resolveRendererUrl(relativePath))
}

export {
  DEV_WEB_CONSOLE_URL,
  PRODUCTION_WEB_CONSOLE_URL,
  appRoot,
  devServerUrl,
  distDir,
  getWebConsoleUrl,
  isDev,
  loadWindow,
  preloadPath,
  resolveRendererUrl,
}
