import { ipcMain } from 'electron'
import { execFile } from 'node:child_process'

import { IPC_CHANNELS } from '../shared/ipc-channels.mjs'
import { buildLocalFileUrl } from '../shared/dev-file-protocol.mjs'

function checkGitInstalled() {
  return new Promise((resolve) => {
    execFile('git', ['--version'], (error, stdout, stderr) => {
      if (error) {
        resolve({
          installed: false,
          version: null,
          detail: `未找到 Git 命令：${error.message}`,
        })
        return
      }

      const version = stdout.trim()
      resolve({
        installed: true,
        version: version || null,
        detail: version ? `已检测到 Git：${version}` : stderr.trim() || 'Git 环境检查完成',
      })
    })
  })
}

function registerUtilityIpc() {
  ipcMain.handle(IPC_CHANNELS.utilityCheckGit, async () => {
    try {
      return await checkGitInstalled()
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error)
      return {
        installed: false,
        version: null,
        detail: `Git 环境检查失败：${message}`,
      }
    }
  })

  ipcMain.handle(IPC_CHANNELS.fileToUrl, async (_event, filePath) => {
    return buildLocalFileUrl(filePath)
  })
}

export {
  registerUtilityIpc,
}
