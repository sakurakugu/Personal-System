import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import {
  changeCurrentUserPassword,
  deleteCurrentUserAccount,
  register as requestRegister,
  updateCurrentUser,
} from './api'
import { getConfiguredAuthSessionDriver, getConfiguredDeveloperLoginHandler } from './context'
import { isDeveloperLoginEnabled } from './runtime'
import type { AuthUser, AuthUserRole, ProfileUpdatePayload } from './types'

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
    const sessionDriver = getConfiguredAuthSessionDriver()
    user.value = null
    sessionChecked.value = true
    void sessionDriver.clearSession?.()
  }

  async function login(username: string, password: string) {
    const sessionDriver = getConfiguredAuthSessionDriver()
    const loginResult = await sessionDriver.login({ username, password })
    if (loginResult) {
      user.value = loginResult
      sessionChecked.value = true
      return
    }
    await fetchUser()
  }

  async function developerLogin(role: AuthUserRole) {
    if (!isDeveloperLoginEnabled()) {
      throw new Error('当前环境不支持开发者登录')
    }
    const performDeveloperLogin = getConfiguredDeveloperLoginHandler()
    if (!performDeveloperLogin) {
      throw new Error('当前应用未配置开发者登录能力')
    }
    await performDeveloperLogin(role)
    await fetchUser()
  }

  async function register(username: string, email: string, password: string, nickname?: string) {
    await requestRegister({ username, email, password, nickname })
  }

  async function fetchUser() {
    const sessionDriver = getConfiguredAuthSessionDriver()
    const data = await sessionDriver.fetchCurrentUser()
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
    const sessionDriver = getConfiguredAuthSessionDriver()
    try {
      await sessionDriver.logout()
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
