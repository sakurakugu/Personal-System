import api from '../../shared/api'
import type { AuthUserRole } from './types'

export interface DeveloperLoginAction {
  role: AuthUserRole
  label: string
}

export const developerLoginActions: DeveloperLoginAction[] = [
  { role: 'super_admin', label: '超级管理员登录' },
  { role: 'admin', label: '管理员登录' },
  { role: 'user', label: '普通用户登录' },
]

export async function loginByDeveloperShortcut(role: AuthUserRole): Promise<void> {
  await api.post(`/auth/dev-login/${role}`)
}

