import { Capacitor } from '@capacitor/core'
import { SecureStorage } from '@aparajita/capacitor-secure-storage'

const PHONE_AUTH_TOKEN_STORAGE_KEY = 'personal-system:phone-auth-token'

let cachedPhoneAuthToken: string | null = null
let phoneAuthTokenInitialized = false

function normalizeToken(token: string | null | undefined): string | null {
  const normalized = token?.trim()
  return normalized ? normalized : null
}

function isNativePhoneStorageAvailable(): boolean {
  return Capacitor.isNativePlatform()
}

async function getTokenFromSecureStorage(): Promise<string | null> {
  const storedToken = await SecureStorage.getItem(PHONE_AUTH_TOKEN_STORAGE_KEY)
  return normalizeToken(storedToken)
}

async function removeLegacyLocalStorageToken(): Promise<void> {
  localStorage.removeItem(PHONE_AUTH_TOKEN_STORAGE_KEY)
}

async function initializeFromLocalStorage(): Promise<void> {
  cachedPhoneAuthToken = normalizeToken(localStorage.getItem(PHONE_AUTH_TOKEN_STORAGE_KEY))
}

async function initializeFromSecureStorage(): Promise<void> {
  const secureToken = await getTokenFromSecureStorage()
  cachedPhoneAuthToken = secureToken
  await removeLegacyLocalStorageToken()
}

export function getStoredPhoneAuthToken(): string | null {
  return cachedPhoneAuthToken
}

export async function initializePhoneAuthTokenStorage(): Promise<void> {
  if (phoneAuthTokenInitialized) {
    return
  }
  phoneAuthTokenInitialized = true

  if (!isNativePhoneStorageAvailable()) {
    await initializeFromLocalStorage()
    return
  }

  await initializeFromSecureStorage()
}

export async function setStoredPhoneAuthToken(token: string | null): Promise<void> {
  const normalizedToken = normalizeToken(token)
  cachedPhoneAuthToken = normalizedToken

  if (!isNativePhoneStorageAvailable()) {
    if (!normalizedToken) {
      localStorage.removeItem(PHONE_AUTH_TOKEN_STORAGE_KEY)
      return
    }
    localStorage.setItem(PHONE_AUTH_TOKEN_STORAGE_KEY, normalizedToken)
    return
  }

  if (!normalizedToken) {
    await SecureStorage.removeItem(PHONE_AUTH_TOKEN_STORAGE_KEY)
    await removeLegacyLocalStorageToken()
    return
  }

  await SecureStorage.setItem(PHONE_AUTH_TOKEN_STORAGE_KEY, normalizedToken)
  await removeLegacyLocalStorageToken()
}
