import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  changeCurrentUserPassword,
  deleteCurrentUserAccount,
  fetchCurrentUser,
  login as requestLogin,
  refreshToken as requestRefreshToken,
  register as requestRegister,
  updateCurrentUser,
} from '../features/auth/api'
import type { AuthUser, AuthUserRole, ProfileUpdatePayload } from '../features/auth/types'

export const useAuthStore = defineStore('auth', () => {
  const accessToken = ref<string | null>(localStorage.getItem('access_token'))
  const refreshToken = ref<string | null>(localStorage.getItem('refresh_token'))
  const user = ref<AuthUser | null>(null)
  const isLoading = ref(false)
  let restoreTask: Promise<void> | null = null

  const isAuthenticated = computed(() => !!accessToken.value)
  const isSuperAdmin = computed(() => user.value?.role === 'super_admin')
  const isAdmin = computed(() => user.value?.role === 'admin' || user.value?.role === 'super_admin')
  const userRole = computed(() => user.value?.role || 'guest')

  function setTokens(access: string, refresh: string) {
    accessToken.value = access
    refreshToken.value = refresh
    localStorage.setItem('access_token', access)
    localStorage.setItem('refresh_token', refresh)
  }

  async function login(username: string, password: string) {
    const data = await requestLogin({ username, password })
    setTokens(data.access_token, data.refresh_token)
    await fetchUser()
  }

  async function developerLogin(role: AuthUserRole) {
    if (!import.meta.env.DEV) {
      throw new Error('当前环境不支持开发者登录')
    }
    const { loginByDeveloperShortcut } = await import('../features/auth/dev-login')
    const data = await loginByDeveloperShortcut(role)
    setTokens(data.access_token, data.refresh_token)
    await fetchUser()
  }

  async function register(username: string, email: string, password: string, nickname?: string) {
    await requestRegister({ username, email, password, nickname })
  }

  async function fetchUser() {
    if (!accessToken.value) return
    try {
      const data = await fetchCurrentUser()
      user.value = data
    } catch {
      logout()
    }
  }

  function restoreUserIfNeeded(): Promise<void> {
    if (!accessToken.value || user.value) {
      return Promise.resolve()
    }
    if (restoreTask) {
      return restoreTask
    }
    restoreTask = fetchUser().finally(() => {
      restoreTask = null
    })
    return restoreTask
  }

  async function refresh(): Promise<boolean> {
    if (!refreshToken.value) return false
    try {
      const data = await requestRefreshToken(refreshToken.value)
      setTokens(data.access_token, data.refresh_token)
      return true
    } catch {
      return false
    }
  }

  async function updateProfile(payload: ProfileUpdatePayload) {
    const data = await updateCurrentUser(payload)
    user.value = data
    return data
  }

  async function changePassword(currentPassword: string, newPassword: string) {
    await changeCurrentUserPassword(currentPassword, newPassword)
  }

  async function deleteAccount(password: string) {
    await deleteCurrentUserAccount(password)
    logout()
  }

  function logout() {
    accessToken.value = null
    refreshToken.value = null
    user.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  return {
    accessToken,
    refreshToken,
    user,
    isLoading,
    isAuthenticated,
    isSuperAdmin,
    isAdmin,
    userRole,
    login,
    developerLogin,
    register,
    fetchUser,
    restoreUserIfNeeded,
    refresh,
    updateProfile,
    changePassword,
    deleteAccount,
    logout,
  }
})
