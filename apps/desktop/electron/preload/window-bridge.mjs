import { IPC_CHANNELS, IPC_EVENTS } from '../shared/ipc-channels.mjs'
import {
  createInvokeBridge,
  createPayloadListenerBridge,
} from './ipc-helpers.mjs'

function createWindowBridge(ipcRenderer) {
  return {
    openDesktopMainWindow: createInvokeBridge(ipcRenderer, IPC_CHANNELS.windowOpenMain),
    openDesktopWidgetWindow: createInvokeBridge(ipcRenderer, IPC_CHANNELS.windowOpenWidget),
    closeDesktopWidgetWindow: createInvokeBridge(ipcRenderer, IPC_CHANNELS.windowCloseWidget),
    getDesktopWidgetWindowState: createInvokeBridge(ipcRenderer, IPC_CHANNELS.widgetGetState),
    setDesktopWidgetWindowState: createInvokeBridge(ipcRenderer, IPC_CHANNELS.widgetSetState),
    setDesktopWidgetWindowContentHeight: createInvokeBridge(ipcRenderer, IPC_CHANNELS.widgetSetContentHeight),
    onDesktopWidgetWindowStateChange: createPayloadListenerBridge(ipcRenderer, IPC_EVENTS.widgetStateChanged),
    closeCurrentWindow: createInvokeBridge(ipcRenderer, IPC_CHANNELS.windowCloseCurrent),
    minimizeCurrentWindow: createInvokeBridge(ipcRenderer, IPC_CHANNELS.windowMinimizeCurrent),
    toggleMaximizeCurrentWindow: createInvokeBridge(ipcRenderer, IPC_CHANNELS.windowToggleMaximizeCurrent),
    getCurrentWindowState: createInvokeBridge(ipcRenderer, IPC_CHANNELS.windowGetCurrentState),
    onCurrentWindowStateChange: createPayloadListenerBridge(ipcRenderer, IPC_EVENTS.windowStateChanged),
  }
}

export {
  createWindowBridge,
}
