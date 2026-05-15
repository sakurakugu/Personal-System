import { getDesktopRuntime } from './desktop-runtime'

export type 我的世界服务器记录 = {
  address: string
  edition: 'auto' | 'java' | 'bedrock'
}

export type 我的世界服务器存储数据 = {
  favorites: 我的世界服务器记录[]
  history: 我的世界服务器记录[]
}

export async function 读取我的世界服务器存储(): Promise<我的世界服务器存储数据> {
  const runtime = getDesktopRuntime()
  if (!runtime) {
    return { favorites: [], history: [] }
  }
  return await runtime.readMinecraftServerStorage()
}

export async function 写入我的世界服务器存储(data: 我的世界服务器存储数据): Promise<void> {
  const runtime = getDesktopRuntime()
  if (!runtime) {
    return
  }
  await runtime.writeMinecraftServerStorage(data)
}
