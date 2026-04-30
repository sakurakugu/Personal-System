import axios from 'axios'

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
