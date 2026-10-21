import { createAppBridge } from './app-bridge.mjs'
import { createAuthBridge } from './auth-bridge.mjs'
import { createWindowBridge } from './window-bridge.mjs'

function createDesktopBridge(ipcRenderer) {
  return {
    runtime: 'electron',
    ...createAppBridge(ipcRenderer),
    ...createWindowBridge(ipcRenderer),
    ...createAuthBridge(ipcRenderer),
  }
}

export {
  createDesktopBridge,
}
