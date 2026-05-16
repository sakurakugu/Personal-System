import api from '@personal-system/api'
import type { HolidayCalendarYear } from './types'

export async function fetchHolidayCalendarYear(year: number): Promise<HolidayCalendarYear> {
  const { data } = await api.get<HolidayCalendarYear>(`/calendar/years/${year}`)
  return data
}
