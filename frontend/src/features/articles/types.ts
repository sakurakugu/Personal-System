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
}

export interface TagRecord {
  id: string
  name: string
  slug: string
}

export type ArticleStatus = 'draft' | 'published'

export interface ArticleRecord {
  id: string
  title: string
  slug: string
  content: string
  excerpt: string | null
  cover_url: string | null
  status: ArticleStatus
  view_count: number
  author: ArticleAuthor
  category: CategoryRecord | null
  tags: TagRecord[]
  published_at: string | null
  created_at: string
  updated_at: string
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
