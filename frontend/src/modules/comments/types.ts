export interface CommentUser {
  id: string
  username: string
  nickname: string | null
}

export interface ReplyToUser extends CommentUser {
  guest_name: string | null
}

export interface CommentRecord {
  id: string
  article_id?: string
  user_id?: string | null
  parent_id?: string | null
  content: string
  status?: string
  user: CommentUser | null
  guest_name: string | null
  created_at: string
  like_count: number
  is_liked: boolean
  reply_to_user: ReplyToUser | null
  replies: CommentRecord[]
}

export interface CreateCommentPayload {
  article_id: string
  content: string
  guest_name?: string
  parent_id?: string
}
