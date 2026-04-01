import { Capacitor } from '@capacitor/core'

const DEFAULT_WEB_API_BASE = '/api/v1'
const DEFAULT_ANDROID_EMULATOR_API_BASE = 'http://10.0.2.2:8000/api/v1'
const DEFAULT_IOS_SIMULATOR_API_BASE = 'http://localhost:8000/api/v1'

function isAbsoluteUrl(value: string): boolean {
  return /^https?:\/\//.test(value)
}

export function resolveApiBase(): string {
  const webApiBase = import.meta.env.VITE_API_BASE?.trim()
  const nativeApiBase = import.meta.env.VITE_NATIVE_API_BASE?.trim()

  if (!Capacitor.isNativePlatform()) {
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
