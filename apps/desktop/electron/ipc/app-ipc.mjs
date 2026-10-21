/**
 * 应用级 IPC：桌面端与网页后台之间的桥接。
 */
import { ipcMain, shell } from 'electron'

import { IPC_CHANNELS } from '../shared/ipc-channels.mjs'
import { getWebConsoleUrl } from '../shared/environment.mjs'

function registerAppIpc() {
  // 打开网页后台：开发环境指向本地 5173，打包后指向线上地址。
  ipcMain.handle(IPC_CHANNELS.appOpenWebConsole, async (event) => {
    const url = getWebConsoleUrl()
    await shell.openExternal(url)
    console.log('桌面端已打开网页后台', {
      url,
      senderUrl: event.senderFrame?.url ?? event.sender.getURL(),
    })
  })
}

export {
  registerAppIpc,
}
