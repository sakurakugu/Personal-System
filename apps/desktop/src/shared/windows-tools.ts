import { 获取必需桌面运行时 } from './desktop-runtime'

export type Git环境状态 = {
  installed: boolean
  version: string | null
  detail: string
}

export async function 检查Git环境(): Promise<Git环境状态> {
  const runtime = 获取必需桌面运行时('当前环境不支持 Windows 工具')
  return await runtime.checkGitEnvironment()
}
