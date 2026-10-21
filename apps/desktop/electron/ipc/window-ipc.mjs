import { ipcMain } from 'electron'

import { IPC_CHANNELS } from '../shared/ipc-channels.mjs'
import {
  ensureWidgetWindowStateLoaded,
  saveWidgetWindowState,
} from '../services/widget-state.mjs'
import {
  applySavedWidgetWindowState,
  closeWidgetWindow,
  getCurrentWidgetWindowState,
  getWidgetWindow,
  resizeWidgetWindowHeight,
} from '../windows/widget-window.mjs'

function registerWindowIpc() {
  ipcMain.handle(IPC_CHANNELS.windowCloseWidget, async () => {
    return closeWidgetWindow()
  })

  ipcMain.handle(IPC_CHANNELS.widgetGetState, async () => {
    await ensureWidgetWindowStateLoaded()
    return getCurrentWidgetWindowState()
  })

  ipcMain.handle(IPC_CHANNELS.widgetSetState, async (_event, payload) => {
    const currentState = await ensureWidgetWindowStateLoaded()
    const nextState = await saveWidgetWindowState({
      ...currentState,
      ...payload,
    })

    applySavedWidgetWindowState(nextState)
    return getCurrentWidgetWindowState()
  })

  ipcMain.handle(IPC_CHANNELS.widgetSetContentHeight, async (_event, height) => {
    const widgetWindow = getWidgetWindow()
    if (!widgetWindow || widgetWindow.isDestroyed()) {
      return null
    }

    if (typeof height !== 'number' || !Number.isFinite(height)) {
      return widgetWindow.getBounds().height
    }

    return resizeWidgetWindowHeight(height)
  })
}

export {
  registerWindowIpc,
}
