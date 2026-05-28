export type 聊天角色 = 'user' | 'assistant' | 'system'
export type 聊天状态 = '空闲' | '请求中' | '失败'

export interface 聊天附件 {
  id: string
  file?: File
  filename: string
  mediaType: string
  size: number
  url?: string
}

export interface 聊天消息 {
  id: string
  role: 聊天角色
  content: string
  createdAt: number
  attachments?: 聊天附件[]
}

export interface 客服信息 {
  name: string
  pictureUrl?: string | null
  isOnline?: boolean
  statusLabel?: string
}
