import { createAuthBridge } from './auth-bridge.mjs'
import { createImageClassifierBridge } from './image-classifier-bridge.mjs'
import { createImageToolsBridge } from './image-tools-bridge.mjs'
import { createMinecraftBridge } from './minecraft-bridge.mjs'
import { createWindowBridge } from './window-bridge.mjs'

function createDesktopBridge(ipcRenderer) {
  return {
    runtime: 'electron',
    ...createWindowBridge(ipcRenderer),
    ...createAuthBridge(ipcRenderer),
    ...createMinecraftBridge(ipcRenderer),
    ...createImageToolsBridge(ipcRenderer),
    ...createImageClassifierBridge(ipcRenderer),
  }
}

export {
  createDesktopBridge,
}
