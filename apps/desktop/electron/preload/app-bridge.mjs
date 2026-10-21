import { IPC_CHANNELS } from '../shared/ipc-channels.mjs'
import { createInvokeBridge } from './ipc-helpers.mjs'

function createAppBridge(ipcRenderer) {
  return {
    openWebConsole: createInvokeBridge(ipcRenderer, IPC_CHANNELS.appOpenWebConsole),
  }
}

export {
  createAppBridge,
}
