import api from '@personal-system/api'
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

export async function 获取所有文章元数据(): Promise<ArticleMetaRecord[]> {
  const { data } = await api.get<ArticleMetaRecord[]>('/articles/all-meta')
  return data
}

export async function 获取文章列表(page = 1, query: ArticleQuery = {}): Promise<ArticleListResponse> {
  const { data } = await api.get<ArticleListResponse>('/articles', {
    params: {
      page,
      page_size: DEFAULT_PAGE_SIZE,
      ...query,
    },
  })
  return data
}

export async function 根据路径获取文章(slug: string): Promise<ArticleRecord> {
  const { data } = await api.get<ArticleRecord>(`/articles/${slug}`)
  return data
}

export async function 获取相关文章(slug: string): Promise<ArticleRelatedResponse> {
  const { data } = await api.get<ArticleRelatedResponse>(`/articles/${slug}/related`)
  return data
}

export async function 点赞文章(slug: string): Promise<ArticleLikeResult> {
  const { data } = await api.post<ArticleLikeResult>(`/articles/${slug}/like`)
  return data
}

export async function 取消点赞文章(slug: string): Promise<ArticleLikeResult> {
  const { data } = await api.delete<ArticleLikeResult>(`/articles/${slug}/like`)
  return data
}

export async function 获取我的文章列表(
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

export async function 根据ID获取我的文章(id: string, isDeleted = false): Promise<ArticleRecord> {
  const { data } = await api.get<ArticleRecord>(`/articles/my/${id}`, {
    params: {
      is_deleted: String(isDeleted),
    },
  })
  return data
}

export async function 获取文章图片(articleId: string): Promise<ArticleImageRecord[]> {
  const { data } = await api.get<ArticleImageRecord[]>(`/articles/my/${articleId}/images`)
  return data
}

export async function 创建文章(payload: ArticleEditorPayload): Promise<ArticleRecord> {
  const { data } = await api.post<ArticleRecord>('/articles', payload)
  return data
}

export async function 创建文章草稿(payload?: Partial<ArticleDraftPayload>): Promise<ArticleRecord> {
  const { data } = await api.post<ArticleRecord>('/articles/draft', payload ?? {})
  return data
}

export async function 更新文章(id: string, payload: ArticleUpdatePayload): Promise<ArticleRecord> {
  const { data } = await api.patch<ArticleRecord>(`/articles/${id}`, payload)
  return data
}

export async function 上传文章图片(articleId: string, file: File): Promise<ArticleImageRecord> {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await api.post<ArticleImageRecord>(`/articles/${articleId}/images`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return data
}

export async function 删除文章(id: string, permanent = false): Promise<void> {
  await api.delete(`/articles/${id}`, {
    params: {
      permanent: String(permanent),
    },
  })
}

export async function 恢复文章(id: string): Promise<ArticleRecord> {
  const { data } = await api.post<ArticleRecord>(`/articles/${id}/restore`)
  return data
}

export async function 获取分类列表(): Promise<CategoryRecord[]> {
  const { data } = await api.get<CategoryRecord[]>('/categories')
  return data
}

export async function 创建分类(name: string): Promise<CategoryRecord> {
  const { data } = await api.post<CategoryRecord>('/categories', { name })
  return data
}

export async function 获取标签列表(): Promise<TagRecord[]> {
  const { data } = await api.get<TagRecord[]>('/tags')
  return data
}

export async function 创建标签(name: string): Promise<TagRecord> {
  const { data } = await api.post<TagRecord>('/tags', { name })
  return data
}
