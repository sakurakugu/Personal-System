import { initializeThemeStore, runBootstrapTaskOnce } from '@personal-system/app-core'
import type { Pinia } from 'pinia'
import {
  configureAuthStoreContext,
  createDeviceTokenSessionDriver,
  isDeveloperLoginEnabled,
  useAuthStore,
} from '@personal-system/domain/auth'
import { configureApiClientContext } from '@personal-system/api'
import { useSettingsStore } from '@personal-system/domain/system'
import type { Router } from 'vue-router'
import { watch } from 'vue'
import { 初始化原生外壳, 同步原生主题 } from './native-shell'
import { 开发者快捷登录 } from '../modules/认证/lib/dev-login'
import {
  获取存储的手机令牌,
  初始化手机令牌存储,
  设置存储的手机令牌,
} from '../shared/auth/device-token'
import { useApiEnvironmentStore } from '../shared/stores/api-environment'
import { useTabBarStore } from '../shared/stores/tab-bar'
import { useThemeStore } from '../shared/stores/theme'

const bootstrapState = {
  task: null as Promise<void> | null,
}

export function 初始化应用外壳(pinia: Pinia, router: Router): Promise<void> {
  return runBootstrapTaskOnce(bootstrapState, async () => {
    const auth = useAuthStore(pinia)
    const settings = useSettingsStore(pinia)
    const apiEnvironment = useApiEnvironmentStore(pinia)
    const tabBar = useTabBarStore(pinia)
    const theme = useThemeStore(pinia)

    await 初始化手机令牌存储()

    configureApiClientContext({
      getActiveBaseUrl: () => apiEnvironment.activeBaseUrl,
      getAuthToken: 获取存储的手机令牌,
      handleUnauthorized: () => auth.clearSession(),
    })
    configureAuthStoreContext({
      sessionDriver: createDeviceTokenSessionDriver({
        deviceName: 'Personal System Phone',
        deviceType: 'phone',
        scope: 'full_client',
        platform: navigator.platform || 'phone',
        persistToken: 设置存储的手机令牌,
      }),
      performDeveloperLogin: isDeveloperLoginEnabled() ? 开发者快捷登录 : undefined,
    })
    initializeThemeStore(theme)
    tabBar.init()
    watch(
      () => theme.isDark,
      (isDark) => {
        void 同步原生主题(isDark)
      },
      { immediate: true },
    )
    apiEnvironment.init()
    await 初始化原生外壳(router)

    await Promise.all([
      settings.ensurePublicSettingsLoaded(),
      auth.restoreUserIfNeeded(),
    ])
  })
}
