import api from '@personal-system/api'

export interface HolidayCalendarYear {
  year: number
  supported: boolean
  holiday_dates: string[]
  workday_dates: string[]
}

export async function 获取节假日年份(year: number): Promise<HolidayCalendarYear> {
  const { data } = await api.get<HolidayCalendarYear>(`/calendar/years/${year}`)
  return data
}
