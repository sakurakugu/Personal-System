import type { 屏幕使用事件, 屏幕使用事件类型 } from '@personal-system/platform/phone-usage'

export type { 屏幕使用事件, 屏幕使用事件类型 }

export interface 每日手机使用汇总 {
  日期: string
  亮屏次数: number
  解锁次数: number
  亮屏总时长毫秒: number
  解锁使用总时长毫秒: number
  解锁时间点列表: number[]
}

export interface 手机使用采集元数据 {
  最后采集时间戳: number
  最后汇总时间戳: number
  是否已授权使用情况访问: boolean
}

export interface 手机使用持久化状态 {
  元数据: 手机使用采集元数据
  原始事件列表: 屏幕使用事件[]
}

export interface 手机使用补采结果 {
  新增事件数: number
  总事件数: number
  汇总列表: 每日手机使用汇总[]
}

export interface 手机使用当前状态 {
  是否亮屏: boolean
  是否解锁: boolean
  是否正在使用手机: boolean
}

export interface 手机使用时段 {
  开始时间戳: number
  结束时间戳: number
  时长毫秒: number
}

export type 手机使用汇总字段 = '亮屏总时长毫秒' | '解锁使用总时长毫秒'

export const 屏幕使用事件类型列表: 屏幕使用事件类型[] = [
  'screen_interactive',
  'screen_non_interactive',
  'keyguard_hidden',
  'keyguard_shown',
]
