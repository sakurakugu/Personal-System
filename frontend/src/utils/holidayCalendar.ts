import api from './api'

export interface HolidayCalendarYear {
  year: number
  supported: boolean
  holiday_dates: string[]
  workday_dates: string[]
}

const yearCache = new Map<number, Promise<HolidayCalendarYear>>()

async function fetchHolidayCalendarYear(year: number): Promise<HolidayCalendarYear> {
  const { data } = await api.get<HolidayCalendarYear>(`/calendar/years/${year}`)
  return data
}

export async function getHolidayCalendarYears(years: number[]): Promise<HolidayCalendarYear[]> {
  const uniqueYears = Array.from(new Set(years)).sort((a, b) => a - b)
  return Promise.all(uniqueYears.map((year) => {
    const cached = yearCache.get(year)
    if (cached) return cached
    const request = fetchHolidayCalendarYear(year).catch((error) => {
      yearCache.delete(year)
      throw error
    })
    yearCache.set(year, request)
    return request
  }))
}
