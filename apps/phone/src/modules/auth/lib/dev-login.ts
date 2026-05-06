import api from '@personal-system/api'
export { developerLoginActions, type DeveloperLoginAction } from '@personal-system/modules/auth'
import type { AuthUserRole } from '@personal-system/domain/auth'
import type { DeviceLoginResponse } from '@personal-system/domain/auth'
import { setStoredPhoneAuthToken } from '@/shared/auth/device-token'

export async function loginByDeveloperShortcut(role: AuthUserRole): Promise<void> {
  const { data } = await api.post<DeviceLoginResponse>(`/auth/device/dev-login/${role}`, {
    device_name: 'Personal System Phone',
    device_type: 'phone',
    scope: 'full_client',
    platform: navigator.platform || 'phone',
  })
  await setStoredPhoneAuthToken(data.token)
}
