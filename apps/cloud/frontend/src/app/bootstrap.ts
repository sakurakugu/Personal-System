import { 仅运行一次引导任务, 初始化主题存储 } from '@personal-system/app-core'
import { 使用认证存储, 配置认证存储上下文 } from '@personal-system/domain/auth'
import { 使用博客外观存储 } from '@personal-system/module-blog/store'
import type { Pinia } from 'pinia'
import { 开发者快捷登录 } from '../modules/认证/dev-login'
import { 配置API客户端上下文 } from '../shared/api/context'
import { 使用设置存储 } from '../shared/stores/settings'
import { 使用主题存储 } from '../shared/stores/theme'

const bootstrapState = {
  task: null as Promise<void> | null,
}

export function 初始化应用外壳(pinia: Pinia): Promise<void> {
  return 仅运行一次引导任务(bootstrapState, async () => {
    const theme = 使用主题存储(pinia)
    const settings = 使用设置存储(pinia)
    const auth = 使用认证存储(pinia)
    const blogAppearance = 使用博客外观存储(pinia)

    初始化主题存储(theme)
    blogAppearance.init()
    配置API客户端上下文({
      handleUnauthorized: () => auth.清除会话(),
    })
    配置认证存储上下文({
      performDeveloperLogin: import.meta.env.DEV ? 开发者快捷登录 : undefined,
    })

    await Promise.all([settings.ensurePublicSettingsLoaded(), auth.需要时恢复用户()])
  })
}
