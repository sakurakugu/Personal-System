import {
  获取当前用户,
  登录 as 请求登录,
  退出登录 as 请求退出登录,
} from '../api'
import type {
  AuthSessionDriver,
  AuthUser,
  LoginPayload,
} from '../types'

export const browserSessionDriver: AuthSessionDriver = {
  mode: 'browser-session',
  async 登录(payload: LoginPayload): Promise<AuthUser | null> {
    await 请求登录(payload)
    return null
  },
  async 登出(): Promise<void> {
    await 请求退出登录()
  },
  async 获取当前用户(): Promise<AuthUser> {
    return await 获取当前用户()
  },
}
