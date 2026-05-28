export type 屏幕使用事件类型 =
  | 'screen_interactive'
  | 'screen_non_interactive'
  | 'keyguard_hidden'
  | 'keyguard_shown'

export interface 屏幕使用事件 {
  type: 屏幕使用事件类型
  timestamp: number
}

export interface 屏幕使用事件查询参数 {
  startTime: number
  endTime: number
}

export interface 屏幕使用事件查询结果 {
  events: 屏幕使用事件[]
}

export interface 使用情况权限状态 {
  granted: boolean
}

export interface 手机使用采集平台服务 {
  checkUsageAccess(): Promise<使用情况权限状态>
  openUsageAccessSettings(): Promise<void>
  queryScreenUsageEvents(params: 屏幕使用事件查询参数): Promise<屏幕使用事件查询结果>
}
