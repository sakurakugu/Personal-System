import { registerAuthIpc } from './auth-ipc.mjs'
import { registerImageClassifierIpc } from './image-classifier-ipc.mjs'
import { registerImageToolsIpc } from './image-tools-ipc.mjs'
import { registerMinecraftIpc } from './minecraft-ipc.mjs'
import { registerUtilityIpc } from './utility-ipc.mjs'
import { registerWindowIpc } from './window-ipc.mjs'

function registerIpcHandlers() {
  registerWindowIpc()
  registerAuthIpc()
  registerMinecraftIpc()
  registerImageToolsIpc()
  registerImageClassifierIpc()
  registerUtilityIpc()
  console.log('桌面端 IPC 处理器注册完成')
}

export {
  registerIpcHandlers,
}
