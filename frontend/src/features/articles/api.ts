import api from '../../utils/api'
import type {
  ArticleEditorPayload,
  ArticleListResponse,
  ArticleQuery,
  ArticleRecord,
  CategoryRecord,
  TagRecord,
} from './types'

const DEFAULT_PAGE_SIZE = 10

export async function fetchArticleList(page = 1, query: ArticleQuery = {}): Promise<ArticleListResponse> {
  const { data } = await api.get<ArticleListResponse>('/articles', {
    params: {
      page,
      page_size: DEFAULT_PAGE_SIZE,
      ...query,
    },
  })
  return data
}

export async function fetchArticleBySlug(slug: string): Promise<ArticleRecord> {
  const { data } = await api.get<ArticleRecord>(`/articles/${slug}`)
  return data
}

export async function fetchMyArticleList(page = 1, pageSize = DEFAULT_PAGE_SIZE): Promise<ArticleListResponse> {
  const { data } = await api.get<ArticleListResponse>('/articles/my/list', {
    params: {
      page,
      page_size: pageSize,
    },
  })
  return data
}

export async function fetchMyArticleById(id: string): Promise<ArticleRecord> {
  const { data } = await api.get<ArticleRecord>(`/articles/my/${id}`)
  return data
}

export async function createArticle(payload: ArticleEditorPayload): Promise<ArticleRecord> {
  const { data } = await api.post<ArticleRecord>('/articles', payload)
  return data
}

export async function updateArticle(id: string, payload: ArticleEditorPayload): Promise<ArticleRecord> {
  const { data } = await api.patch<ArticleRecord>(`/articles/${id}`, payload)
  return data
}

export async function deleteArticle(id: string): Promise<void> {
  await api.delete(`/articles/${id}`)
}

export async function fetchCategories(): Promise<CategoryRecord[]> {
  const { data } = await api.get<CategoryRecord[]>('/categories')
  return data
}

export async function fetchTags(): Promise<TagRecord[]> {
  const { data } = await api.get<TagRecord[]>('/tags')
  return data
}
