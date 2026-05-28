import { ipcMain } from 'electron'

import { IPC_CHANNELS } from '../shared/ipc-channels.mjs'
import {
  loadDesktopAuthToken,
  saveDesktopAuthToken,
} from '../services/auth-token.mjs'

function registerAuthIpc() {
  ipcMain.handle(IPC_CHANNELS.authLoadToken, async () => {
    return await loadDesktopAuthToken()
  })

  ipcMain.handle(IPC_CHANNELS.authSaveToken, async (_event, token) => {
    await saveDesktopAuthToken(token)
  })
}

export {
  registerAuthIpc,
}
