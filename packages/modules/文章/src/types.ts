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
export type ArticleOrganizationState = 'inbox' | 'organized' | 'archived'

export interface ArticleConversion {
  id: string
  target_type: 'todo' | 'material'
  target_id: string
  created_at: string
}

export interface ArticleMetaRecord {
  id: string
  title: string
  slug: string
  published_at: string | null
  view_count: number
  like_count: number
  author: ArticleAuthor
  tags: TagRecord[]
  category: CategoryRecord | null
}

export interface ArticleNavigationRecord {
  title: string
  slug: string
}

export interface ArticleRelatedResponse {
  prev: ArticleNavigationRecord | null
  next: ArticleNavigationRecord | null
  related: ArticleMetaRecord[]
  random: ArticleMetaRecord[]
}

export interface ArticleRecord {
  id: string
  title: string
  slug: string
  content: string
  organization_state: ArticleOrganizationState
  archived_at: string | null
  converted_items: ArticleConversion[]
  excerpt: string | null
  cover_url: string | null
  status: ArticleStatus
  view_count: number
  like_count: number
  liked: boolean
  word_count: number
  author: ArticleAuthor
  category: CategoryRecord | null
  tags: TagRecord[]
  is_deleted: boolean
  deleted_at: string | null
  published_at: string | null
  created_at: string
  last_edited_at: string
  updated_at: string
  revision: number
  has_unpublished_changes: boolean
  pinned?: boolean
}

export interface ArticleLikeResult {
  like_count: number
  changed: boolean
  liked: boolean
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
  is_deleted?: boolean
}

export interface ArticleEditorPayload {
  title: string
  content: string
  excerpt: string
  cover_url: string
  category_id: string | null
  tag_ids: string[]
}

export type ArticleUpdatePayload = Partial<ArticleEditorPayload> & { organization_state?: ArticleOrganizationState }

export interface ArticleDraftPayload {
  organization_state?: ArticleOrganizationState
  title: string
  content: string
  excerpt: string
  cover_url: string
  category_id: string | null
  tag_ids: string[]
}

export interface ArticleConvertTodoPayload {
  title: string
  description: string | null
  start_date?: string | null
  end_date?: string | null
}

export interface ArticleConvertMaterialPayload {
  title: string
  content_text: string | null
  note: string | null
  type: 'text' | 'link'
}

export interface ArticleImageRecord {
  used_by_publication: boolean
  id: string
  original_name: string
  url: string
  preview_url: string
  thumbnail_url: string | null
  size: number
  mime_type: string
  created_at: string
}

export interface ArticleAIRequestPayload {
  title?: string | null
  content: string
  excerpt?: string | null
  category_names: string[]
  tag_names: string[]
}

export interface ArticleAIMetadataSuggestion {
  title: string
  excerpt: string
  category_name: string | null
  tag_names: string[]
  reason: string
}

export interface ArticleAIContentPolishResult {
  content: string
  summary: string
}
