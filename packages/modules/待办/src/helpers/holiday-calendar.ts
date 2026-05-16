import { 获取节假日年份 } from '../calendar/api'
import type { HolidayCalendarYear } from '../calendar/types'

const yearCache = new Map<number, Promise<HolidayCalendarYear>>()

export async function getHolidayCalendarYears(years: number[]): Promise<HolidayCalendarYear[]> {
  const uniqueYears = Array.from(new Set(years)).sort((a, b) => a - b)
  return Promise.all(uniqueYears.map((year) => {
    const cached = yearCache.get(year)
    if (cached) return cached
    const request = 获取节假日年份(year).catch((error: unknown) => {
      yearCache.delete(year)
      throw error
    })
    yearCache.set(year, request)
    return request
  }))
}
