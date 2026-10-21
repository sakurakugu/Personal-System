import { 获取桌面运行时 } from './desktop-runtime'
import type { 桌面小工具窗口状态, 桌面小工具窗口状态补丁 } from './desktop-runtime-contract'

/** 小工具默认窗口状态，运行时不值可用时作为兜底。 */
const 默认小工具窗口状态: 桌面小工具窗口状态 = {
  open: false,
  alwaysOnTop: true,
  movable: false,
  surfaceOpacity: 100,
  showCloseButton: true,
}

export async function 打开网页后台() {
  const runtime = 获取桌面运行时()
  if (!runtime) {
    return
  }
  await runtime.openWebConsole()
}

export async function 关闭桌面小工具窗口() {
  const runtime = 获取桌面运行时()
  if (!runtime) {
    return false
  }
  return await runtime.closeDesktopWidgetWindow()
}

export async function 获取桌面小工具窗口状态() {
  const runtime = 获取桌面运行时()
  if (!runtime) {
    return { ...默认小工具窗口状态 }
  }
  return await runtime.getDesktopWidgetWindowState()
}

export async function 设置桌面小工具窗口内容高度(height: number) {
  const runtime = 获取桌面运行时()
  if (!runtime) {
    return null
  }
  return await runtime.setDesktopWidgetWindowContentHeight(height)
}

export async function 设置桌面小工具窗口状态(payload: 桌面小工具窗口状态补丁) {
  const runtime = 获取桌面运行时()
  if (!runtime) {
    return { ...默认小工具窗口状态 }
  }
  return await runtime.setDesktopWidgetWindowState(payload)
}

export function 监听桌面小工具窗口状态变更(listener: (payload: 桌面小工具窗口状态) => void) {
  const runtime = 获取桌面运行时()
  if (!runtime) {
    return () => {}
  }
  return runtime.onDesktopWidgetWindowStateChange(listener)
}
