import { LazyStore } from '@tauri-apps/plugin-store'

const DESKTOP_AUTH_STORE_PATH = 'auth.store.json'
const DESKTOP_AUTH_TOKEN_STORAGE_KEY = 'desktop-auth-token'

const desktopAuthStore = new LazyStore(DESKTOP_AUTH_STORE_PATH)

let cachedDesktopAuthToken: string | null = null
let desktopAuthTokenInitTask: Promise<void> | null = null

export function getStoredDesktopAuthToken(): string | null {
  return cachedDesktopAuthToken
}

export function initializeDesktopAuthTokenStorage(): Promise<void> {
  if (desktopAuthTokenInitTask) {
    return desktopAuthTokenInitTask
  }

  desktopAuthTokenInitTask = (async () => {
    const storedToken = await desktopAuthStore.get<string>(DESKTOP_AUTH_TOKEN_STORAGE_KEY)
    cachedDesktopAuthToken = storedToken && storedToken.trim() ? storedToken : null
  })()

  return desktopAuthTokenInitTask
}

export async function setStoredDesktopAuthToken(token: string | null): Promise<void> {
  const normalizedToken = token && token.trim() ? token : null
  cachedDesktopAuthToken = normalizedToken
  if (!normalizedToken) {
    await desktopAuthStore.delete(DESKTOP_AUTH_TOKEN_STORAGE_KEY)
    return
  }
  await desktopAuthStore.set(DESKTOP_AUTH_TOKEN_STORAGE_KEY, normalizedToken)
}
