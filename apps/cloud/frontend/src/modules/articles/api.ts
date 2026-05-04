import api from '../../shared/api'
import type {
  ArticleDraftPayload,
  ArticleImageRecord,
  ArticleLikeResult,
  ArticleEditorPayload,
  ArticleListResponse,
  ArticleMetaRecord,
  ArticleQuery,
  ArticleRecord,
  ArticleRelatedResponse,
  ArticleUpdatePayload,
  CategoryRecord,
  TagRecord,
} from './types'

const DEFAULT_PAGE_SIZE = 10

export async function fetchAllArticleMeta(): Promise<ArticleMetaRecord[]> {
  const { data } = await api.get<ArticleMetaRecord[]>('/articles/all-meta')
  return data
}

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

export async function fetchArticleRelated(slug: string): Promise<ArticleRelatedResponse> {
  const { data } = await api.get<ArticleRelatedResponse>(`/articles/${slug}/related`)
  return data
}

export async function likeArticle(slug: string): Promise<ArticleLikeResult> {
  const { data } = await api.post<ArticleLikeResult>(`/articles/${slug}/like`)
  return data
}

export async function unlikeArticle(slug: string): Promise<ArticleLikeResult> {
  const { data } = await api.delete<ArticleLikeResult>(`/articles/${slug}/like`)
  return data
}

export async function fetchMyArticleList(
  page = 1,
  pageSize = DEFAULT_PAGE_SIZE,
  isDeleted = false,
): Promise<ArticleListResponse> {
  const { data } = await api.get<ArticleListResponse>('/articles/my/list', {
    params: {
      page,
      page_size: pageSize,
      is_deleted: String(isDeleted),
    },
  })
  return data
}

export async function fetchMyArticleById(id: string, isDeleted = false): Promise<ArticleRecord> {
  const { data } = await api.get<ArticleRecord>(`/articles/my/${id}`, {
    params: {
      is_deleted: String(isDeleted),
    },
  })
  return data
}

export async function fetchArticleImages(articleId: string): Promise<ArticleImageRecord[]> {
  const { data } = await api.get<ArticleImageRecord[]>(`/articles/my/${articleId}/images`)
  return data
}

export async function createArticle(payload: ArticleEditorPayload): Promise<ArticleRecord> {
  const { data } = await api.post<ArticleRecord>('/articles', payload)
  return data
}

export async function createArticleDraft(payload?: Partial<ArticleDraftPayload>): Promise<ArticleRecord> {
  const { data } = await api.post<ArticleRecord>('/articles/draft', payload ?? {})
  return data
}

export async function updateArticle(id: string, payload: ArticleUpdatePayload): Promise<ArticleRecord> {
  const { data } = await api.patch<ArticleRecord>(`/articles/${id}`, payload)
  return data
}

export async function uploadArticleImage(articleId: string, file: File): Promise<ArticleImageRecord> {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await api.post<ArticleImageRecord>(`/articles/${articleId}/images`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return data
}

export async function deleteArticle(id: string, permanent = false): Promise<void> {
  await api.delete(`/articles/${id}`, {
    params: {
      permanent: String(permanent),
    },
  })
}

export async function restoreArticle(id: string): Promise<ArticleRecord> {
  const { data } = await api.post<ArticleRecord>(`/articles/${id}/restore`)
  return data
}

export async function fetchCategories(): Promise<CategoryRecord[]> {
  const { data } = await api.get<CategoryRecord[]>('/categories')
  return data
}

export async function createCategory(name: string): Promise<CategoryRecord> {
  const { data } = await api.post<CategoryRecord>('/categories', { name })
  return data
}

export async function fetchTags(): Promise<TagRecord[]> {
  const { data } = await api.get<TagRecord[]>('/tags')
  return data
}

export async function createTag(name: string): Promise<TagRecord> {
  const { data } = await api.post<TagRecord>('/tags', { name })
  return data
}
