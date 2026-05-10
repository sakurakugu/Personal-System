import { invoke, isTauri } from '@tauri-apps/api/core'

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

function assertDesktopRuntime() {
  if (!isTauri()) {
    throw new Error('当前环境不支持本地服务器查询')
  }
}

export async function 查询我的世界服务器(request: 我的世界服务器查询请求): Promise<我的世界服务器查询结果> {
  assertDesktopRuntime()
  return await invoke<我的世界服务器查询结果>('query_minecraft_server', {
    request: {
      address: request.address.trim(),
      edition: request.edition ?? 'auto',
      timeout: request.timeout ?? 3,
    },
  })
}
