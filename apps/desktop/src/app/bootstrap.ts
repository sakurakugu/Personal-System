import { 初始化主题存储, 仅运行一次引导任务 } from '@personal-system/app-core'
import type { Pinia } from 'pinia'
import { 配置API客户端上下文 } from '@personal-system/api'
import {
  配置认证存储上下文,
  创建设备令牌会话驱动,
  使用认证存储,
} from '@personal-system/domain/auth'
import { 使用主题存储 } from '../shared/stores/theme'
import {
  获取存储的桌面令牌,
  初始化桌面令牌存储,
  设置存储的桌面令牌,
} from '../shared/auth/device-token'

const bootstrapState = {
  task: null as Promise<void> | null,
}

/**
 * 初始化桌面小工具应用外壳。
 * 小工具只需要设备令牌登录态、主题与 API 客户端上下文，不再初始化主窗口相关能力。
 */
export function 初始化应用外壳(pinia: Pinia): Promise<void> {
  return 仅运行一次引导任务(bootstrapState, async () => {
    const auth = 使用认证存储(pinia)
    const theme = 使用主题存储(pinia)

    await 初始化桌面令牌存储()

    配置API客户端上下文({
      getAuthToken: 获取存储的桌面令牌,
      handleUnauthorized: () => auth.清除会话(),
    })
    配置认证存储上下文({
      sessionDriver: 创建设备令牌会话驱动({
        deviceName: 'Personal System',
        deviceType: 'desktop',
        scope: 'full_client',
        clientVersion: '0.1.0',
        platform: navigator.platform || 'desktop',
        persistToken: 设置存储的桌面令牌,
      }),
    })

    初始化主题存储(theme)

    await auth.需要时恢复用户()
  })
}
