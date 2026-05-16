import api from '@personal-system/api'
import type {
  AuthSessionDriver,
  AuthUser,
  DeviceLoginPayload,
  DeviceLoginResponse,
  DeviceSessionScope,
  DeviceSessionType,
  LoginPayload,
} from '../types'

export interface DeviceTokenSessionDriverOptions {
  deviceName: string
  deviceType: DeviceSessionType
  scope: DeviceSessionScope
  clientVersion?: string
  platform?: string
  persistToken: (token: string | null) => void | Promise<void>
}

function buildDeviceLoginPayload(
  payload: LoginPayload,
  options: DeviceTokenSessionDriverOptions,
): DeviceLoginPayload {
  return {
    username: payload.username,
    password: payload.password,
    device_name: options.deviceName,
    device_type: options.deviceType,
    scope: options.scope,
    client_version: options.clientVersion,
    platform: options.platform,
  }
}

export function 创建设备令牌会话驱动(
  options: DeviceTokenSessionDriverOptions,
): AuthSessionDriver {
  return {
    mode: 'device-token',
    async login(payload: LoginPayload): Promise<AuthUser> {
      const { data } = await api.post<DeviceLoginResponse>(
        '/auth/device/login',
        buildDeviceLoginPayload(payload, options),
      )
      await options.persistToken(data.token)
      return data.user
    },
    async logout(): Promise<void> {
      try {
        await api.post('/auth/device/logout')
      } finally {
        await options.persistToken(null)
      }
    },
    async fetchCurrentUser(): Promise<AuthUser> {
      const { data } = await api.get<AuthUser>('/users/me')
      return data
    },
    async clearSession(): Promise<void> {
      await options.persistToken(null)
    },
  }
}
