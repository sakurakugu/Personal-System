import api from '@personal-system/api'
export { developerLoginActions, type DeveloperLoginAction } from '@personal-system/module-auth/dev-login'
import type { AuthUserRole } from '@personal-system/domain/auth'

export async function loginByDeveloperShortcut(role: AuthUserRole): Promise<void> {
  await api.post(`/auth/dev-login/${role}`)
}
