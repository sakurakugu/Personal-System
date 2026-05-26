import type { FileItem } from '@personal-system/module-files'

export type MediaType = 'game' | 'novel' | 'book' | 'anime' | 'comic' | 'movie' | 'tv' | 'music' | 'other'
export type MediaStatus = 'planned' | 'doing' | 'done' | 'paused' | 'dropped'

export interface MediaRecord {
  id: string
  title: string
  original_title: string | null
  media_type: MediaType
  status: MediaStatus
  rating: number | null
  creator: string | null
  summary: string | null
  description: string | null
  genres: string[]
  tags: string[]
  cover_file_id: string | null
  cover_file: FileItem | null
  is_visible: boolean
  created_at: string
  updated_at: string
}

export interface MediaFilterStat {
  name: string
  count: number
}

export interface MediaListResponse {
  items: MediaRecord[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface MediaPayload {
  title: string
  original_title?: string | null
  media_type: MediaType
  status: MediaStatus
  rating?: number | null
  creator?: string | null
  summary?: string | null
  description?: string | null
  genres?: string[] | null
  tags?: string[] | null
  cover_file_id?: string | null
  is_visible?: boolean
}

export interface MediaListQuery {
  page?: number
  page_size?: number
  media_type?: MediaType | ''
  status?: MediaStatus | ''
  rating?: number | null
  keyword?: string
  genre?: string
  tag?: string
}
