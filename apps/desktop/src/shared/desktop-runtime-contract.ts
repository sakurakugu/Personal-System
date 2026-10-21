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

/** 桌面端暴露给渲染层的运行时能力。 */
export type 桌面运行时Api = {
  runtime: 'electron'
  /** 打开网页后台（开发环境本地 5173，打包后线上地址）。 */
  openWebConsole: () => Promise<void>
  closeDesktopWidgetWindow: () => Promise<boolean>
  getDesktopWidgetWindowState: () => Promise<桌面小工具窗口状态>
  setDesktopWidgetWindowContentHeight: (height: number) => Promise<number | null>
  setDesktopWidgetWindowState: (payload: 桌面小工具窗口状态补丁) => Promise<桌面小工具窗口状态>
  onDesktopWidgetWindowStateChange: (listener: (payload: 桌面小工具窗口状态) => void) => () => void
  loadDesktopAuthToken: () => Promise<string | null>
  saveDesktopAuthToken: (token: string | null) => Promise<void>
}
