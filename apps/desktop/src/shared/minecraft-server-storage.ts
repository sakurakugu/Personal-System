import { invoke } from '@tauri-apps/api/core'

export type 我的世界服务器记录 = {
  address: string
  edition: 'auto' | 'java' | 'bedrock'
}

export type 我的世界服务器存储数据 = {
  favorites: 我的世界服务器记录[]
  history: 我的世界服务器记录[]
}

export async function 读取我的世界服务器存储(): Promise<我的世界服务器存储数据> {
  return invoke<我的世界服务器存储数据>('read_minecraft_server_storage')
}

export async function 写入我的世界服务器存储(data: 我的世界服务器存储数据): Promise<void> {
  await invoke('write_minecraft_server_storage', {
    data: {
      favorites: data.favorites,
      history: data.history,
    },
  })
}
