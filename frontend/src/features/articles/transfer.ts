import type {
  ArticleAuthor,
  ArticleRecord,
  ArticleStatus,
  CategoryRecord,
  TagRecord,
} from './types'

export interface ArticleTransferCategory {
  name: string
  slug: string
}

export interface ArticleTransferTag {
  name: string
  slug: string
}

export interface ArticleTransferItem {
  source_article_id: string
  title: string
  slug: string
  content: string
  excerpt?: string
  cover_url?: string
  status: ArticleStatus
  view_count: number
  author: ArticleAuthor
  category: ArticleTransferCategory | null
  tags: ArticleTransferTag[]
  published_at?: string
  created_at: string
  last_edited_at: string
  updated_at: string
}

export interface ArticleTransferPayload {
  version: number
  exported_at: string
  total: number
  articles: ArticleTransferItem[]
}

function toTransferCategory(category: CategoryRecord | null): ArticleTransferCategory | null {
  if (!category) {
    return null
  }
  return {
    name: category.name,
    slug: category.slug,
  }
}

function toTransferTags(tags: TagRecord[]): ArticleTransferTag[] {
  return tags.map((tag) => ({
    name: tag.name,
    slug: tag.slug,
  }))
}

export function toArticleTransferItem(article: ArticleRecord): ArticleTransferItem {
  return {
    source_article_id: article.id,
    title: article.title,
    slug: article.slug,
    content: article.content,
    excerpt: article.excerpt ?? undefined,
    cover_url: article.cover_url ?? undefined,
    status: article.status,
    view_count: article.view_count,
    author: article.author,
    category: toTransferCategory(article.category),
    tags: toTransferTags(article.tags),
    published_at: article.published_at ?? undefined,
    created_at: article.created_at,
    last_edited_at: article.last_edited_at,
    updated_at: article.updated_at,
  }
}

export function buildArticleTransferPayload(version: number, articles: ArticleRecord[]): ArticleTransferPayload {
  return {
    version,
    exported_at: new Date().toISOString(),
    total: articles.length,
    articles: articles.map((article) => toArticleTransferItem(article)),
  }
}
