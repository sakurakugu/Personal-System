export function 是否启用开发者登录(): boolean {
  if (import.meta.env.DEV) {
    return true
  }
  return import.meta.env.VITE_ENABLE_DEVELOPER_LOGIN === 'true'
}
