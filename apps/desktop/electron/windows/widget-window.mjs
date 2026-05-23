import { BrowserWindow, screen } from 'electron'

import {
  WIDGET_STATE_EVENT_CHANNEL,
  WIDGET_WINDOW_MIN_HEIGHT,
  WIDGET_WINDOW_WIDTH,
} from '../shared/constants.mjs'
import { loadWindow, preloadPath } from '../shared/environment.mjs'
import { getStoredWidgetWindowState } from '../services/widget-state.mjs'
import { showAndFocusWindow } from './window-utils.mjs'

let widgetWindow = null

function getWidgetWindow() {
  return widgetWindow
}

function applyWidgetWindowState(window, nextState) {
  window.setAlwaysOnTop(nextState.alwaysOnTop)
  window.setMovable(nextState.movable)
}

function getCurrentWidgetWindowState() {
  const widgetWindowState = getStoredWidgetWindowState()

  if (widgetWindow && !widgetWindow.isDestroyed()) {
    return {
      open: true,
      alwaysOnTop: widgetWindow.isAlwaysOnTop(),
      movable: widgetWindow.isMovable(),
      surfaceOpacity: widgetWindowState.surfaceOpacity,
      showCloseButton: widgetWindowState.showCloseButton,
    }
  }

  return {
    open: false,
    alwaysOnTop: widgetWindowState.alwaysOnTop,
    movable: widgetWindowState.movable,
    surfaceOpacity: widgetWindowState.surfaceOpacity,
    showCloseButton: widgetWindowState.showCloseButton,
  }
}

function emitWidgetWindowState() {
  const payload = getCurrentWidgetWindowState()

  for (const window of BrowserWindow.getAllWindows()) {
    if (!window.isDestroyed()) {
      window.webContents.send(WIDGET_STATE_EVENT_CHANNEL, payload)
    }
  }
}

function resizeWidgetWindowHeight(contentHeight) {
  if (!widgetWindow || widgetWindow.isDestroyed()) {
    return null
  }

  const bounds = widgetWindow.getBounds()
  const display = screen.getDisplayMatching(bounds)
  const workAreaHeight = display.workArea.height
  const nextHeight = Math.max(WIDGET_WINDOW_MIN_HEIGHT, Math.min(Math.round(contentHeight), workAreaHeight - 32))
  const currentSize = widgetWindow.getSize()

  if (Math.abs(currentSize[1] - nextHeight) <= 1 && currentSize[0] === WIDGET_WINDOW_WIDTH) {
    return nextHeight
  }

  widgetWindow.setBounds({
    x: bounds.x,
    y: bounds.y,
    width: WIDGET_WINDOW_WIDTH,
    height: nextHeight,
  })

  return nextHeight
}

function createWidgetWindow() {
  if (widgetWindow && !widgetWindow.isDestroyed()) {
    return widgetWindow
  }

  const widgetWindowState = getStoredWidgetWindowState()

  widgetWindow = new BrowserWindow({
    width: WIDGET_WINDOW_WIDTH,
    height: 620,
    minWidth: WIDGET_WINDOW_WIDTH,
    maxWidth: WIDGET_WINDOW_WIDTH,
    minHeight: WIDGET_WINDOW_MIN_HEIGHT,
    resizable: false,
    frame: false,
    transparent: true,
    backgroundColor: '#00000000',
    alwaysOnTop: widgetWindowState.alwaysOnTop,
    movable: widgetWindowState.movable,
    skipTaskbar: true,
    show: false,
    webPreferences: {
      preload: preloadPath,
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
    },
  })

  applyWidgetWindowState(widgetWindow, widgetWindowState)

  widgetWindow.once('ready-to-show', () => {
    widgetWindow?.show()
    emitWidgetWindowState()
  })

  widgetWindow.webContents.on('did-fail-load', (_event, errorCode, errorDescription, validatedURL) => {
    console.error('桌面端小工具窗口加载失败', {
      errorCode,
      errorDescription,
      validatedURL,
    })
  })

  widgetWindow.on('closed', () => {
    widgetWindow = null
    emitWidgetWindowState()
  })

  void loadWindow(widgetWindow, '/widget.html')

  return widgetWindow
}

function openWidgetWindow() {
  const window = showAndFocusWindow(createWidgetWindow())
  emitWidgetWindowState()
  return window
}

function closeWidgetWindow() {
  if (!widgetWindow || widgetWindow.isDestroyed()) {
    emitWidgetWindowState()
    return false
  }

  widgetWindow.close()
  return true
}

function applySavedWidgetWindowState(nextState) {
  if (widgetWindow && !widgetWindow.isDestroyed()) {
    applyWidgetWindowState(widgetWindow, nextState)
  }

  emitWidgetWindowState()
}

export {
  applySavedWidgetWindowState,
  closeWidgetWindow,
  createWidgetWindow,
  emitWidgetWindowState,
  getCurrentWidgetWindowState,
  getWidgetWindow,
  openWidgetWindow,
  resizeWidgetWindowHeight,
}
