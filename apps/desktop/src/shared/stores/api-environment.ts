import { isApiEnvironmentSwitchEnabled } from '@personal-system/api'
import {
  createApiEnvironmentStore,
  createBuiltinApiEnvironments,
  getDefaultApiEnvironmentId,
  type ApiEnvironmentItem,
} from '@personal-system/domain/api-environment'

const STORAGE_KEY_CUSTOM = 'personal-system:desktop-api-env:custom'
const STORAGE_KEY_ACTIVE = 'personal-system:desktop-api-env:active'
const DEFAULT_LOCAL_API_BASE = 'http://localhost:1420/api/v1'

function getDefaultEnvironmentId(): string {
  return getDefaultApiEnvironmentId(import.meta.env.DEV)
}

function getDefaultEnvironments(): ApiEnvironmentItem[] {
  const localBase =
    import.meta.env.VITE_DESKTOP_LOCAL_API_BASE?.trim()
    || DEFAULT_LOCAL_API_BASE

  return createBuiltinApiEnvironments(
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
  getDefaultEnvironments,
  getDefaultEnvironmentId,
  isEnvironmentSwitchEnabled: isApiEnvironmentSwitchEnabled,
})
