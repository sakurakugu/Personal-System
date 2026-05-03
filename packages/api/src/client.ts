import axios, { AxiosHeaders } from 'axios'
import { getConfiguredAuthToken, notifyApiUnauthorized } from './context'
import { resolveCurrentApiBase } from './runtime'

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
  baseURL: resolveCurrentApiBase(),
  timeout: 15000,
  withCredentials: true,
})

api.interceptors.request.use((config) => {
  config.baseURL = resolveCurrentApiBase()
  ensureVisitorCookie()
  const authToken = getConfiguredAuthToken()
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
      notifyApiUnauthorized()
    }
    return Promise.reject(error)
  },
)

export default api
