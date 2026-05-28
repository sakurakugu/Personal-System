import { IPC_CHANNELS } from '../shared/ipc-channels.mjs'
import { createInvokeBridge } from './ipc-helpers.mjs'

function createAuthBridge(ipcRenderer) {
  return {
    loadDesktopAuthToken: createInvokeBridge(ipcRenderer, IPC_CHANNELS.authLoadToken),
    saveDesktopAuthToken: createInvokeBridge(ipcRenderer, IPC_CHANNELS.authSaveToken),
    checkGitEnvironment: createInvokeBridge(ipcRenderer, IPC_CHANNELS.utilityCheckGit),
    convertFileSrc: createInvokeBridge(ipcRenderer, IPC_CHANNELS.fileToUrl),
  }
}

export {
  createAuthBridge,
}
