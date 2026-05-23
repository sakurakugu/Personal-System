import { ipcMain } from 'electron'

import { IPC_CHANNELS } from '../shared/ipc-channels.mjs'
import {
  loadDesktopAuthToken,
  saveDesktopAuthToken,
  syncWidgetAuthToken,
} from '../services/auth-token.mjs'

function registerAuthIpc() {
  ipcMain.handle(IPC_CHANNELS.authLoadToken, async () => {
    return await loadDesktopAuthToken()
  })

  ipcMain.handle(IPC_CHANNELS.authSaveToken, async (_event, token) => {
    await saveDesktopAuthToken(token)
  })

  ipcMain.handle(IPC_CHANNELS.widgetSyncToken, async (_event, payload) => {
    return await syncWidgetAuthToken(payload)
  })
}

export {
  registerAuthIpc,
}
