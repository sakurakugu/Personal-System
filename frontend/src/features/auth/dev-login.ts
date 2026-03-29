import api from '../../utils/api'
import type { AuthTokens, AuthUserRole } from './types'

export interface DeveloperLoginAction {
  role: AuthUserRole
  label: string
}

export const developerLoginActions: DeveloperLoginAction[] = [
  { role: 'super_admin', label: '超级管理员登录' },
  { role: 'admin', label: '管理员登录' },
  { role: 'user', label: '普通用户登录' },
]

export async function loginByDeveloperShortcut(role: AuthUserRole): Promise<AuthTokens> {
  const { data } = await api.post<AuthTokens>(`/auth/dev-login/${role}`)
  return data
}
