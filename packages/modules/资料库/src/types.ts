import type { FileItem } from './files-types'

export type MaterialType = 'link' | 'text' | 'image' | 'file'
export type MaterialStatus = 'active' | 'archived'

export interface MaterialAssetPayload {
  file_id: string
  sort_order: number
}

export interface MaterialAssetRecord {
  id: string
  file_id: string
  sort_order: number
  created_at: string
  file: FileItem
}

export interface MaterialRecord {
  id: string
  type: MaterialType
  title: string | null
  content_text: string | null
  note: string | null
  status: MaterialStatus
  tags: string[] | null
  assets: MaterialAssetRecord[]
  archived_at: string | null
  is_deleted: boolean
  deleted_at: string | null
  created_at: string
  updated_at: string
}

export interface MaterialTagStat {
  name: string
  count: number
}

export interface MaterialListResponse {
  items: MaterialRecord[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface MaterialPayload {
  type: MaterialType
  title?: string | null
  content_text?: string | null
  note?: string | null
  status?: MaterialStatus
  tags?: string[] | null
  assets?: MaterialAssetPayload[] | null
}

export interface MaterialListQuery {
  page?: number
  page_size?: number
  status?: MaterialStatus | ''
  type?: MaterialType | ''
  tag?: string
  keyword?: string
  is_deleted?: boolean
}

export interface MaterialBatchStatusPayload {
  ids: string[]
  status: MaterialStatus
}
