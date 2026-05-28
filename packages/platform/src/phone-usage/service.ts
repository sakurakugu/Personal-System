import { Capacitor, registerPlugin } from '@capacitor/core'
import type {
  屏幕使用事件,
  屏幕使用事件查询参数,
  屏幕使用事件查询结果,
  手机使用采集平台服务,
  使用情况权限状态,
} from './types'

interface CapacitorPhoneUsagePlugin {
  checkUsageAccess(): Promise<使用情况权限状态>
  openUsageAccessSettings(): Promise<void>
  queryScreenUsageEvents(params: 屏幕使用事件查询参数): Promise<屏幕使用事件查询结果>
}

const phoneUsagePlugin = registerPlugin<CapacitorPhoneUsagePlugin>('PhoneUsage')

function 获取原生手机使用插件(): CapacitorPhoneUsagePlugin | null {
  if (!Capacitor.isNativePlatform()) {
    return null
  }

  return phoneUsagePlugin
}

function 过滤屏幕使用事件(events: 屏幕使用事件[]): 屏幕使用事件[] {
  return events
    .filter((event) => (
      typeof event.timestamp === 'number'
      && Number.isFinite(event.timestamp)
      && (
        event.type === 'screen_interactive'
        || event.type === 'screen_non_interactive'
        || event.type === 'keyguard_hidden'
        || event.type === 'keyguard_shown'
      )
    ))
    .sort((left, right) => left.timestamp - right.timestamp || left.type.localeCompare(right.type))
}

export function 创建手机使用采集平台服务(): 手机使用采集平台服务 {
  return {
    async checkUsageAccess() {
      const plugin = 获取原生手机使用插件()
      if (!plugin) {
        return { granted: false }
      }

      return plugin.checkUsageAccess()
    },
    async openUsageAccessSettings() {
      const plugin = 获取原生手机使用插件()
      if (!plugin) {
        console.warn('[PhoneUsagePlatform] 当前运行环境不支持打开使用情况访问设置')
        return
      }

      await plugin.openUsageAccessSettings()
    },
    async queryScreenUsageEvents(params) {
      const plugin = 获取原生手机使用插件()
      if (!plugin) {
        console.info('[PhoneUsagePlatform] 当前运行环境不支持读取屏幕使用事件')
        return { events: [] }
      }

      const result = await plugin.queryScreenUsageEvents(params)
      return {
        events: 过滤屏幕使用事件(result.events),
      }
    },
  }
}
