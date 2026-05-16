import axios, { AxiosHeaders } from 'axios'
import { 获取已配置的认证令牌, 通知API未授权 } from './context'
import { 解析当前API基地址 } from './runtime'

const CSRF_COOKIE_NAME = 'csrf_token'
const CSRF_HEADER_NAME = 'X-CSRF-Token'
const VISITOR_COOKIE_NAME = 'visitor_id'
const VISITOR_COOKIE_MAX_AGE = 60 * 60 * 24 * 365 * 5

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

function buildVisitorId(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID()
  }
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`
}

function ensureVisitorCookie(): void {
  if (typeof document === 'undefined') {
    return
  }
  if (readCookie(VISITOR_COOKIE_NAME)) {
    return
  }
  document.cookie = [
    `${VISITOR_COOKIE_NAME}=${encodeURIComponent(buildVisitorId())}`,
    'Path=/',
    `Max-Age=${VISITOR_COOKIE_MAX_AGE}`,
    'SameSite=Lax',
  ].join('; ')
}

const api = axios.create({
  baseURL: 解析当前API基地址(),
  timeout: 15000,
  withCredentials: true,
})

api.interceptors.request.use((config) => {
  config.baseURL = 解析当前API基地址()
  ensureVisitorCookie()
  const authToken = 获取已配置的认证令牌()
  config.withCredentials = !authToken

  const method = (config.method || 'get').toUpperCase()
  const headers = AxiosHeaders.from(config.headers)
  if (authToken) {
    headers.set('Authorization', `Bearer ${authToken}`)
  } else {
    headers.delete('Authorization')
  }
  if (['GET', 'HEAD'].includes(method) && import.meta.env.DEV) {
    config.params = { ...config.params, _t: Date.now() }
    headers.set('Cache-Control', 'no-cache')
    headers.set('Pragma', 'no-cache')
  }
  if (!['GET', 'HEAD', 'OPTIONS', 'TRACE'].includes(method)) {
    const csrfToken = readCookie(CSRF_COOKIE_NAME)
    if (csrfToken && !authToken) {
      headers.set(CSRF_HEADER_NAME, csrfToken)
    }
  }
  config.headers = headers
  return config
})

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config as typeof error.config | undefined
    if (error.response?.status === 401 && original) {
      通知API未授权()
    }
    return Promise.reject(error)
  },
)

export default api
