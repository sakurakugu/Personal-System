const DESKTOP_AUTH_TOKEN_STORAGE_KEY = 'desktop-auth-token'

export function getStoredDesktopAuthToken(): string | null {
  return localStorage.getItem(DESKTOP_AUTH_TOKEN_STORAGE_KEY)
}

export function setStoredDesktopAuthToken(token: string | null): void {
  if (!token) {
    localStorage.removeItem(DESKTOP_AUTH_TOKEN_STORAGE_KEY)
    return
  }
  localStorage.setItem(DESKTOP_AUTH_TOKEN_STORAGE_KEY, token)
}
