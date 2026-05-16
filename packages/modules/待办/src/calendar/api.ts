import api from '@personal-system/api'
import type { HolidayCalendarYear } from './types'

export async function 获取节假日年份(year: number): Promise<HolidayCalendarYear> {
  const { data } = await api.get<HolidayCalendarYear>(`/calendar/years/${year}`)
  return data
}
