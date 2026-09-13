import { registerAuthIpc } from './auth-ipc.mjs'
import { registerWindowIpc } from './window-ipc.mjs'

function registerIpcHandlers() {
  registerWindowIpc()
  registerAuthIpc()
  console.log('桌面端 IPC 处理器注册完成')
}

export {
  registerIpcHandlers,
}
