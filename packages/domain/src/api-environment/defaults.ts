import { 规范化API环境基础URL, type ApiEnvironmentItem } from './store'

export const DEFAULT_SERVER_ENVIRONMENT_ID = 'server'
export const DEFAULT_LOCAL_ENVIRONMENT_ID = 'local'
export const DEFAULT_SERVER_API_BASE = 'https://api.sakurakugu.top/v1'

export function 获取默认API环境ID(isDevelopment: boolean): string {
  if (isDevelopment) {
    return DEFAULT_LOCAL_ENVIRONMENT_ID
  }
  return DEFAULT_SERVER_ENVIRONMENT_ID
}

export function 解析默认服务器API基地址(serverBase?: string, productionBase?: string): string {
  return 规范化API环境基础URL(
    serverBase?.trim()
    || productionBase?.trim()
    || DEFAULT_SERVER_API_BASE,
  )
}

export function 创建内置API环境(localBase: string, serverBase?: string, productionBase?: string): ApiEnvironmentItem[] {
  return [
    {
      id: DEFAULT_SERVER_ENVIRONMENT_ID,
      name: '线上环境',
      baseUrl: 解析默认服务器API基地址(serverBase, productionBase),
    },
    {
      id: DEFAULT_LOCAL_ENVIRONMENT_ID,
      name: '本地开发',
      baseUrl: 规范化API环境基础URL(localBase),
    },
  ]
}
