import { 初始化主题存储, 仅运行一次引导任务 } from '@personal-system/app-core'
import type { Pinia } from 'pinia'
import { 配置认证存储上下文, useAuthStore } from '@personal-system/domain/auth'
import { 配置API客户端上下文 } from '../shared/api/context'
import { useBlogAppearanceStore } from '../modules/博客/store'
import { useSettingsStore } from '../shared/stores/settings'
import { useThemeStore } from '../shared/stores/theme'
import { 开发者快捷登录 } from '../modules/认证/dev-login'

const bootstrapState = {
  task: null as Promise<void> | null,
}

export function 初始化应用外壳(pinia: Pinia): Promise<void> {
  return 仅运行一次引导任务(bootstrapState, async () => {
    const theme = useThemeStore(pinia)
    const settings = useSettingsStore(pinia)
    const auth = useAuthStore(pinia)
    const blogAppearance = useBlogAppearanceStore(pinia)

    初始化主题存储(theme)
    blogAppearance.init()
    配置API客户端上下文({
      handleUnauthorized: () => auth.clearSession(),
    })
    配置认证存储上下文({
      performDeveloperLogin: import.meta.env.DEV ? 开发者快捷登录 : undefined,
    })

    await Promise.all([
      settings.ensurePublicSettingsLoaded(),
      auth.restoreUserIfNeeded(),
    ])
  })
}
