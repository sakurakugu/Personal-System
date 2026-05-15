import { getDesktopRuntime } from './desktop-runtime'

export type Git环境状态 = {
  installed: boolean
  version: string | null
  detail: string
}

function assertDesktopRuntime() {
  if (getDesktopRuntime()) {
    return
  }
  throw new Error('当前环境不支持 Windows 工具')
}

export async function 检查Git环境(): Promise<Git环境状态> {
  assertDesktopRuntime()
  const runtime = getDesktopRuntime()
  if (!runtime) {
    throw new Error('当前环境不支持 Windows 工具')
  }
  return await runtime.checkGitEnvironment()
}
