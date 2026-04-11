import type { FileItem } from '../files/types'

export type CollectionType = 'link' | 'text' | 'image' | 'file'
export type CollectionStatus = 'inbox' | 'processing' | 'ready' | 'archived' | 'dropped'
export interface CollectionAssetPayload {
  file_id: string
  sort_order: number
}

export interface CollectionAssetRecord {
  id: string
  file_id: string
  sort_order: number
  created_at: string
  file: FileItem
}

export interface CollectionRecord {
  id: string
  type: CollectionType
  title: string | null
  content_text: string | null
  note: string | null
  status: CollectionStatus
  tags: string[] | null
  assets: CollectionAssetRecord[]
  archived_at: string | null
  created_at: string
  updated_at: string
}

export interface CollectionTagStat {
  name: string
  count: number
}

export interface CollectionListResponse {
  items: CollectionRecord[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface CollectionPayload {
  type: CollectionType
  title?: string | null
  content_text?: string | null
  note?: string | null
  status?: CollectionStatus
  tags?: string[] | null
  assets?: CollectionAssetPayload[] | null
}

export interface CollectionListQuery {
  page?: number
  page_size?: number
  status?: CollectionStatus | ''
  type?: CollectionType | ''
  tag?: string
  keyword?: string
}

export interface CollectionBatchStatusPayload {
  ids: string[]
  status: CollectionStatus
}

export interface CollectionConvertResult {
  collection_id: string
  target_type: 'article' | 'moment_draft' | 'todo'
  target_id: string
  message: string
}
