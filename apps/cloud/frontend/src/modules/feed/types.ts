import type { MomentImageRecord } from '@personal-system/modules/moments'
import type { ArticleAuthor, CategoryRecord, TagRecord } from '@personal-system/modules/articles'

export interface FeedArticleRecord {
  id: string
  title: string
  slug: string
  excerpt: string | null
  cover_url: string | null
  status: 'private' | 'login_required' | 'public'
  view_count: number
  like_count: number
  word_count: number
  author: ArticleAuthor
  category: CategoryRecord | null
  tags: TagRecord[]
  published_at: string | null
  created_at: string
  last_edited_at: string
  pinned?: boolean
}

export interface FeedMomentAuthor {
  id: string
  username: string
  nickname: string | null
  avatar_url: string | null
}

export interface FeedMomentRecord {
  id: string
  title: string | null
  content: string
  images: MomentImageRecord[]
  view_count: number
  like_count: number
  liked: boolean
  published_at: string
  last_edited_at: string
  user: FeedMomentAuthor
}

export type FeedItemRecord =
  | {
    type: 'article'
    source_id: string
    published_at: string
    article: FeedArticleRecord
    moment?: never
  }
  | {
    type: 'moment'
    source_id: string
    published_at: string
    article?: never
    moment: FeedMomentRecord
  }

export interface FeedQuery {
  search?: string
  category?: string
  tag?: string
  include_own_private?: boolean
}

export interface FeedListResponse {
  items: FeedItemRecord[]
  total: number
  page: number
  page_size: number
  pages: number
}
