import { getDesktopRuntime } from './desktop-runtime'

function normalizeApiBase(rawValue: string | null | undefined): string {
  const normalized = rawValue?.trim().replace(/\/+$/, '')
  return normalized || 'http://127.0.0.1:8000/api/v1'
}

export async function syncWidgetTokenToDesktopWidget(options: {
  token: string
  apiBaseUrl?: string | null
  widgetName?: string | null
}): Promise<string> {
  const runtime = getDesktopRuntime()
  if (!runtime) {
    throw new Error('当前环境不支持桌面小工具同步')
  }

  return await runtime.syncWidgetAuthToken({
    token: options.token,
    apiBaseUrl: normalizeApiBase(options.apiBaseUrl),
    widgetName: options.widgetName?.trim() || 'Personal System Widget',
  })
}
