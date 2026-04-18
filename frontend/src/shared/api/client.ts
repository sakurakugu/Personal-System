import axios, { AxiosHeaders } from 'axios'
import { notifyApiUnauthorized } from './context'
import { resolveCurrentApiBase } from './runtime'

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
  baseURL: resolveCurrentApiBase(),
  timeout: 15000,
  withCredentials: true,
})

api.interceptors.request.use((config) => {
  config.baseURL = resolveCurrentApiBase()

  const method = (config.method || 'get').toUpperCase()
  if (['GET', 'HEAD'].includes(method) && import.meta.env.DEV) {
    config.params = { ...config.params, _t: Date.now() }
    const headers = AxiosHeaders.from(config.headers)
    headers.set('Cache-Control', 'no-cache')
    headers.set('Pragma', 'no-cache')
    config.headers = headers
  }
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
      notifyApiUnauthorized()
    }
    return Promise.reject(error)
  },
)

export default api
