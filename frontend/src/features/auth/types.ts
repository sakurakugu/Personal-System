export type AuthUserRole = 'user' | 'admin' | 'super_admin'

export interface AuthUser {
  id: string
  username: string
  nickname: string | null
  email: string
  role: AuthUserRole
  avatar_url: string | null
  bio: string | null
  show_private_articles_on_home: boolean
  is_active: boolean
  created_at: string
}

export interface AuthTokens {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface LoginPayload {
  username: string
  password: string
}

export interface RegisterPayload {
  username: string
  email: string
  password: string
  nickname?: string
}

export interface ProfileUpdatePayload {
  username?: string
  nickname?: string | null
  email?: string
  avatar_url?: string | null
  bio?: string | null
  show_private_articles_on_home?: boolean
}
