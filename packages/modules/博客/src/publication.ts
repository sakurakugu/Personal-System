import api from '@personal-system/api'
import type { ArticleRecord } from '@personal-system/module-articles'

export type BlogVisibility = 'public' | 'login_required'
export type BlogManageState = 'all' | 'published' | 'unpublished' | 'changed'

export interface BlogManageItem {
  id: string
  title: string
  word_count: number
  revision: number
  has_unpublished_changes: boolean
  publication: {
    title: string
    word_count: number
    slug: string
    visibility: BlogVisibility
    is_published: boolean
    version: number
    published_at: string
    updated_at: string
    view_count: number
    like_count: number
  } | null
}

export interface BlogManageResponse {
  items: BlogManageItem[]
  total: number
  pages: number
}

export async function 获取博客管理列表(
  page: number,
  state: BlogManageState,
  search: string,
): Promise<BlogManageResponse> {
  const { data } = await api.get<BlogManageResponse>('/articles/blog/manage', {
    params: { page, page_size: 10, state, search },
  })
  return data
}

export async function 获取博客发布快照(id: string): Promise<ArticleRecord> {
  const { data } = await api.get<ArticleRecord>(`/articles/blog/${id}/snapshot`)
  return data
}

export async function 发布博客文章(
  id: string,
  revision: number,
  visibility: BlogVisibility,
): Promise<BlogManageItem> {
  const { data } = await api.post<BlogManageItem>(`/articles/blog/${id}/publish`, {
    expected_revision: revision,
    visibility,
  })
  return data
}

export async function 设置博客可见性(id: string, visibility: BlogVisibility): Promise<void> {
  await api.patch(`/articles/blog/${id}/visibility`, { visibility })
}

export async function 撤下博客发布(id: string): Promise<void> {
  await api.post(`/articles/blog/${id}/withdraw`)
}
