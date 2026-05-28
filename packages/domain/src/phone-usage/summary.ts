import type {
  屏幕使用事件,
  每日手机使用汇总,
  手机使用当前状态,
  手机使用时段,
  手机使用汇总字段,
} from './types'

const 一天毫秒数 = 24 * 60 * 60 * 1000

export function 获取本地日期键(timestamp = Date.now()): string {
  const date = new Date(timestamp)
  const year = date.getFullYear()
  const month = `${date.getMonth() + 1}`.padStart(2, '0')
  const day = `${date.getDate()}`.padStart(2, '0')
  return `${year}-${month}-${day}`
}

export function 获取本地日期开始时间(dateKey: string): number {
  return new Date(`${dateKey}T00:00:00`).getTime()
}

export function 创建每日手机使用汇总(dateKey: string): 每日手机使用汇总 {
  return {
    日期: dateKey,
    亮屏次数: 0,
    解锁次数: 0,
    亮屏总时长毫秒: 0,
    解锁使用总时长毫秒: 0,
    解锁时间点列表: [],
  }
}

export function 规范化屏幕使用事件(events: 屏幕使用事件[]): 屏幕使用事件[] {
  const seen = new Set<string>()
  return events
    .filter((event) => Number.isFinite(event.timestamp))
    .sort((left, right) => left.timestamp - right.timestamp || left.type.localeCompare(right.type))
    .filter((event) => {
      const key = `${event.timestamp}:${event.type}`
      if (seen.has(key)) {
        return false
      }
      seen.add(key)
      return true
    })
}

export function 获取最近日期键列表(dayCount: number, endAt = Date.now()): string[] {
  const endDateStart = 获取本地日期开始时间(获取本地日期键(endAt))
  return Array.from({ length: dayCount }, (_, index) => {
    const timestamp = endDateStart - (dayCount - 1 - index) * 一天毫秒数
    return 获取本地日期键(timestamp)
  })
}

function 确保每日汇总(map: Map<string, 每日手机使用汇总>, dateKey: string) {
  let summary = map.get(dateKey)
  if (!summary) {
    summary = 创建每日手机使用汇总(dateKey)
    map.set(dateKey, summary)
  }
  return summary
}

function 累加跨天时长(
  map: Map<string, 每日手机使用汇总>,
  startAt: number,
  endAt: number,
  field: 手机使用汇总字段,
) {
  if (endAt <= startAt) {
    return
  }

  let cursor = startAt
  while (cursor < endAt) {
    const dateKey = 获取本地日期键(cursor)
    const nextDayStart = 获取本地日期开始时间(dateKey) + 一天毫秒数
    const segmentEnd = Math.min(endAt, nextDayStart)
    const summary = 确保每日汇总(map, dateKey)
    summary[field] += segmentEnd - cursor
    cursor = segmentEnd
  }
}

function 追加跨天使用时段(map: Map<string, 手机使用时段[]>, startAt: number, endAt: number) {
  if (endAt <= startAt) {
    return
  }

  let cursor = startAt
  while (cursor < endAt) {
    const dateKey = 获取本地日期键(cursor)
    const nextDayStart = 获取本地日期开始时间(dateKey) + 一天毫秒数
    const segmentEnd = Math.min(endAt, nextDayStart)
    const periods = map.get(dateKey) ?? []
    periods.push({
      开始时间戳: cursor,
      结束时间戳: segmentEnd,
      时长毫秒: segmentEnd - cursor,
    })
    map.set(dateKey, periods)
    cursor = segmentEnd
  }
}

export function 汇总屏幕使用事件(events: 屏幕使用事件[], endAt = Date.now()): 每日手机使用汇总[] {
  const summaryMap = new Map<string, 每日手机使用汇总>()
  const normalizedEvents = 规范化屏幕使用事件(events)
  let screenStartAt: number | null = null
  let usageStartAt: number | null = null

  for (const event of normalizedEvents) {
    const dateKey = 获取本地日期键(event.timestamp)
    const summary = 确保每日汇总(summaryMap, dateKey)

    if (event.type === 'screen_interactive') {
      summary.亮屏次数 += 1
      screenStartAt = event.timestamp
      continue
    }

    if (event.type === 'screen_non_interactive') {
      if (screenStartAt !== null) {
        累加跨天时长(summaryMap, screenStartAt, event.timestamp, '亮屏总时长毫秒')
        screenStartAt = null
      }
      if (usageStartAt !== null) {
        累加跨天时长(summaryMap, usageStartAt, event.timestamp, '解锁使用总时长毫秒')
        usageStartAt = null
      }
      continue
    }

    if (event.type === 'keyguard_hidden') {
      summary.解锁次数 += 1
      summary.解锁时间点列表.push(event.timestamp)
      usageStartAt = event.timestamp
      continue
    }

    if (event.type === 'keyguard_shown' && usageStartAt !== null) {
      累加跨天时长(summaryMap, usageStartAt, event.timestamp, '解锁使用总时长毫秒')
      usageStartAt = null
    }
  }

  if (screenStartAt !== null) {
    累加跨天时长(summaryMap, screenStartAt, endAt, '亮屏总时长毫秒')
  }
  if (usageStartAt !== null) {
    累加跨天时长(summaryMap, usageStartAt, endAt, '解锁使用总时长毫秒')
  }

  return Array.from(summaryMap.values())
    .map((summary) => ({
      ...summary,
      解锁时间点列表: [...summary.解锁时间点列表].sort((left, right) => left - right),
    }))
    .sort((left, right) => left.日期.localeCompare(right.日期))
}

export function 获取每日手机使用时段列表(
  events: 屏幕使用事件[],
  endAt = Date.now(),
): Map<string, 手机使用时段[]> {
  const periodMap = new Map<string, 手机使用时段[]>()
  const normalizedEvents = 规范化屏幕使用事件(events)
  let usageStartAt: number | null = null

  for (const event of normalizedEvents) {
    if (event.type === 'keyguard_hidden') {
      usageStartAt = event.timestamp
      continue
    }

    if (
      usageStartAt !== null
      && (event.type === 'keyguard_shown' || event.type === 'screen_non_interactive')
    ) {
      追加跨天使用时段(periodMap, usageStartAt, event.timestamp)
      usageStartAt = null
    }
  }

  if (usageStartAt !== null) {
    追加跨天使用时段(periodMap, usageStartAt, endAt)
  }

  for (const [dateKey, periods] of periodMap) {
    periodMap.set(
      dateKey,
      [...periods].sort((left, right) => left.开始时间戳 - right.开始时间戳),
    )
  }

  return periodMap
}

export function 获取手机使用当前状态(events: 屏幕使用事件[]): 手机使用当前状态 {
  const state = {
    是否亮屏: false,
    是否解锁: false,
    是否正在使用手机: false,
  }

  for (const event of 规范化屏幕使用事件(events)) {
    if (event.type === 'screen_interactive') {
      state.是否亮屏 = true
    } else if (event.type === 'screen_non_interactive') {
      state.是否亮屏 = false
      state.是否解锁 = false
    } else if (event.type === 'keyguard_hidden') {
      state.是否解锁 = true
    } else if (event.type === 'keyguard_shown') {
      state.是否解锁 = false
    }
  }

  state.是否正在使用手机 = state.是否亮屏 && state.是否解锁
  return state
}
