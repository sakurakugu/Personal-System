export interface ApiClientContextOptions {
  getActiveBaseUrl?: () => string | null | undefined
  getAuthToken?: () => string | null | undefined
  handleUnauthorized?: () => void
}

const apiClientContext: ApiClientContextOptions = {}

export function 配置API客户端上下文(options: ApiClientContextOptions): void {
  apiClientContext.getActiveBaseUrl = options.getActiveBaseUrl
  apiClientContext.getAuthToken = options.getAuthToken
  apiClientContext.handleUnauthorized = options.handleUnauthorized
}

export function 获取已配置的活跃基地址(): string | null {
  return apiClientContext.getActiveBaseUrl?.() ?? null
}

export function 获取已配置的认证令牌(): string | null {
  return apiClientContext.getAuthToken?.() ?? null
}

export function 通知API未授权(): void {
  apiClientContext.handleUnauthorized?.()
}
