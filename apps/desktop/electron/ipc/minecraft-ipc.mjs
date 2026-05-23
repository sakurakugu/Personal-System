import { ipcMain } from 'electron'

import { IPC_CHANNELS } from '../shared/ipc-channels.mjs'
import {
  queryMinecraftServer,
  readMinecraftServerStorage,
  writeMinecraftServerStorage,
} from '../services/minecraft-tool.mjs'

function registerMinecraftIpc() {
  ipcMain.handle(IPC_CHANNELS.minecraftReadStorage, async () => {
    return await readMinecraftServerStorage()
  })

  ipcMain.handle(IPC_CHANNELS.minecraftWriteStorage, async (_event, data) => {
    await writeMinecraftServerStorage(data)
  })

  ipcMain.handle(IPC_CHANNELS.minecraftQuery, async (_event, request) => {
    return await queryMinecraftServer(request)
  })
}

export {
  registerMinecraftIpc,
}
