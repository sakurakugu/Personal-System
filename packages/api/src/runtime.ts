import { Capacitor } from '@capacitor/core'
import { 获取已配置的活跃基地址 } from './context'

const DEFAULT_WEB_API_BASE = '/api/v1'
const DEFAULT_ANDROID_EMULATOR_API_BASE = 'http://10.0.2.2:8000/api/v1'
const DEFAULT_IOS_SIMULATOR_API_BASE = 'http://localhost:8000/api/v1'

function 是否为绝对URL(value: string): boolean {
  return /^https?:\/\//.test(value)
}

function 是否已配置活跃基地址(): boolean {
  return 获取已配置的活跃基地址() !== null
}

export function 是否为原生开发服务器模式(): boolean {
  return Capacitor.isNativePlatform() && import.meta.env.DEV
}

export function 解析原生开发服务器API基地址(): string {
  const webApiBase = import.meta.env.VITE_API_BASE?.trim() || DEFAULT_WEB_API_BASE
  if (是否为绝对URL(webApiBase)) {
    return webApiBase
  }
  if (typeof window !== 'undefined' && window.location?.origin) {
    return new URL(webApiBase, window.location.origin).toString().replace(/\/+$/, '')
  }
  return webApiBase
}

export function 是否启用API环境切换(): boolean {
  if (是否已配置活跃基地址()) {
    if (import.meta.env.DEV) {
      return true
    }
    return import.meta.env.VITE_ENABLE_API_ENV_SWITCH === 'true'
  }
  if (!Capacitor.isNativePlatform()) {
    return false
  }
  if (import.meta.env.DEV) {
    return true
  }
  return import.meta.env.VITE_ENABLE_API_ENV_SWITCH === 'true'
}

export function 解析API基地址(): string {
  const webApiBase = import.meta.env.VITE_API_BASE?.trim()
  const nativeApiBase = import.meta.env.VITE_NATIVE_API_BASE?.trim()

  if (!Capacitor.isNativePlatform()) {
    return webApiBase || DEFAULT_WEB_API_BASE
  }
  if (是否为原生开发服务器模式()) {
    return webApiBase || DEFAULT_WEB_API_BASE
  }

  if (nativeApiBase) {
    return nativeApiBase
  }

  if (webApiBase && 是否为绝对URL(webApiBase)) {
    return webApiBase
  }

  if (Capacitor.getPlatform() === 'android') {
    return DEFAULT_ANDROID_EMULATOR_API_BASE
  }

  return DEFAULT_IOS_SIMULATOR_API_BASE
}

export function 解析当前API基地址(): string {
  if (Capacitor.isNativePlatform() || 是否已配置活跃基地址()) {
    return 获取已配置的活跃基地址() || 解析API基地址()
  }
  return 解析API基地址()
}
