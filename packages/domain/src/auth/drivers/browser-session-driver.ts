import {
  fetchCurrentUser,
  login as requestLogin,
  logout as requestLogout,
} from '../api'
import type {
  AuthSessionDriver,
  AuthUser,
  LoginPayload,
} from '../types'

export const browserSessionDriver: AuthSessionDriver = {
  mode: 'browser-session',
  async login(payload: LoginPayload): Promise<AuthUser | null> {
    await requestLogin(payload)
    return null
  },
  async logout(): Promise<void> {
    await requestLogout()
  },
  async fetchCurrentUser(): Promise<AuthUser> {
    return await fetchCurrentUser()
  },
}
