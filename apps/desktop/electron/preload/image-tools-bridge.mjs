import { IPC_CHANNELS } from '../shared/ipc-channels.mjs'
import { createInvokeBridge } from './ipc-helpers.mjs'

function createImageToolsBridge(ipcRenderer) {
  return {
    imageToolsGetCapabilities: createInvokeBridge(ipcRenderer, IPC_CHANNELS.imageToolsGetCapabilities),
    imageToolsSelectInputs: createInvokeBridge(ipcRenderer, IPC_CHANNELS.imageToolsSelectInputs),
    imageToolsSelectOutputPath: createInvokeBridge(ipcRenderer, IPC_CHANNELS.imageToolsSelectOutputPath),
    imageToolsImportFromPaths: createInvokeBridge(ipcRenderer, IPC_CHANNELS.imageToolsImportFromPaths),
    imageToolsConvert: createInvokeBridge(ipcRenderer, IPC_CHANNELS.imageToolsConvert),
    imageToolsEdit: createInvokeBridge(ipcRenderer, IPC_CHANNELS.imageToolsEdit),
    imageToolsStitch: createInvokeBridge(ipcRenderer, IPC_CHANNELS.imageToolsStitch),
    imageToolsRelease: createInvokeBridge(ipcRenderer, IPC_CHANNELS.imageToolsRelease),
  }
}

export {
  createImageToolsBridge,
}
