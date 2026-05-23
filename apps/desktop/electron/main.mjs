import { app, BrowserWindow, Menu } from 'electron'
import process from 'node:process'

import { registerIpcHandlers } from './ipc/register-ipc-handlers.mjs'
import { ensureWidgetWindowStateLoaded } from './services/widget-state.mjs'
import { createMainWindow } from './windows/main-window.mjs'

registerIpcHandlers()

app.whenReady().then(async () => {
  await ensureWidgetWindowStateLoaded()
  Menu.setApplicationMenu(null)
  createMainWindow()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createMainWindow()
    }
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})
