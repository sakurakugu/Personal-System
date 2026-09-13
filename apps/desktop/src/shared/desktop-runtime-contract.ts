export type 桌面小工具窗口状态 = {
  open: boolean
  alwaysOnTop: boolean
  movable: boolean
  surfaceOpacity: number
  showCloseButton: boolean
}

export type 桌面小工具窗口状态补丁 = {
  alwaysOnTop?: boolean
  movable?: boolean
  surfaceOpacity?: number
  showCloseButton?: boolean
}

export type 当前窗口状态 = {
  maximized: boolean
}

export type 桌面运行时Api = {
  runtime: 'electron'
  openDesktopMainWindow: () => Promise<number | null>
  openDesktopWidgetWindow: () => Promise<number | null>
  closeDesktopWidgetWindow: () => Promise<boolean>
  getDesktopWidgetWindowState: () => Promise<桌面小工具窗口状态>
  setDesktopWidgetWindowContentHeight: (height: number) => Promise<number | null>
  setDesktopWidgetWindowState: (payload: 桌面小工具窗口状态补丁) => Promise<桌面小工具窗口状态>
  onDesktopWidgetWindowStateChange: (listener: (payload: 桌面小工具窗口状态) => void) => () => void
  closeCurrentWindow: () => Promise<void>
  minimizeCurrentWindow: () => Promise<void>
  toggleMaximizeCurrentWindow: () => Promise<当前窗口状态>
  getCurrentWindowState: () => Promise<当前窗口状态>
  onCurrentWindowStateChange: (listener: (payload: 当前窗口状态) => void) => () => void
  loadDesktopAuthToken: () => Promise<string | null>
  saveDesktopAuthToken: (token: string | null) => Promise<void>
}
