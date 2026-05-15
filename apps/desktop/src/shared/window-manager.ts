import { getDesktopRuntime } from './desktop-runtime'

export async function openDesktopMainWindow() {
  const runtime = getDesktopRuntime()
  if (!runtime) {
    return null
  }
  return await runtime.openDesktopMainWindow()
}

export async function openDesktopWidgetWindow() {
  const runtime = getDesktopRuntime()
  if (!runtime) {
    return null
  }
  return await runtime.openDesktopWidgetWindow()
}

export async function closeDesktopWidgetWindow() {
  const runtime = getDesktopRuntime()
  if (!runtime) {
    return false
  }
  return await runtime.closeDesktopWidgetWindow()
}

export async function getDesktopWidgetWindowState() {
  const runtime = getDesktopRuntime()
  if (!runtime) {
    return { open: false, alwaysOnTop: true, movable: false }
  }
  return await runtime.getDesktopWidgetWindowState()
}

export async function setDesktopWidgetWindowContentHeight(height: number) {
  const runtime = getDesktopRuntime()
  if (!runtime) {
    return null
  }
  return await runtime.setDesktopWidgetWindowContentHeight(height)
}

export async function setDesktopWidgetWindowState(payload: {
  alwaysOnTop?: boolean
  movable?: boolean
}) {
  const runtime = getDesktopRuntime()
  if (!runtime) {
    return { open: false, alwaysOnTop: true, movable: false }
  }
  return await runtime.setDesktopWidgetWindowState(payload)
}

export function onDesktopWidgetWindowStateChange(listener: (payload: {
  open: boolean
  alwaysOnTop: boolean
  movable: boolean
}) => void) {
  const runtime = getDesktopRuntime()
  if (!runtime) {
    return () => {}
  }
  return runtime.onDesktopWidgetWindowStateChange(listener)
}

export async function closeCurrentWindow() {
  const runtime = getDesktopRuntime()
  if (!runtime) {
    return
  }
  await runtime.closeCurrentWindow()
}

export async function minimizeCurrentWindow() {
  const runtime = getDesktopRuntime()
  if (!runtime) {
    return
  }
  await runtime.minimizeCurrentWindow()
}

export async function toggleMaximizeCurrentWindow() {
  const runtime = getDesktopRuntime()
  if (!runtime) {
    return { maximized: false }
  }
  return await runtime.toggleMaximizeCurrentWindow()
}

export async function getCurrentWindowState() {
  const runtime = getDesktopRuntime()
  if (!runtime) {
    return { maximized: false }
  }
  return await runtime.getCurrentWindowState()
}

export function onCurrentWindowStateChange(listener: (payload: { maximized: boolean }) => void) {
  const runtime = getDesktopRuntime()
  if (!runtime) {
    return () => {}
  }
  return runtime.onCurrentWindowStateChange(listener)
}
