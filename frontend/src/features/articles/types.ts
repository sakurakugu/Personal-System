export interface ArticleAuthor {
  id: string
  username: string
  nickname: string | null
  avatar_url: string | null
}

export interface CategoryRecord {
  id: string
  name: string
  slug: string
  article_count?: number
}

export interface TagRecord {
  id: string
  name: string
  slug: string
}

export type ArticleStatus = 'private' | 'login_required' | 'public'

export interface ArticleMetaRecord {
  id: string
  title: string
  slug: string
  published_at: string | null
  view_count: number
  tags: TagRecord[]
  category: CategoryRecord | null
}

export interface ArticleRelatedResponse {
  related: ArticleMetaRecord[]
  random: ArticleMetaRecord[]
}

export interface ArticleRecord {
  id: string
  title: string
  slug: string
  content: string
  excerpt: string | null
  cover_url: string | null
  status: ArticleStatus
  view_count: number
  word_count: number
  author: ArticleAuthor
  category: CategoryRecord | null
  tags: TagRecord[]
  published_at: string | null
  created_at: string
  last_edited_at: string
  updated_at: string
  pinned?: boolean
}

export interface ArticleListResponse {
  items: ArticleRecord[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface ArticleQuery {
  search?: string
  category?: string
  sort?: string
}

export interface ArticleEditorPayload {
  title: string
  content: string
  excerpt: string
  cover_url: string
  status: ArticleStatus
  category_id: string | null
  tag_ids: string[]
}

export type ArticleUpdatePayload = Partial<ArticleEditorPayload>

export interface ArticleDraftPayload {
  title: string
  content: string
  excerpt: string
  cover_url: string
  category_id: string | null
  tag_ids: string[]
}

export interface ArticleImageRecord {
  id: string
  original_name: string
  url: string
  preview_url: string
  thumbnail_url: string | null
  size: number
  mime_type: string
  created_at: string
}
