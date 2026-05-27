export type MediaType = 'game' | 'novel' | 'book' | 'anime' | 'comic' | 'movie' | 'tv' | 'music' | 'other'
export type MediaStatus = 'planned' | 'doing' | 'done' | 'paused' | 'dropped'
export type MediaAssetType = 'cover' | 'backdrop' | 'screenshot' | 'logo' | 'other'

export interface MediaAsset {
  id: string
  media_item_id: string
  asset_type: MediaAssetType
  storage_key: string | null
  external_url: string | null
  thumbnail_url: string | null
  source_provider: string | null
  source_asset_id: string | null
  original_name: string | null
  mime_type: string | null
  width: number | null
  height: number | null
  size: number | null
  attribution: string | null
  license: string | null
  is_primary: boolean
  sort_order: number
  url: string | null
  preview_url: string | null
  created_at: string
  updated_at: string
}

export interface MediaExternalSource {
  id: string
  media_item_id: string
  provider: string
  external_id: string
  external_url: string | null
  fetched_at: string
  created_at: string
  updated_at: string
}

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
  personal_tags: string[]
  release_date: string | null
  primary_cover_asset_id: string | null
  primary_cover_asset: MediaAsset | null
  assets: MediaAsset[]
  external_sources: MediaExternalSource[]
  is_visible: boolean
  created_at: string
  updated_at: string
}

export interface MediaFilterStat {
  name: string
  count: number
}

export interface MediaCreatorSuggestion {
  name: string
  count: number
}

export interface MediaListResponse {
  items: MediaRecord[]
  total: number
  page: number
  page_size: number
  pages: number
  all_data_updated_at: string | null
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
  personal_tags?: string[] | null
  release_date?: string | null
  primary_cover_asset_id?: string | null
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
  personal_tag?: string
}

export interface ExternalMediaCandidate {
  provider: string
  external_id: string
  title: string
  original_title: string | null
  media_type: MediaType
  creators: string[]
  summary: string | null
  description: string | null
  genres: string[]
  tags: string[]
  release_date: string | null
  cover_url: string | null
  thumbnail_url: string | null
  external_url: string | null
  raw: Record<string, unknown> | null
}

export interface ExternalMediaSearchResponse {
  items: ExternalMediaCandidate[]
}

export interface ExternalMediaImportPayload {
  provider: string
  external_id: string
  status?: MediaStatus
  rating?: number | null
  is_visible?: boolean
  localize_cover?: boolean
}

export interface ExternalCoverImportPayload {
  external_url: string
  source_provider?: string | null
  source_asset_id?: string | null
  original_name?: string | null
  attribution?: string | null
  license?: string | null
  set_primary?: boolean
}
