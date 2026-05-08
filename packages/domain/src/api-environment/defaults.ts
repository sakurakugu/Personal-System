import { normalizeApiEnvironmentBaseUrl, type ApiEnvironmentItem } from './store'

export const DEFAULT_SERVER_ENVIRONMENT_ID = 'server'
export const DEFAULT_LOCAL_ENVIRONMENT_ID = 'local'
export const DEFAULT_SERVER_API_BASE = 'https://api.sakurakugu.top/v1'

export function getDefaultApiEnvironmentId(isDevelopment: boolean): string {
  if (isDevelopment) {
    return DEFAULT_LOCAL_ENVIRONMENT_ID
  }
  return DEFAULT_SERVER_ENVIRONMENT_ID
}

export function resolveDefaultServerApiBase(serverBase?: string, productionBase?: string): string {
  return normalizeApiEnvironmentBaseUrl(
    serverBase?.trim()
    || productionBase?.trim()
    || DEFAULT_SERVER_API_BASE,
  )
}

export function createBuiltinApiEnvironments(localBase: string, serverBase?: string, productionBase?: string): ApiEnvironmentItem[] {
  return [
    {
      id: DEFAULT_SERVER_ENVIRONMENT_ID,
      name: '线上环境',
      baseUrl: resolveDefaultServerApiBase(serverBase, productionBase),
    },
    {
      id: DEFAULT_LOCAL_ENVIRONMENT_ID,
      name: '本地开发',
      baseUrl: normalizeApiEnvironmentBaseUrl(localBase),
    },
  ]
}
