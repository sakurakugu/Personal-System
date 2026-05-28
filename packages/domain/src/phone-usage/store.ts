import { 创建手机使用采集平台服务 } from '@personal-system/platform/phone-usage'
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import {
  创建每日手机使用汇总,
  获取每日手机使用时段列表,
  汇总屏幕使用事件,
  获取手机使用当前状态,
  获取最近日期键列表,
  规范化屏幕使用事件,
} from './summary'
import type {
  屏幕使用事件,
  手机使用持久化状态,
  手机使用补采结果,
  手机使用采集元数据,
} from './types'

const 存储键 = 'personal-system:phone-usage:v1'
const 原始事件保留天数 = 14
const 默认回溯天数 = 原始事件保留天数

function 创建默认元数据(): 手机使用采集元数据 {
  return {
    最后采集时间戳: 0,
    最后汇总时间戳: 0,
    是否已授权使用情况访问: false,
  }
}

function 读取持久化状态(): 手机使用持久化状态 {
  if (typeof localStorage === 'undefined') {
    return {
      元数据: 创建默认元数据(),
      原始事件列表: [],
    }
  }

  const raw = localStorage.getItem(存储键)
  if (!raw) {
    return {
      元数据: 创建默认元数据(),
      原始事件列表: [],
    }
  }

  try {
    const parsed = JSON.parse(raw) as Partial<手机使用持久化状态>
    return {
      元数据: {
        ...创建默认元数据(),
        ...parsed.元数据,
      },
      原始事件列表: 规范化屏幕使用事件(parsed.原始事件列表 ?? []),
    }
  } catch (error) {
    console.warn('[PhoneUsageStore] 读取本地手机使用状态失败，将重置本地缓存', error)
    return {
      元数据: 创建默认元数据(),
      原始事件列表: [],
    }
  }
}

function 写入持久化状态(state: 手机使用持久化状态) {
  if (typeof localStorage === 'undefined') {
    return
  }

  localStorage.setItem(存储键, JSON.stringify(state))
}

function 获取默认补采开始时间(now: number) {
  return now - 默认回溯天数 * 24 * 60 * 60 * 1000
}

function 裁剪原始事件(events: 屏幕使用事件[], now: number) {
  const oldest = now - 原始事件保留天数 * 24 * 60 * 60 * 1000
  return events.filter((event) => event.timestamp >= oldest)
}

export const 使用手机使用统计存储 = defineStore('phone-usage', () => {
  const service = 创建手机使用采集平台服务()
  const persistedState = 读取持久化状态()
  const 元数据 = ref<手机使用采集元数据>(persistedState.元数据)
  const 原始事件列表 = ref<屏幕使用事件[]>(persistedState.原始事件列表)
  const 正在补采 = ref(false)
  const 最后错误 = ref<string | null>(null)
  let 补采任务: Promise<手机使用补采结果> | null = null

  const 每日汇总列表 = computed(() => 汇总屏幕使用事件(原始事件列表.value))
  const 每日使用时段映射 = computed(() => 获取每日手机使用时段列表(原始事件列表.value))
  const 当前状态 = computed(() => 获取手机使用当前状态(原始事件列表.value))
  const 最近14天汇总列表 = computed(() => {
    const summaryMap = new Map(每日汇总列表.value.map((item) => [item.日期, item]))
    return 获取最近日期键列表(14).map((dateKey) => summaryMap.get(dateKey) ?? 创建每日手机使用汇总(dateKey))
  })
  const 最近7天汇总列表 = computed(() => {
    const summaryMap = new Map(每日汇总列表.value.map((item) => [item.日期, item]))
    return 获取最近日期键列表(7).map((dateKey) => summaryMap.get(dateKey) ?? 创建每日手机使用汇总(dateKey))
  })
  const 今日汇总 = computed(() => 最近7天汇总列表.value.at(-1) ?? 创建每日手机使用汇总(获取最近日期键列表(1)[0]))

  function 保存状态() {
    写入持久化状态({
      元数据: 元数据.value,
      原始事件列表: 原始事件列表.value,
    })
  }

  async function 刷新权限状态() {
    try {
      const result = await service.checkUsageAccess()
      元数据.value = {
        ...元数据.value,
        是否已授权使用情况访问: result.granted,
      }
      保存状态()
      return result.granted
    } catch (error) {
      最后错误.value = error instanceof Error ? error.message : '检查使用情况访问权限失败'
      console.error('[PhoneUsageStore] 检查使用情况访问权限失败', error)
      return false
    }
  }

  async function 打开使用情况权限设置() {
    console.info('[PhoneUsageStore] 打开使用情况访问设置')
    await service.openUsageAccessSettings()
  }

  async function 补采屏幕使用事件() {
    if (补采任务) {
      return 补采任务
    }

    补采任务 = (async () => {
      正在补采.value = true
      最后错误.value = null

      const now = Date.now()
      const hasPermission = await 刷新权限状态()
      if (!hasPermission) {
        正在补采.value = false
        return {
          新增事件数: 0,
          总事件数: 原始事件列表.value.length,
          汇总列表: 每日汇总列表.value,
        }
      }

      const startTime = Math.max(
        元数据.value.最后采集时间戳 || 获取默认补采开始时间(now),
        获取默认补采开始时间(now),
      )
      console.info('[PhoneUsageStore] 开始补采屏幕使用事件', { startTime, endTime: now })

      try {
        const result = await service.queryScreenUsageEvents({
          startTime,
          endTime: now,
        })
        const beforeCount = 原始事件列表.value.length
        原始事件列表.value = 裁剪原始事件(
          规范化屏幕使用事件([...原始事件列表.value, ...result.events]),
          now,
        )
        元数据.value = {
          ...元数据.value,
          最后采集时间戳: now,
          最后汇总时间戳: now,
          是否已授权使用情况访问: true,
        }
        保存状态()
        const summaryList = 每日汇总列表.value
        const addedCount = Math.max(0, 原始事件列表.value.length - beforeCount)
        console.info('[PhoneUsageStore] 屏幕使用事件补采完成', {
          新增事件数: addedCount,
          总事件数: 原始事件列表.value.length,
          汇总天数: summaryList.length,
        })
        return {
          新增事件数: addedCount,
          总事件数: 原始事件列表.value.length,
          汇总列表: summaryList,
        }
      } catch (error) {
        最后错误.value = error instanceof Error ? error.message : '补采屏幕使用事件失败'
        console.error('[PhoneUsageStore] 补采屏幕使用事件失败', error)
        throw error
      } finally {
        正在补采.value = false
      }
    })().finally(() => {
      补采任务 = null
    })

    return 补采任务
  }

  return {
    元数据,
    原始事件列表,
    每日汇总列表,
    每日使用时段映射,
    最近14天汇总列表,
    最近7天汇总列表,
    今日汇总,
    当前状态,
    正在补采,
    最后错误,
    刷新权限状态,
    打开使用情况权限设置,
    补采屏幕使用事件,
  }
})
