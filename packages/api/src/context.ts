export interface ApiClientContextOptions {
  getActiveBaseUrl?: () => string | null | undefined
  handleUnauthorized?: () => void
}

const apiClientContext: ApiClientContextOptions = {}

export function configureApiClientContext(options: ApiClientContextOptions): void {
  apiClientContext.getActiveBaseUrl = options.getActiveBaseUrl
  apiClientContext.handleUnauthorized = options.handleUnauthorized
}

export function getConfiguredActiveBaseUrl(): string | null {
  return apiClientContext.getActiveBaseUrl?.() ?? null
}

export function notifyApiUnauthorized(): void {
  apiClientContext.handleUnauthorized?.()
}
