import api from '@personal-system/api'
export { 开发者登录操作, type DeveloperLoginAction } from '@personal-system/module-auth/dev-login'
import type { AuthUserRole } from '@personal-system/domain/auth'

export async function 开发者快捷登录(role: AuthUserRole): Promise<void> {
  await api.post(`/auth/dev-login/${role}`)
}
