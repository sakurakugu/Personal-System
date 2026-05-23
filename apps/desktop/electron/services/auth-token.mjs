import { app } from 'electron'
import fs from 'node:fs/promises'
import path from 'node:path'

function getDesktopAuthTokenPath() {
  return path.join(app.getPath('userData'), 'desktop-auth-token.txt')
}

function getWidgetConfigPath() {
  return path.join(app.getPath('userData'), 'desktop-widget', 'config.json')
}

function normalizeToken(token) {
  const normalized = token?.trim()
  return normalized ? normalized : null
}

async function loadDesktopAuthToken() {
  try {
    const content = await fs.readFile(getDesktopAuthTokenPath(), 'utf8')
    return normalizeToken(content)
  } catch (error) {
    if (error && typeof error === 'object' && 'code' in error && error.code === 'ENOENT') {
      return null
    }

    throw error
  }
}

async function saveDesktopAuthToken(token) {
  const normalized = normalizeToken(token)
  const tokenPath = getDesktopAuthTokenPath()

  if (!normalized) {
    try {
      await fs.unlink(tokenPath)
    } catch (error) {
      if (!(error && typeof error === 'object' && 'code' in error && error.code === 'ENOENT')) {
        throw error
      }
    }
    return
  }

  await fs.mkdir(path.dirname(tokenPath), { recursive: true })
  await fs.writeFile(tokenPath, `${normalized}\n`, 'utf8')
}

async function syncWidgetAuthToken(payload) {
  const normalizedToken = normalizeToken(payload.token)
  if (!normalizedToken) {
    throw new Error('小工具凭证不能为空')
  }

  const normalizedApiBaseUrl = payload.apiBaseUrl?.trim().replace(/\/+$/, '') || 'http://127.0.0.1:8000/api/v1'
  const normalizedWidgetName = payload.widgetName?.trim() || 'Personal System Widget'
  const configPath = getWidgetConfigPath()

  await fs.mkdir(path.dirname(configPath), { recursive: true })
  await fs.writeFile(configPath, `${JSON.stringify({
    api_base_url: normalizedApiBaseUrl,
    widget_name: normalizedWidgetName,
    token: normalizedToken,
  }, null, 2)}\n`, 'utf8')

  return configPath
}

export {
  loadDesktopAuthToken,
  saveDesktopAuthToken,
  syncWidgetAuthToken,
}
