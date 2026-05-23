import { IPC_CHANNELS } from '../shared/ipc-channels.mjs'
import { createInvokeBridge } from './ipc-helpers.mjs'

function createMinecraftBridge(ipcRenderer) {
  return {
    readMinecraftServerStorage: createInvokeBridge(ipcRenderer, IPC_CHANNELS.minecraftReadStorage),
    writeMinecraftServerStorage: createInvokeBridge(ipcRenderer, IPC_CHANNELS.minecraftWriteStorage),
    queryMinecraftServer: createInvokeBridge(ipcRenderer, IPC_CHANNELS.minecraftQuery),
  }
}

export {
  createMinecraftBridge,
}
