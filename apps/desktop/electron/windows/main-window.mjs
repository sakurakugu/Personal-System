import { BrowserWindow } from 'electron'

import { WINDOW_STATE_EVENT_CHANNEL } from '../shared/constants.mjs'
import { loadWindow, preloadPath } from '../shared/environment.mjs'
import { showAndFocusWindow } from './window-utils.mjs'

let mainWindow = null

function emitMainWindowState() {
  if (!mainWindow || mainWindow.isDestroyed()) {
    return
  }

  mainWindow.webContents.send(WINDOW_STATE_EVENT_CHANNEL, {
    maximized: mainWindow.isMaximized(),
  })
}

function createMainWindow() {
  if (mainWindow && !mainWindow.isDestroyed()) {
    return mainWindow
  }

  mainWindow = new BrowserWindow({
    width: 1280,
    height: 860,
    minWidth: 960,
    minHeight: 680,
    frame: false,
    show: false,
    webPreferences: {
      preload: preloadPath,
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
    },
  })

  mainWindow.once('ready-to-show', () => {
    console.log('桌面端主窗口已就绪')
    mainWindow?.show()
  })

  mainWindow.webContents.on('did-fail-load', (_event, errorCode, errorDescription, validatedURL) => {
    console.error('桌面端主窗口加载失败', {
      errorCode,
      errorDescription,
      validatedURL,
    })
  })

  mainWindow.on('closed', () => {
    mainWindow = null
  })

  mainWindow.on('maximize', emitMainWindowState)
  mainWindow.on('unmaximize', emitMainWindowState)
  mainWindow.on('enter-full-screen', emitMainWindowState)
  mainWindow.on('leave-full-screen', emitMainWindowState)

  void loadWindow(mainWindow, '/')

  return mainWindow
}

function openMainWindow() {
  return showAndFocusWindow(createMainWindow())
}

function getCurrentMainWindowState(window) {
  if (!window || window.isDestroyed()) {
    return { maximized: false }
  }

  return {
    maximized: window.isMaximized(),
  }
}

export {
  createMainWindow,
  getCurrentMainWindowState,
  openMainWindow,
}
