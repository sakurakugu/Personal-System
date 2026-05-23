import { BrowserWindow, ipcMain } from 'electron'

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
  openWidgetWindow,
  resizeWidgetWindowHeight,
} from '../windows/widget-window.mjs'
import {
  getCurrentMainWindowState,
  openMainWindow,
} from '../windows/main-window.mjs'

function registerWindowIpc() {
  ipcMain.handle(IPC_CHANNELS.windowOpenMain, async () => {
    const window = openMainWindow()
    return window.id
  })

  ipcMain.handle(IPC_CHANNELS.windowOpenWidget, async () => {
    await ensureWidgetWindowStateLoaded()
    const window = openWidgetWindow()
    return window.id
  })

  ipcMain.handle(IPC_CHANNELS.windowCloseWidget, async () => {
    return closeWidgetWindow()
  })

  ipcMain.handle(IPC_CHANNELS.windowCloseCurrent, async (event) => {
    const targetWindow = BrowserWindow.fromWebContents(event.sender)
    if (!targetWindow || targetWindow.isDestroyed()) {
      return
    }

    targetWindow.close()
  })

  ipcMain.handle(IPC_CHANNELS.windowMinimizeCurrent, async (event) => {
    const targetWindow = BrowserWindow.fromWebContents(event.sender)
    if (!targetWindow || targetWindow.isDestroyed()) {
      return
    }

    targetWindow.minimize()
  })

  ipcMain.handle(IPC_CHANNELS.windowToggleMaximizeCurrent, async (event) => {
    const targetWindow = BrowserWindow.fromWebContents(event.sender)
    if (!targetWindow || targetWindow.isDestroyed()) {
      return { maximized: false }
    }

    if (targetWindow.isMaximized()) {
      targetWindow.unmaximize()
    } else {
      targetWindow.maximize()
    }

    return getCurrentMainWindowState(targetWindow)
  })

  ipcMain.handle(IPC_CHANNELS.windowGetCurrentState, async (event) => {
    const targetWindow = BrowserWindow.fromWebContents(event.sender)
    return getCurrentMainWindowState(targetWindow)
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
