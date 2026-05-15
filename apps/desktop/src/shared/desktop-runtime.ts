type 桌面运行时Api = {
  runtime: 'electron'
  openDesktopMainWindow: () => Promise<number | null>
  openDesktopWidgetWindow: () => Promise<number | null>
  closeDesktopWidgetWindow: () => Promise<boolean>
  getDesktopWidgetWindowState: () => Promise<{
    open: boolean
    alwaysOnTop: boolean
    movable: boolean
  }>
  setDesktopWidgetWindowContentHeight: (height: number) => Promise<number | null>
  setDesktopWidgetWindowState: (payload: {
    alwaysOnTop?: boolean
    movable?: boolean
  }) => Promise<{
    open: boolean
    alwaysOnTop: boolean
    movable: boolean
  }>
  onDesktopWidgetWindowStateChange: (
    listener: (payload: {
      open: boolean
      alwaysOnTop: boolean
      movable: boolean
    }) => void,
  ) => () => void
  closeCurrentWindow: () => Promise<void>
  minimizeCurrentWindow: () => Promise<void>
  toggleMaximizeCurrentWindow: () => Promise<{ maximized: boolean }>
  getCurrentWindowState: () => Promise<{ maximized: boolean }>
  onCurrentWindowStateChange: (
    listener: (payload: { maximized: boolean }) => void,
  ) => () => void
  loadDesktopAuthToken: () => Promise<string | null>
  saveDesktopAuthToken: (token: string | null) => Promise<void>
  syncWidgetAuthToken: (payload: {
    token: string
    apiBaseUrl?: string | null
    widgetName?: string | null
  }) => Promise<string>
  checkGitEnvironment: () => Promise<{
    installed: boolean
    version: string | null
    detail: string
  }>
  readMinecraftServerStorage: () => Promise<{
    favorites: Array<{ address: string; edition: 'auto' | 'java' | 'bedrock' }>
    history: Array<{ address: string; edition: 'auto' | 'java' | 'bedrock' }>
  }>
  writeMinecraftServerStorage: (data: {
    favorites: Array<{ address: string; edition: 'auto' | 'java' | 'bedrock' }>
    history: Array<{ address: string; edition: 'auto' | 'java' | 'bedrock' }>
  }) => Promise<void>
  queryMinecraftServer: (request: {
    address: string
    edition?: 'auto' | 'java' | 'bedrock'
    timeout?: number
  }) => Promise<unknown>
  convertFileSrc: (filePath: string) => Promise<string>
  checkImageClassifierEnvironment: () => Promise<unknown>
  selectImageClassifierInputs: (mode: 'file' | 'folder') => Promise<string[]>
  selectImageClassifierOutputPath: (mode: 'csv' | 'json' | 'folder') => Promise<string | null>
  discoverImageClassifierInputs: (request: {
    inputs: string[]
    recursive: boolean
  }) => Promise<{ inputs: string[] }>
  stopImageClassifier: () => Promise<void>
  imageClassifierAction: (request: unknown) => Promise<unknown>
  runImageClassifier: (request: unknown) => Promise<unknown>
  runImageClassifierResultAction: (request: unknown) => Promise<unknown>
  runImageClassifierStream: (
    request: unknown,
    onEvent: (event: unknown) => void,
  ) => Promise<void>
}

declare global {
  interface Window {
    personalSystemDesktop?: 桌面运行时Api
  }
}

export function getDesktopRuntime() {
  return window.personalSystemDesktop ?? null
}

export function isElectronDesktop() {
  return getDesktopRuntime()?.runtime === 'electron'
}
