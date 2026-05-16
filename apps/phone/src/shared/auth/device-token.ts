import { Capacitor } from '@capacitor/core'
import { SecureStorage } from '@aparajita/capacitor-secure-storage'

const PHONE_AUTH_TOKEN_STORAGE_KEY = 'personal-system:phone-auth-token'

let cachedPhoneAuthToken: string | null = null
let phoneAuthTokenInitialized = false

function 标准化令牌(token: string | null | undefined): string | null {
  const normalized = token?.trim()
  return normalized ? normalized : null
}

function 原生手机存储是否可用(): boolean {
  return Capacitor.isNativePlatform()
}

async function 从安全存储获取令牌(): Promise<string | null> {
  const storedToken = await SecureStorage.getItem(PHONE_AUTH_TOKEN_STORAGE_KEY)
  return 标准化令牌(storedToken)
}

async function 移除遗留本地存储令牌(): Promise<void> {
  localStorage.removeItem(PHONE_AUTH_TOKEN_STORAGE_KEY)
}

async function 从本地存储初始化(): Promise<void> {
  cachedPhoneAuthToken = 标准化令牌(localStorage.getItem(PHONE_AUTH_TOKEN_STORAGE_KEY))
}

async function 从安全存储初始化(): Promise<void> {
  const secureToken = await 从安全存储获取令牌()
  cachedPhoneAuthToken = secureToken
  await 移除遗留本地存储令牌()
}

export function 获取存储的手机令牌(): string | null {
  return cachedPhoneAuthToken
}

export async function 初始化手机令牌存储(): Promise<void> {
  if (phoneAuthTokenInitialized) {
    return
  }
  phoneAuthTokenInitialized = true

  if (!原生手机存储是否可用()) {
    await 从本地存储初始化()
    return
  }

  await 从安全存储初始化()
}

export async function 设置存储的手机令牌(token: string | null): Promise<void> {
  const normalizedToken = 标准化令牌(token)
  cachedPhoneAuthToken = normalizedToken

  if (!原生手机存储是否可用()) {
    if (!normalizedToken) {
      localStorage.removeItem(PHONE_AUTH_TOKEN_STORAGE_KEY)
      return
    }
    localStorage.setItem(PHONE_AUTH_TOKEN_STORAGE_KEY, normalizedToken)
    return
  }

  if (!normalizedToken) {
    await SecureStorage.removeItem(PHONE_AUTH_TOKEN_STORAGE_KEY)
    await 移除遗留本地存储令牌()
    return
  }

  await SecureStorage.setItem(PHONE_AUTH_TOKEN_STORAGE_KEY, normalizedToken)
  await 移除遗留本地存储令牌()
}
