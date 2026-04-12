import axios, { AxiosHeaders } from 'axios'
import { Capacitor } from '@capacitor/core'
import { useAuthStore } from '../stores/auth'
import { useApiEnvironmentStore } from '../stores/api-environment'
import { isNativeDevServerMode, resolveApiBase } from './runtime'

const CSRF_COOKIE_NAME = 'csrf_token'
const CSRF_HEADER_NAME = 'X-CSRF-Token'

function readCookie(name: string): string | null {
  if (typeof document === 'undefined') {
    return null
  }
  const prefix = `${name}=`
  for (const item of document.cookie.split(';')) {
    const normalized = item.trim()
    if (normalized.startsWith(prefix)) {
      return decodeURIComponent(normalized.slice(prefix.length))
    }
  }
  return null
}

const api = axios.create({
  baseURL: resolveApiBase(),
  timeout: 15000,
  withCredentials: true,
})

api.interceptors.request.use((config) => {
  const environmentStore = useApiEnvironmentStore()
  if (Capacitor.isNativePlatform() && !isNativeDevServerMode() && environmentStore.activeBaseUrl) {
    config.baseURL = environmentStore.activeBaseUrl
  }
  const method = (config.method || 'get').toUpperCase()
  if (!['GET', 'HEAD', 'OPTIONS', 'TRACE'].includes(method)) {
    const csrfToken = readCookie(CSRF_COOKIE_NAME)
    if (csrfToken) {
      const headers = AxiosHeaders.from(config.headers)
      headers.set(CSRF_HEADER_NAME, csrfToken)
      config.headers = headers
    }
  }
  return config
})

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config as typeof error.config | undefined
    if (error.response?.status === 401 && original) {
      const auth = useAuthStore()
      auth.clearSession()
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
