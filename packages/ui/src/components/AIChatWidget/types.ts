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

export type 聊天请求上下文 = {
  hasAttachments: boolean
}

export type 聊天请求配置 = {
  url: string
  init: RequestInit
  context: 聊天请求上下文
}

export type 聊天请求调整器 = (config: 聊天请求配置) => 聊天请求配置 | Promise<聊天请求配置>
