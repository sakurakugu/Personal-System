import { getDesktopRuntime } from './desktop-runtime'

export async function 打开桌面主窗口() {
  const runtime = getDesktopRuntime()
  if (!runtime) {
    return null
  }
  return await runtime.openDesktopMainWindow()
}

export async function 打开桌面小工具窗口() {
  const runtime = getDesktopRuntime()
  if (!runtime) {
    return null
  }
  return await runtime.openDesktopWidgetWindow()
}

export async function 关闭桌面小工具窗口() {
  const runtime = getDesktopRuntime()
  if (!runtime) {
    return false
  }
  return await runtime.closeDesktopWidgetWindow()
}

export async function 获取桌面小工具窗口状态() {
  const runtime = getDesktopRuntime()
  if (!runtime) {
    return {
      open: false,
      alwaysOnTop: true,
      movable: false,
      surfaceOpacity: 100,
      showCloseButton: true,
    }
  }
  return await runtime.getDesktopWidgetWindowState()
}

export async function 设置桌面小工具窗口内容高度(height: number) {
  const runtime = getDesktopRuntime()
  if (!runtime) {
    return null
  }
  return await runtime.setDesktopWidgetWindowContentHeight(height)
}

export async function 设置桌面小工具窗口状态(payload: {
  alwaysOnTop?: boolean
  movable?: boolean
  surfaceOpacity?: number
  showCloseButton?: boolean
}) {
  const runtime = getDesktopRuntime()
  if (!runtime) {
    return {
      open: false,
      alwaysOnTop: true,
      movable: false,
      surfaceOpacity: 100,
      showCloseButton: true,
    }
  }
  return await runtime.setDesktopWidgetWindowState(payload)
}

export function 监听桌面小工具窗口状态变更(listener: (payload: {
  open: boolean
  alwaysOnTop: boolean
  movable: boolean
  surfaceOpacity: number
  showCloseButton: boolean
}) => void) {
  const runtime = getDesktopRuntime()
  if (!runtime) {
    return () => {}
  }
  return runtime.onDesktopWidgetWindowStateChange(listener)
}

export async function 关闭当前窗口() {
  const runtime = getDesktopRuntime()
  if (!runtime) {
    return
  }
  await runtime.closeCurrentWindow()
}

export async function 最小化当前窗口() {
  const runtime = getDesktopRuntime()
  if (!runtime) {
    return
  }
  await runtime.minimizeCurrentWindow()
}

export async function 切换最大化当前窗口() {
  const runtime = getDesktopRuntime()
  if (!runtime) {
    return { maximized: false }
  }
  return await runtime.toggleMaximizeCurrentWindow()
}

export async function 获取当前窗口状态() {
  const runtime = getDesktopRuntime()
  if (!runtime) {
    return { maximized: false }
  }
  return await runtime.getCurrentWindowState()
}

export function 监听当前窗口状态变更(listener: (payload: { maximized: boolean }) => void) {
  const runtime = getDesktopRuntime()
  if (!runtime) {
    return () => {}
  }
  return runtime.onCurrentWindowStateChange(listener)
}
