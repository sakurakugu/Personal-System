import api from '@personal-system/api'
export { developerLoginActions, type DeveloperLoginAction } from '@personal-system/module-auth'
import type { AuthUserRole, DeviceLoginResponse } from '@personal-system/domain/auth'
import { setStoredDesktopAuthToken } from '@/shared/auth/device-token'

export async function loginByDeveloperShortcut(role: AuthUserRole): Promise<void> {
  const { data } = await api.post<DeviceLoginResponse>(`/auth/device/dev-login/${role}`, {
    device_name: 'Personal System Desktop',
    device_type: 'desktop',
    scope: 'full_client',
    client_version: '0.1.0',
    platform: navigator.platform || 'desktop',
  })
  await setStoredDesktopAuthToken(data.token)
}
