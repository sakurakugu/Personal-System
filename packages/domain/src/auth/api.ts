import api from '@personal-system/api'
import type {
  DeviceSessionInfo,
  AuthUser,
  DeviceLoginResponse,
  LoginPayload,
  ProfileUpdatePayload,
  RegisterPayload,
  WidgetTokenIssuePayload,
} from './types'

export async function 登录(payload: LoginPayload): Promise<void> {
  await api.post('/auth/login', payload)
}

export async function 注册(payload: RegisterPayload): Promise<AuthUser> {
  const { data } = await api.post<AuthUser>('/auth/register', payload)
  return data
}

export async function 获取当前用户(): Promise<AuthUser> {
  const { data } = await api.get<AuthUser>('/users/me')
  return data
}

export async function 退出登录(): Promise<void> {
  await api.post('/auth/logout')
}

export async function 获取设备会话列表(): Promise<DeviceSessionInfo[]> {
  const { data } = await api.get<DeviceSessionInfo[]>('/auth/device/sessions')
  return data
}

export async function 撤销设备会话(sessionId: string): Promise<void> {
  await api.delete(`/auth/device/sessions/${sessionId}`)
}

export async function 撤销所有设备会话(): Promise<void> {
  await api.delete('/auth/device/sessions')
}

export async function 签发小工具令牌(payload: WidgetTokenIssuePayload): Promise<DeviceLoginResponse> {
  const { data } = await api.post<DeviceLoginResponse>('/auth/device/widget-token', payload)
  return data
}

export async function 更新当前用户(payload: ProfileUpdatePayload): Promise<AuthUser> {
  const { data } = await api.patch<AuthUser>('/users/me', payload)
  return data
}

export async function 修改当前用户密码(currentPassword: string, newPassword: string): Promise<void> {
  await api.patch('/users/me/password', {
    current_password: currentPassword,
    new_password: newPassword,
  })
}

export async function 删除当前用户账号(password: string): Promise<void> {
  await api.delete('/users/me/account', {
    params: { password },
  })
}
