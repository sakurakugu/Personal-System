import type { 桌面运行时Api } from './desktop-runtime-contract'

declare global {
  interface Window {
    personalSystemDesktop?: 桌面运行时Api
  }
}

export function 获取桌面运行时() {
  return window.personalSystemDesktop ?? null
}

export function 获取必需桌面运行时(errorMessage: string): 桌面运行时Api {
  const runtime = 获取桌面运行时()
  if (!runtime) {
    throw new Error(errorMessage)
  }

  return runtime
}

export function 是否为Electron桌面() {
  return 获取桌面运行时()?.runtime === 'electron'
}
