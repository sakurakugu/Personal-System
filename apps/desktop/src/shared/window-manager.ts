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
