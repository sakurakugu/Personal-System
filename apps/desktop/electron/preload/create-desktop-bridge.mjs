import { createAuthBridge } from './auth-bridge.mjs'
import { createWindowBridge } from './window-bridge.mjs'

function createDesktopBridge(ipcRenderer) {
  return {
    runtime: 'electron',
    ...createWindowBridge(ipcRenderer),
    ...createAuthBridge(ipcRenderer),
  }
}

export {
  createDesktopBridge,
}
