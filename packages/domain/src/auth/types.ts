export type AuthUserRole = 'user' | 'admin' | 'super_admin'

export interface AuthUserSettings {
  show_private_articles_on_home: boolean
}

export interface AuthUser {
  id: string
  username: string
  nickname: string | null
  email: string
  role: AuthUserRole
  avatar_url: string | null
  bio: string | null
  settings: AuthUserSettings
  is_active: boolean
  created_at: string
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
  settings?: Partial<AuthUserSettings>
}
