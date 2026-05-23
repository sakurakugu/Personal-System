import { 获取必需桌面运行时 } from './desktop-runtime'

export type 我的世界服务器版本 = 'auto' | 'java' | 'bedrock'

export type 我的世界服务器查询请求 = {
  address: string
  edition?: 我的世界服务器版本
  timeout?: number
}

export type 我的世界服务器查询结果 = {
  requestedAddress: string
  requestedEdition: 我的世界服务器版本
  host: string
  requestedPort: number | null
  online: boolean
  resolvedEdition: 'java' | 'bedrock' | null
  resolvedPort: number | null
  latencyMs: number | null
  versionName: string | null
  protocolVersion: number | null
  playersOnline: number | null
  playersMax: number | null
  samplePlayers: string[]
  description: string | null
  mapName: string | null
  gameMode: string | null
  brand: string | null
  icon: string | null
  error: string | null
}

export async function 查询我的世界服务器(request: 我的世界服务器查询请求): Promise<我的世界服务器查询结果> {
  const runtime = 获取必需桌面运行时('当前环境不支持本地服务器查询')
  return await runtime.queryMinecraftServer(request)
}
