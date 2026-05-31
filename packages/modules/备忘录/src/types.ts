export type MemoStatus = 'inbox' | 'processed' | 'archived' | 'dropped'
export type MemoSource = 'manual' | 'wechat' | 'web' | 'share' | 'unknown'
export type MemoConvertTarget = 'collection' | 'article' | 'todo'

export interface MemoRecord {
  id: string
  content: string
  status: MemoStatus
  source: MemoSource
  converted_to_type: MemoConvertTarget | null
  converted_to_id: string | null
  archived_at: string | null
  deleted_at: string | null
  created_at: string
  updated_at: string
}

export interface MemoListResponse {
  items: MemoRecord[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface MemoListQuery {
  page?: number
  page_size?: number
  status?: MemoStatus | ''
  source?: MemoSource | ''
  keyword?: string
  is_deleted?: boolean
}

export interface MemoCreatePayload {
  content: string
  source?: MemoSource
}

export interface MemoUpdatePayload {
  content?: string
  status?: MemoStatus
  source?: MemoSource
}

export interface MemoConvertResult {
  memo_id: string
  target_type: MemoConvertTarget
  target_id: string
  message: string
}
