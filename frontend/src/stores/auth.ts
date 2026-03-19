import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../utils/api'

interface User {
  id: string
  username: string
  email: string
  role: string
  avatar_url: string | null
  bio: string | null
  is_active: boolean
  created_at: string
}

export const useAuthStore = defineStore('auth', () => {
  const accessToken = ref<string | null>(localStorage.getItem('access_token'))
  const refreshToken = ref<string | null>(localStorage.getItem('refresh_token'))
  const user = ref<User | null>(null)

  const isAuthenticated = computed(() => !!accessToken.value)
  const isSuperAdmin = computed(() => user.value?.role === 'super_admin')
  const isAdmin = computed(() => user.value?.role === 'admin' || user.value?.role === 'super_admin')

  function setTokens(access: string, refresh: string) {
    accessToken.value = access
    refreshToken.value = refresh
    localStorage.setItem('access_token', access)
    localStorage.setItem('refresh_token', refresh)
  }

  async function login(username: string, password: string) {
    const { data } = await api.post('/auth/login', { username, password })
    setTokens(data.access_token, data.refresh_token)
    await fetchUser()
  }

  async function register(username: string, email: string, password: string) {
    await api.post('/auth/register', { username, email, password })
  }

  async function fetchUser() {
    if (!accessToken.value) return
    try {
      const { data } = await api.get('/users/me')
      user.value = data
    } catch {
      logout()
    }
  }

  async function refresh(): Promise<boolean> {
    if (!refreshToken.value) return false
    try {
      const { data } = await api.post('/auth/refresh', { refresh_token: refreshToken.value })
      setTokens(data.access_token, data.refresh_token)
      return true
    } catch {
      return false
    }
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
    isAuthenticated,
    isSuperAdmin,
    isAdmin,
    login,
    register,
    fetchUser,
    refresh,
    logout,
  }
})
