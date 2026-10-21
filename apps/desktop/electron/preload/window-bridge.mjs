import { IPC_CHANNELS, IPC_EVENTS } from '../shared/ipc-channels.mjs'
import {
  createInvokeBridge,
  createPayloadListenerBridge,
} from './ipc-helpers.mjs'

function createWindowBridge(ipcRenderer) {
  return {
    closeDesktopWidgetWindow: createInvokeBridge(ipcRenderer, IPC_CHANNELS.windowCloseWidget),
    getDesktopWidgetWindowState: createInvokeBridge(ipcRenderer, IPC_CHANNELS.widgetGetState),
    setDesktopWidgetWindowContentHeight: createInvokeBridge(ipcRenderer, IPC_CHANNELS.widgetSetContentHeight),
    setDesktopWidgetWindowState: createInvokeBridge(ipcRenderer, IPC_CHANNELS.widgetSetState),
    onDesktopWidgetWindowStateChange: createPayloadListenerBridge(ipcRenderer, IPC_EVENTS.widgetStateChanged),
  }
}

export {
  createWindowBridge,
}
