import { invoke } from '@tauri-apps/api/core'
import { isTauri } from '@tauri-apps/api/core'

const DESKTOP_AUTH_TOKEN_STORAGE_KEY = 'desktop-auth-token'

let cachedDesktopAuthToken: string | null = null
let desktopAuthTokenInitTask: Promise<void> | null = null

function normalizeToken(token: string | null | undefined): string | null {
  const normalizedToken = token?.trim()
  return normalizedToken ? normalizedToken : null
}

function readBrowserToken(): string | null {
  if (typeof localStorage === 'undefined') {
    return null
  }
  return normalizeToken(localStorage.getItem(DESKTOP_AUTH_TOKEN_STORAGE_KEY))
}

function writeBrowserToken(token: string | null): void {
  if (typeof localStorage === 'undefined') {
    return
  }
  if (!token) {
    localStorage.removeItem(DESKTOP_AUTH_TOKEN_STORAGE_KEY)
    return
  }
  localStorage.setItem(DESKTOP_AUTH_TOKEN_STORAGE_KEY, token)
}

export function getStoredDesktopAuthToken(): string | null {
  return cachedDesktopAuthToken
}

export function initializeDesktopAuthTokenStorage(): Promise<void> {
  if (desktopAuthTokenInitTask) {
    return desktopAuthTokenInitTask
  }

  desktopAuthTokenInitTask = (async () => {
    if (!isTauri()) {
      cachedDesktopAuthToken = readBrowserToken()
      return
    }
    const storedToken = await invoke<string | null>('load_desktop_auth_token')
    cachedDesktopAuthToken = normalizeToken(storedToken)
  })()

  return desktopAuthTokenInitTask
}

export async function setStoredDesktopAuthToken(token: string | null): Promise<void> {
  const normalizedToken = normalizeToken(token)
  cachedDesktopAuthToken = normalizedToken
  if (!isTauri()) {
    writeBrowserToken(normalizedToken)
    return
  }
  await invoke('save_desktop_auth_token', { token: normalizedToken })
}
