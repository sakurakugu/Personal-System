import { invoke, isTauri } from '@tauri-apps/api/core'

export async function openDesktopMainWindow() {
  if (!isTauri()) {
    return null
  }

  return await invoke<string | null>('open_desktop_main_window')
}

export async function openDesktopWidgetWindow() {
  if (!isTauri()) {
    return null
  }

  return await invoke<string | null>('open_desktop_widget_window')
}

export async function closeDesktopWidgetWindow() {
  if (!isTauri()) {
    return false
  }

  return await invoke<boolean>('close_desktop_widget_window')
}

export async function closeCurrentWindow() {
  if (!isTauri()) {
    return
  }

  await invoke('close_current_window')
}
