import { readTwikooEnvId } from '../constants/twikooConfig'

interface TwikooApiResponse<T = Record<string, unknown>> {
  result: T & {
    code?: number
    message?: string
  }
}

export interface TwikooAdminConfig {
  HIDE_ADMIN_CRYPT?: string
  [key: string]: unknown
}

function 读取Twikoo环境地址(): string {
  const envId = readTwikooEnvId()
  if (!envId) {
    throw new Error('尚未配置 Twikoo 服务地址')
  }
  return envId
}

export function 读取Twikoo访问令牌(): string {
  return window.localStorage.getItem('twikoo-access-token')?.trim() || ''
}

async function 请求Twikoo<T = Record<string, unknown>>(
  event: string,
  data: Record<string, unknown> = {},
): Promise<TwikooApiResponse<T>> {
  const response = await fetch(读取Twikoo环境地址(), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      event,
      accessToken: 读取Twikoo访问令牌(),
      ...data,
    }),
  })

  if (!response.ok) {
    throw new Error(`Twikoo 请求失败：HTTP ${response.status}`)
  }

  return await response.json() as TwikooApiResponse<T>
}

export async function 读取Twikoo管理配置(): Promise<TwikooAdminConfig> {
  const response = await 请求Twikoo<{ config?: TwikooAdminConfig }>('GET_CONFIG_FOR_ADMIN')
  if (response.result.code) {
    throw new Error(response.result.message || '读取 Twikoo 配置失败')
  }
  return response.result.config || {}
}

export async function 更新Twikoo管理配置(config: TwikooAdminConfig): Promise<void> {
  const response = await 请求Twikoo('SET_CONFIG', { config })
  if (response.result.code) {
    throw new Error(response.result.message || '保存 Twikoo 配置失败')
  }
}
