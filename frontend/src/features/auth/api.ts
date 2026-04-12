import api from '../../utils/api'
import type {
  AuthUser,
  LoginPayload,
  ProfileUpdatePayload,
  RegisterPayload,
} from './types'

export async function login(payload: LoginPayload): Promise<void> {
  await api.post('/auth/login', payload)
}

export async function register(payload: RegisterPayload): Promise<AuthUser> {
  const { data } = await api.post<AuthUser>('/auth/register', payload)
  return data
}

export async function fetchCurrentUser(): Promise<AuthUser> {
  const { data } = await api.get<AuthUser>('/users/me')
  return data
}

export async function logout(): Promise<void> {
  await api.post('/auth/logout')
}

export async function updateCurrentUser(payload: ProfileUpdatePayload): Promise<AuthUser> {
  const { data } = await api.patch<AuthUser>('/users/me', payload)
  return data
}

export async function changeCurrentUserPassword(currentPassword: string, newPassword: string): Promise<void> {
  await api.patch('/users/me/password', {
    current_password: currentPassword,
    new_password: newPassword,
  })
}

export async function deleteCurrentUserAccount(password: string): Promise<void> {
  await api.delete('/users/me/account', {
    params: { password },
  })
}
