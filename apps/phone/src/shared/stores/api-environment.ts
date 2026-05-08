import { Capacitor } from '@capacitor/core'
import { isApiEnvironmentSwitchEnabled, isNativeDevServerMode, resolveNativeDevServerApiBase } from '@personal-system/api'
import {
  createApiEnvironmentStore,
  createBuiltinApiEnvironments,
  getDefaultApiEnvironmentId,
  normalizeApiEnvironmentBaseUrl,
  type ApiEnvironmentItem,
} from '@personal-system/domain/api-environment'

const STORAGE_KEY_CUSTOM = 'personal-system:api-env:custom'
const STORAGE_KEY_ACTIVE = 'personal-system:api-env:active'
const DEFAULT_ANDROID_LOCAL_API_BASE = 'http://10.0.2.2:8000/api/v1'
const DEFAULT_IOS_LOCAL_API_BASE = 'http://127.0.0.1:8000/api/v1'

function getDefaultLocalApiBase(): string {
  if (isNativeDevServerMode()) {
    return normalizeApiEnvironmentBaseUrl(resolveNativeDevServerApiBase())
  }
  if (Capacitor.getPlatform() === 'android') {
    return DEFAULT_ANDROID_LOCAL_API_BASE
  }
  return DEFAULT_IOS_LOCAL_API_BASE
}

function getDefaultEnvironmentId(): string {
  return getDefaultApiEnvironmentId(import.meta.env.DEV)
}

function getDefaultEnvironments(): ApiEnvironmentItem[] {
  return createBuiltinApiEnvironments(
    getDefaultLocalApiBase(),
    import.meta.env.VITE_SERVER_API_BASE,
    import.meta.env.VITE_PRODUCTION_API_BASE,
  )
}

export { type ApiEnvironmentItem }

export const useApiEnvironmentStore = createApiEnvironmentStore({
  storeId: 'phone-api-environment',
  storageKeyCustom: STORAGE_KEY_CUSTOM,
  storageKeyActive: STORAGE_KEY_ACTIVE,
  getDefaultEnvironments,
  getDefaultEnvironmentId,
  isEnvironmentSwitchEnabled: isApiEnvironmentSwitchEnabled,
})
