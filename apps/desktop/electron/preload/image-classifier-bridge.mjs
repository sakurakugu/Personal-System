import { randomUUID } from 'node:crypto'

import { IPC_CHANNELS, IPC_EVENTS } from '../shared/ipc-channels.mjs'
import { createInvokeBridge } from './ipc-helpers.mjs'

function createImageClassifierBridge(ipcRenderer) {
  return {
    checkImageClassifierEnvironment: createInvokeBridge(ipcRenderer, IPC_CHANNELS.imageClassifierCheckEnvironment),
    selectImageClassifierInputs: createInvokeBridge(ipcRenderer, IPC_CHANNELS.imageClassifierSelectInputs),
    selectImageClassifierOutputPath: createInvokeBridge(ipcRenderer, IPC_CHANNELS.imageClassifierSelectOutputPath),
    discoverImageClassifierInputs: createInvokeBridge(ipcRenderer, IPC_CHANNELS.imageClassifierDiscoverInputs),
    stopImageClassifier: createInvokeBridge(ipcRenderer, IPC_CHANNELS.imageClassifierStop),
    imageClassifierAction: createInvokeBridge(ipcRenderer, IPC_CHANNELS.imageClassifierAction),
    runImageClassifier: createInvokeBridge(ipcRenderer, IPC_CHANNELS.imageClassifierRun),
    runImageClassifierResultAction: createInvokeBridge(ipcRenderer, IPC_CHANNELS.imageClassifierResultAction),
    runImageClassifierStream: (request, onEvent) => {
      const channel = `${IPC_EVENTS.imageClassifierStreamPrefix}${randomUUID()}`
      const listener = (_event, payload) => {
        onEvent(payload)
      }

      ipcRenderer.on(channel, listener)
      return ipcRenderer.invoke(IPC_CHANNELS.imageClassifierRunStream, {
        ...request,
        eventChannel: channel,
      }).finally(() => {
        ipcRenderer.removeListener(channel, listener)
      })
    },
  }
}

export {
  createImageClassifierBridge,
}
