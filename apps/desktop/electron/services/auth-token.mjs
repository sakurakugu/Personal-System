import { app } from 'electron'
import fs from 'node:fs/promises'
import path from 'node:path'

function getDesktopAuthTokenPath() {
  return path.join(app.getPath('userData'), 'desktop-auth-token.txt')
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

export {
  loadDesktopAuthToken,
  saveDesktopAuthToken,
}
