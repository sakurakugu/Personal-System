import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  changeCurrentUserPassword,
  deleteCurrentUserAccount,
  fetchCurrentUser,
  login as requestLogin,
  logout as requestLogout,
  register as requestRegister,
  updateCurrentUser,
} from '../features/auth/api'
import type { AuthUser, AuthUserRole, ProfileUpdatePayload } from '../features/auth/types'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<AuthUser | null>(null)
  const isLoading = ref(false)
  const sessionChecked = ref(false)
  let restoreTask: Promise<void> | null = null

  const isAuthenticated = computed(() => !!user.value)
  const isSuperAdmin = computed(() => user.value?.role === 'super_admin')
  const isAdmin = computed(() => user.value?.role === 'admin' || user.value?.role === 'super_admin')
  const userRole = computed(() => user.value?.role || 'guest')

  function clearSession() {
    user.value = null
    sessionChecked.value = true
  }

  async function login(username: string, password: string) {
    await requestLogin({ username, password })
    await fetchUser()
  }

  async function developerLogin(role: AuthUserRole) {
    if (!import.meta.env.DEV) {
      throw new Error('当前环境不支持开发者登录')
    }
    const { loginByDeveloperShortcut } = await import('../features/auth/dev-login')
    await loginByDeveloperShortcut(role)
    await fetchUser()
  }

  async function register(username: string, email: string, password: string, nickname?: string) {
    await requestRegister({ username, email, password, nickname })
  }

  async function fetchUser() {
    const data = await fetchCurrentUser()
    user.value = data
    sessionChecked.value = true
  }

  function restoreUserIfNeeded(): Promise<void> {
    if (user.value || sessionChecked.value) {
      return Promise.resolve()
    }
    if (restoreTask) {
      return restoreTask
    }
    restoreTask = (async () => {
      try {
        await fetchUser()
      } catch {
        clearSession()
      } finally {
        restoreTask = null
      }
    })()
    return restoreTask
  }

  async function updateProfile(payload: ProfileUpdatePayload) {
    const data = await updateCurrentUser(payload)
    user.value = data
    return data
  }

  async function changePassword(currentPassword: string, newPassword: string) {
    await changeCurrentUserPassword(currentPassword, newPassword)
    clearSession()
  }

  async function deleteAccount(password: string) {
    await deleteCurrentUserAccount(password)
    clearSession()
  }

  async function logout() {
    try {
      await requestLogout()
    } finally {
      clearSession()
    }
  }

  return {
    user,
    isLoading,
    sessionChecked,
    isAuthenticated,
    isSuperAdmin,
    isAdmin,
    userRole,
    clearSession,
    login,
    developerLogin,
    register,
    fetchUser,
    restoreUserIfNeeded,
    updateProfile,
    changePassword,
    deleteAccount,
    logout,
  }
})
