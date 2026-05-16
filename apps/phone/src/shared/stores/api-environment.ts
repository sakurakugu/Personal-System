import { Capacitor } from '@capacitor/core'
import { 是否启用API环境切换, 是否为原生开发服务器模式, 解析原生开发服务器API基地址 } from '@personal-system/api'
import {
  创建API环境存储,
  创建内置API环境,
  获取默认API环境ID,
  规范化API环境基础URL,
  type ApiEnvironmentItem,
} from '@personal-system/domain/api-environment'

const STORAGE_KEY_CUSTOM = 'personal-system:api-env:custom'
const STORAGE_KEY_ACTIVE = 'personal-system:api-env:active'
const DEFAULT_ANDROID_LOCAL_API_BASE = 'http://10.0.2.2:8000/api/v1'
const DEFAULT_IOS_LOCAL_API_BASE = 'http://127.0.0.1:8000/api/v1'

function 获取默认本地API基地址(): string {
  if (是否为原生开发服务器模式()) {
    return 规范化API环境基础URL(解析原生开发服务器API基地址())
  }
  if (Capacitor.getPlatform() === 'android') {
    return DEFAULT_ANDROID_LOCAL_API_BASE
  }
  return DEFAULT_IOS_LOCAL_API_BASE
}

function 获取默认环境ID(): string {
  return 获取默认API环境ID(import.meta.env.DEV)
}

function 获取默认环境列表(): ApiEnvironmentItem[] {
  return 创建内置API环境(
    获取默认本地API基地址(),
    import.meta.env.VITE_SERVER_API_BASE,
    import.meta.env.VITE_PRODUCTION_API_BASE,
  )
}

export { type ApiEnvironmentItem }

export const 使用API环境存储 = 创建API环境存储({
  storeId: 'phone-api-environment',
  storageKeyCustom: STORAGE_KEY_CUSTOM,
  storageKeyActive: STORAGE_KEY_ACTIVE,
  getDefaultEnvironments: 获取默认环境列表,
  getDefaultEnvironmentId: 获取默认环境ID,
  isEnvironmentSwitchEnabled: 是否启用API环境切换,
})
