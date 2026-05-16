import { 初始化主题存储, 仅运行一次引导任务 } from '@personal-system/app-core'
import type { Pinia } from 'pinia'
import {
  配置认证存储上下文,
  创建设备令牌会话驱动,
  是否启用开发者登录,
  使用认证存储,
} from '@personal-system/domain/auth'
import { 配置API客户端上下文 } from '@personal-system/api'
import { 使用设置存储 } from '@personal-system/domain/system'
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
import { 使用标签栏存储 } from '../shared/stores/tab-bar'
import { 使用主题存储 } from '../shared/stores/theme'

const bootstrapState = {
  task: null as Promise<void> | null,
}

export function 初始化应用外壳(pinia: Pinia, router: Router): Promise<void> {
  return 仅运行一次引导任务(bootstrapState, async () => {
    const auth = 使用认证存储(pinia)
    const settings = 使用设置存储(pinia)
    const apiEnvironment = useApiEnvironmentStore(pinia)
    const tabBar = 使用标签栏存储(pinia)
    const theme = 使用主题存储(pinia)

    await 初始化手机令牌存储()

    配置API客户端上下文({
      getActiveBaseUrl: () => apiEnvironment.activeBaseUrl,
      getAuthToken: 获取存储的手机令牌,
      handleUnauthorized: () => auth.清除会话(),
    })
    配置认证存储上下文({
      sessionDriver: 创建设备令牌会话驱动({
        deviceName: 'Personal System Phone',
        deviceType: 'phone',
        scope: 'full_client',
        platform: navigator.platform || 'phone',
        persistToken: 设置存储的手机令牌,
      }),
      performDeveloperLogin: 是否启用开发者登录() ? 开发者快捷登录 : undefined,
    })
    初始化主题存储(theme)
    tabBar.init()
    watch(
      () => theme.isDark,
      (isDark) => {
        void 同步原生主题(isDark)
      },
      { immediate: true },
    )
    apiEnvironment.初始化()
    await 初始化原生外壳(router)

    await Promise.all([
      settings.ensurePublicSettingsLoaded(),
      auth.需要时恢复用户(),
    ])
  })
}
