import { 获取桌面运行时 } from './desktop-runtime'

export type Git环境状态 = {
  installed: boolean
  version: string | null
  detail: string
}

function 断言桌面运行时() {
  if (获取桌面运行时()) {
    return
  }
  throw new Error('当前环境不支持 Windows 工具')
}

export async function 检查Git环境(): Promise<Git环境状态> {
  断言桌面运行时()
  const runtime = 获取桌面运行时()
  if (!runtime) {
    throw new Error('当前环境不支持 Windows 工具')
  }
  return await runtime.checkGitEnvironment()
}
