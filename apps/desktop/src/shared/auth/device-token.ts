import { 获取桌面运行时, 是否为Electron桌面 } from '../desktop-runtime'

const DESKTOP_AUTH_TOKEN_STORAGE_KEY = 'desktop-auth-token'

let cachedDesktopAuthToken: string | null = null
let desktopAuthTokenInitTask: Promise<void> | null = null

function 标准化令牌(token: string | null | undefined): string | null {
  const normalizedToken = token?.trim()
  return normalizedToken ? normalizedToken : null
}

function 读取浏览器令牌(): string | null {
  if (typeof localStorage === 'undefined') {
    return null
  }
  return 标准化令牌(localStorage.getItem(DESKTOP_AUTH_TOKEN_STORAGE_KEY))
}

function 写入浏览器令牌(token: string | null): void {
  if (typeof localStorage === 'undefined') {
    return
  }
  if (!token) {
    localStorage.removeItem(DESKTOP_AUTH_TOKEN_STORAGE_KEY)
    return
  }
  localStorage.setItem(DESKTOP_AUTH_TOKEN_STORAGE_KEY, token)
}

export function 获取存储的桌面令牌(): string | null {
  return cachedDesktopAuthToken
}

export function 初始化桌面令牌存储(): Promise<void> {
  if (desktopAuthTokenInitTask) {
    return desktopAuthTokenInitTask
  }

  desktopAuthTokenInitTask = (async () => {
    if (是否为Electron桌面()) {
      const storedToken = await 获取桌面运行时()?.loadDesktopAuthToken()
      cachedDesktopAuthToken = 标准化令牌(storedToken)
      return
    }
    cachedDesktopAuthToken = 读取浏览器令牌()
  })()

  return desktopAuthTokenInitTask
}

export async function 设置存储的桌面令牌(token: string | null): Promise<void> {
  const normalizedToken = 标准化令牌(token)
  cachedDesktopAuthToken = normalizedToken
  if (是否为Electron桌面()) {
    await 获取桌面运行时()?.saveDesktopAuthToken(normalizedToken)
    return
  }
  写入浏览器令牌(normalizedToken)
}
