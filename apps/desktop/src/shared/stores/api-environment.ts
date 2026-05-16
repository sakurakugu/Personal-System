import { 是否启用API环境切换 } from '@personal-system/api'
import {
  createApiEnvironmentStore,
  创建内置API环境,
  获取默认API环境ID,
  type ApiEnvironmentItem,
} from '@personal-system/domain/api-environment'

const STORAGE_KEY_CUSTOM = 'personal-system:desktop-api-env:custom'
const STORAGE_KEY_ACTIVE = 'personal-system:desktop-api-env:active'
const DEFAULT_LOCAL_API_BASE = 'http://localhost:5175/api/v1'

function 获取默认环境ID(): string {
  return 获取默认API环境ID(import.meta.env.DEV)
}

function 获取默认环境列表(): ApiEnvironmentItem[] {
  const localBase =
    import.meta.env.VITE_DESKTOP_LOCAL_API_BASE?.trim()
    || DEFAULT_LOCAL_API_BASE

  return 创建内置API环境(
    localBase,
    import.meta.env.VITE_SERVER_API_BASE,
    import.meta.env.VITE_PRODUCTION_API_BASE,
  )
}

export { type ApiEnvironmentItem }

export const useApiEnvironmentStore = createApiEnvironmentStore({
  storeId: 'desktop-api-environment',
  storageKeyCustom: STORAGE_KEY_CUSTOM,
  storageKeyActive: STORAGE_KEY_ACTIVE,
  getDefaultEnvironments: 获取默认环境列表,
  getDefaultEnvironmentId: 获取默认环境ID,
  isEnvironmentSwitchEnabled: 是否启用API环境切换,
})
