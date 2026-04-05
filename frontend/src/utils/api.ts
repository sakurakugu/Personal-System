import axios from 'axios'
import { Capacitor } from '@capacitor/core'
import { useAuthStore } from '../stores/auth'
import { useApiEnvironmentStore } from '../stores/api-environment'
import { isNativeDevServerMode, resolveApiBase } from './runtime'

const api = axios.create({
  baseURL: resolveApiBase(),
  timeout: 15000,
})

// 请求拦截：附加访问令牌
api.interceptors.request.use((config) => {
  const auth = useAuthStore()
  const environmentStore = useApiEnvironmentStore()
  if (Capacitor.isNativePlatform() && !isNativeDevServerMode() && environmentStore.activeBaseUrl) {
    config.baseURL = environmentStore.activeBaseUrl
  }
  if (auth.accessToken) {
    config.headers.Authorization = `Bearer ${auth.accessToken}`
  }
  return config
})

// 响应拦截：在 401 时自动刷新令牌
api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config as (typeof error.config & { _retry?: boolean }) | undefined
    const requestUrl = typeof original?.url === 'string' ? original.url : ''
    const isRefreshRequest = requestUrl.includes('/auth/refresh')
    // 刷新接口自身失败时直接退出，避免递归触发刷新。
    if (error.response?.status === 401 && original && !original._retry && !isRefreshRequest) {
      original._retry = true
      const auth = useAuthStore()
      const ok = await auth.refresh()
      if (ok) {
        original.headers.Authorization = `Bearer ${auth.accessToken}`
        return api(original)
      }
      auth.logout()
    }
    return Promise.reject(error)
  }
)

function formatValidationPath(loc: unknown): string {
  if (!Array.isArray(loc)) return ''
  const fields = loc.filter((item) => item !== 'body' && typeof item === 'string')
  return fields.join('.')
}

export function getApiErrorMessage(error: unknown, fallback: string): string {
  if (!axios.isAxiosError(error)) return fallback
  const detail = error.response?.data?.detail
  if (typeof detail === 'string' && detail.trim()) return detail
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0]
    if (typeof first === 'string' && first.trim()) return first
    if (first && typeof first === 'object') {
      const path = formatValidationPath((first as { loc?: unknown }).loc)
      const message = (first as { msg?: unknown }).msg
      if (typeof message === 'string' && message.trim()) {
        return path ? `${path}: ${message}` : message
      }
    }
  }
  return fallback
}

export default api
