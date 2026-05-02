import { Capacitor } from '@capacitor/core'
import { getConfiguredActiveBaseUrl } from './context'

const DEFAULT_WEB_API_BASE = '/api/v1'
const DEFAULT_ANDROID_EMULATOR_API_BASE = 'http://10.0.2.2:8000/api/v1'
const DEFAULT_IOS_SIMULATOR_API_BASE = 'http://localhost:8000/api/v1'

function isAbsoluteUrl(value: string): boolean {
  return /^https?:\/\//.test(value)
}

export function isNativeDevServerMode(): boolean {
  return Capacitor.isNativePlatform() && import.meta.env.DEV
}

export function resolveNativeDevServerApiBase(): string {
  const webApiBase = import.meta.env.VITE_API_BASE?.trim() || DEFAULT_WEB_API_BASE
  if (isAbsoluteUrl(webApiBase)) {
    return webApiBase
  }
  if (typeof window !== 'undefined' && window.location?.origin) {
    return new URL(webApiBase, window.location.origin).toString().replace(/\/+$/, '')
  }
  return webApiBase
}

export function isApiEnvironmentSwitchEnabled(): boolean {
  if (!Capacitor.isNativePlatform()) {
    return false
  }
  if (import.meta.env.DEV) {
    return true
  }
  return import.meta.env.VITE_ENABLE_API_ENV_SWITCH === 'true'
}

export function resolveApiBase(): string {
  const webApiBase = import.meta.env.VITE_API_BASE?.trim()
  const nativeApiBase = import.meta.env.VITE_NATIVE_API_BASE?.trim()

  if (!Capacitor.isNativePlatform()) {
    return webApiBase || DEFAULT_WEB_API_BASE
  }
  if (isNativeDevServerMode()) {
    return webApiBase || DEFAULT_WEB_API_BASE
  }

  if (nativeApiBase) {
    return nativeApiBase
  }

  if (webApiBase && isAbsoluteUrl(webApiBase)) {
    return webApiBase
  }

  if (Capacitor.getPlatform() === 'android') {
    return DEFAULT_ANDROID_EMULATOR_API_BASE
  }

  return DEFAULT_IOS_SIMULATOR_API_BASE
}

export function resolveCurrentApiBase(): string {
  if (Capacitor.isNativePlatform()) {
    return getConfiguredActiveBaseUrl() || resolveApiBase()
  }
  return resolveApiBase()
}
