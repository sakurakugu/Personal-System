export function isDeveloperLoginEnabled(): boolean {
  if (import.meta.env.DEV) {
    return true
  }
  return import.meta.env.VITE_ENABLE_DEVELOPER_LOGIN === 'true'
}
