import api from '@personal-system/api'
export { 开发者登录操作, type DeveloperLoginAction } from '@personal-system/module-auth'
import type { AuthUserRole } from '@personal-system/domain/auth'
import type { DeviceLoginResponse } from '@personal-system/domain/auth'
import { 设置存储的手机令牌 } from '@/shared/auth/device-token'

export async function 开发者快捷登录(role: AuthUserRole): Promise<void> {
  const { data } = await api.post<DeviceLoginResponse>(`/auth/device/dev-login/${role}`, {
    device_name: 'Personal System Phone',
    device_type: 'phone',
    scope: 'full_client',
    platform: navigator.platform || 'phone',
  })
  await 设置存储的手机令牌(data.token)
}
