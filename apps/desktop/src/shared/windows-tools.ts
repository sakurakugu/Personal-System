import { invoke, isTauri } from '@tauri-apps/api/core'

export type Git环境状态 = {
  installed: boolean
  version: string | null
  detail: string
}

function assertDesktopRuntime() {
  if (!isTauri()) {
    throw new Error('当前环境不支持 Windows 工具')
  }
}

export async function 检查Git环境(): Promise<Git环境状态> {
  assertDesktopRuntime()
  return await invoke<Git环境状态>('check_git_environment')
}
