import type {
  图片分类动作结果,
  图片分类动作请求,
  图片分类环境状态,
  图片分类进度事件,
  图片分类结果,
  图片分类结果处理结果,
  图片分类输入选择模式,
  图片分类输出选择模式,
  图片分类请求,
} from './image-classifier'
import type { 我的世界服务器查询请求, 我的世界服务器查询结果 } from './minecraft-server'
import type { 我的世界服务器存储数据 } from './minecraft-server-storage'
import type { Git环境状态 } from './windows-tools'
import type {
  图片工具能力,
  图片导出参数,
  图片拼接参数,
  图片编辑参数,
  图片资源句柄,
  桌面文件结果,
} from '../../../../packages/platform/src/image-tools/types'

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

export type 同步小工具凭证请求 = {
  token: string
  apiBaseUrl?: string | null
  widgetName?: string | null
}

export type 桌面图片工具输出选项 = {
  defaultName?: string
  filters?: Array<{ name: string, extensions: string[] }>
}

export type 图片分类结果处理请求 = {
  action: 'export_csv' | 'export_json' | 'move_results'
  payload: Pick<图片分类结果, 'results' | 'skipped'>
  outputPath: string
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
  syncWidgetAuthToken: (payload: 同步小工具凭证请求) => Promise<string>
  checkGitEnvironment: () => Promise<Git环境状态>
  readMinecraftServerStorage: () => Promise<我的世界服务器存储数据>
  writeMinecraftServerStorage: (data: 我的世界服务器存储数据) => Promise<void>
  queryMinecraftServer: (request: 我的世界服务器查询请求) => Promise<我的世界服务器查询结果>
  convertFileSrc: (filePath: string) => Promise<string>
  imageToolsGetCapabilities: () => Promise<图片工具能力>
  imageToolsSelectInputs: () => Promise<string[]>
  imageToolsSelectOutputPath: (mode: 'file' | 'folder', options?: 桌面图片工具输出选项) => Promise<string | null>
  imageToolsImportFromPaths: (paths: string[]) => Promise<图片资源句柄[]>
  imageToolsConvert: (request: {
    resourceId: string
    output: 图片导出参数
  }) => Promise<桌面文件结果>
  imageToolsEdit: (request: {
    resourceId: string
    edit: 图片编辑参数
    output: 图片导出参数
  }) => Promise<桌面文件结果>
  imageToolsStitch: (request: {
    resourceIds: string[]
    stitch: 图片拼接参数
    output: 图片导出参数
  }) => Promise<桌面文件结果>
  imageToolsRelease: (resourceIds: string[]) => Promise<void>
  checkImageClassifierEnvironment: () => Promise<图片分类环境状态>
  selectImageClassifierInputs: (mode: 图片分类输入选择模式) => Promise<string[]>
  selectImageClassifierOutputPath: (mode: 图片分类输出选择模式) => Promise<string | null>
  discoverImageClassifierInputs: (request: {
    inputs: string[]
    recursive: boolean
  }) => Promise<{ inputs: string[] }>
  stopImageClassifier: () => Promise<void>
  imageClassifierAction: (request: 图片分类动作请求) => Promise<图片分类动作结果>
  runImageClassifier: (request: 图片分类请求) => Promise<图片分类结果>
  runImageClassifierResultAction: (request: 图片分类结果处理请求) => Promise<图片分类结果处理结果>
  runImageClassifierStream: (
    request: 图片分类请求,
    onEvent: (event: 图片分类进度事件) => void,
  ) => Promise<void>
}
