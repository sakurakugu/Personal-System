export interface MomentImageRecord {
  id: string
  original_name: string
  url: string
  preview_url: string
  thumbnail_url: string | null
  size: number
  mime_type: string
  sort_order: number
  created_at: string
}

export interface MomentAuthor {
  id: string
  username: string
  nickname: string | null
  avatar_url: string | null
}

export interface MomentListItem {
  id: string
  title: string | null
  content: string
  images: MomentImageRecord[]
  view_count: number
  like_count: number
  liked: boolean
  published_at: string | null
  user?: MomentAuthor
}

export interface PublishedMoment extends MomentListItem {
  user: MomentAuthor
}

export interface UserMoment extends MomentListItem {
  is_published: boolean
  user_id: string
  created_at: string
  updated_at: string
}

export interface MomentDraft {
  id: string
  title: string | null
  content: string
  images: MomentImageRecord[]
  updated_at: string
}

export interface MomentListResponse<T extends MomentListItem> {
  items: T[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface MomentPayload {
  title?: string
  content: string
}

export interface MomentLikeResult {
  like_count: number
  changed: boolean
  liked: boolean
}

export interface MomentViewResult {
  view_count: number
  changed: boolean
}
