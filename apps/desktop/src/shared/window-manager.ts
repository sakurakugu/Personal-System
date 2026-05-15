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
