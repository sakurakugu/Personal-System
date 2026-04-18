import api from '../../shared/api'
import type { CommentRecord, CreateCommentPayload } from './types'

export async function fetchComments(articleId: string): Promise<CommentRecord[]> {
  const { data } = await api.get<CommentRecord[]>('/comments', {
    params: {
      article_id: articleId,
    },
  })
  return data
}

export async function createComment(payload: CreateCommentPayload): Promise<CommentRecord> {
  const { data } = await api.post<CommentRecord>('/comments', payload)
  return data
}

export async function deleteComment(id: string): Promise<void> {
  await api.delete(`/comments/${id}`)
}

export async function likeComment(id: string): Promise<void> {
  await api.post(`/comments/${id}/like`)
}

export async function unlikeComment(id: string): Promise<void> {
  await api.delete(`/comments/${id}/like`)
}

