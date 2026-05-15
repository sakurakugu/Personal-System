import { getDesktopRuntime, isElectronDesktop } from '../desktop-runtime'

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
    if (isElectronDesktop()) {
      const storedToken = await getDesktopRuntime()?.loadDesktopAuthToken()
      cachedDesktopAuthToken = normalizeToken(storedToken)
      return
    }
    cachedDesktopAuthToken = readBrowserToken()
  })()

  return desktopAuthTokenInitTask
}

export async function setStoredDesktopAuthToken(token: string | null): Promise<void> {
  const normalizedToken = normalizeToken(token)
  cachedDesktopAuthToken = normalizedToken
  if (isElectronDesktop()) {
    await getDesktopRuntime()?.saveDesktopAuthToken(normalizedToken)
    return
  }
  writeBrowserToken(normalizedToken)
}
