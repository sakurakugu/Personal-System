import type { AuthUserRole } from '@personal-system/domain/auth'

export interface DeveloperLoginAction {
  role: AuthUserRole
  label: string
}

export const developerLoginActions: DeveloperLoginAction[] = [
  { role: 'super_admin', label: '超级管理员登录' },
  { role: 'admin', label: '管理员登录' },
  { role: 'user', label: '普通用户登录' },
]
