import api from '@personal-system/api'
import type {
  MomentDraft,
  MomentImageRecord,
  MomentLikeResult,
  MomentListResponse,
  MomentPayload,
  MomentViewResult,
  PublishedMoment,
  UserMoment,
} from './types'

const DEFAULT_PAGE_SIZE = 10

export async function 获取已发布动态(page = 1, pageSize = DEFAULT_PAGE_SIZE): Promise<MomentListResponse<PublishedMoment>> {
  const { data } = await api.get<MomentListResponse<PublishedMoment>>('/moments', {
    params: {
      page,
      page_size: pageSize,
    },
  })
  return data
}

export async function 获取我的动态(
  page = 1,
  pageSize = DEFAULT_PAGE_SIZE,
  isDeleted = false,
): Promise<MomentListResponse<UserMoment>> {
  const { data } = await api.get<MomentListResponse<UserMoment>>('/moments/my/list', {
    params: {
      page,
      page_size: pageSize,
      is_deleted: String(isDeleted),
    },
  })
  return data
}

export async function 获取动态草稿(): Promise<MomentDraft | null> {
  const { data } = await api.get<MomentDraft | null>('/moments/draft')
  return data
}

export async function 保存动态草稿(payload: MomentPayload): Promise<MomentDraft> {
  const { data } = await api.put<MomentDraft>('/moments/draft', payload)
  return data
}

export async function 获取动态图片(momentId: string): Promise<MomentImageRecord[]> {
  const { data } = await api.get<MomentImageRecord[]>(`/moments/${momentId}/images`)
  return data
}

export async function 上传动态图片(momentId: string, file: File): Promise<MomentImageRecord> {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await api.post<MomentImageRecord>(`/moments/${momentId}/images`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return data
}

export async function 重新排序动态图片(momentId: string, imageIds: string[]): Promise<MomentImageRecord[]> {
  const { data } = await api.patch<MomentImageRecord[]>(`/moments/${momentId}/images/order`, {
    image_ids: imageIds,
  })
  return data
}

export async function 删除动态图片(momentId: string, imageId: string): Promise<void> {
  await api.delete(`/moments/${momentId}/images/${imageId}`)
}

export async function 发布动态(payload: MomentPayload): Promise<UserMoment> {
  const { data } = await api.post<UserMoment>('/moments/publish', payload)
  return data
}

export async function 更新动态(momentId: string, payload: MomentPayload): Promise<UserMoment> {
  const { data } = await api.put<UserMoment>(`/moments/${momentId}`, payload)
  return data
}

export async function 根据ID获取公开动态(id: string): Promise<PublishedMoment> {
  const { data } = await api.get<PublishedMoment>(`/moments/public/${id}`)
  return data
}

export async function 点赞动态(id: string): Promise<MomentLikeResult> {
  const { data } = await api.post<MomentLikeResult>(`/moments/${id}/like`)
  return data
}

export async function 取消点赞动态(id: string): Promise<MomentLikeResult> {
  const { data } = await api.delete<MomentLikeResult>(`/moments/${id}/like`)
  return data
}

export async function 记录动态浏览(id: string): Promise<MomentViewResult> {
  const { data } = await api.post<MomentViewResult>(`/moments/${id}/view`)
  return data
}

export async function 删除动态(id: string, permanent = false): Promise<void> {
  await api.delete(`/moments/${id}`, {
    params: {
      permanent: String(permanent),
    },
  })
}

export async function 恢复动态(id: string): Promise<UserMoment> {
  const { data } = await api.post<UserMoment>(`/moments/${id}/restore`)
  return data
}
