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

export type AuthSessionMode = 'browser-session' | 'device-token'
export type DeviceSessionType = 'desktop' | 'widget' | 'phone' | 'other'
export type DeviceSessionScope = 'full_client' | 'widget_basic'

export interface DeviceSessionInfo {
  id: string
  user_id: string
  device_name: string
  device_type: DeviceSessionType
  scope: DeviceSessionScope
  client_version: string | null
  platform: string | null
  last_ip: string | null
  last_user_agent: string | null
  expires_at: string
  last_used_at: string
  created_at: string
  revoked_at: string | null
  is_current?: boolean
}

export interface DeviceLoginPayload extends LoginPayload {
  device_name: string
  device_type: DeviceSessionType
  scope: DeviceSessionScope
  client_version?: string
  platform?: string
}

export interface DeviceLoginResponse {
  token: string
  expires_at: string
  session: DeviceSessionInfo
  user: AuthUser
}

export interface RegisterPayload {
  username: string
  email: string
  password: string
  nickname?: string
}

export interface AuthSessionDriver {
  mode: AuthSessionMode
  login: (payload: LoginPayload) => Promise<AuthUser | null | void>
  logout: () => Promise<void>
  fetchCurrentUser: () => Promise<AuthUser>
  clearSession?: () => void | Promise<void>
}

export interface ProfileUpdatePayload {
  username?: string
  nickname?: string | null
  email?: string
  avatar_url?: string | null
  bio?: string | null
  settings?: Partial<AuthUserSettings>
}
