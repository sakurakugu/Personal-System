import { contextBridge, ipcRenderer } from 'electron'
import { randomUUID } from 'node:crypto'
import { IPC_CHANNELS, IPC_EVENTS } from './shared/ipc-channels.mjs'

contextBridge.exposeInMainWorld('personalSystemDesktop', {
  runtime: 'electron',
  openDesktopMainWindow: () => ipcRenderer.invoke(IPC_CHANNELS.windowOpenMain),
  openDesktopWidgetWindow: () => ipcRenderer.invoke(IPC_CHANNELS.windowOpenWidget),
  closeDesktopWidgetWindow: () => ipcRenderer.invoke(IPC_CHANNELS.windowCloseWidget),
  getDesktopWidgetWindowState: () => ipcRenderer.invoke(IPC_CHANNELS.widgetGetState),
  setDesktopWidgetWindowState: (payload) => ipcRenderer.invoke(IPC_CHANNELS.widgetSetState, payload),
  setDesktopWidgetWindowContentHeight: (height) => ipcRenderer.invoke(IPC_CHANNELS.widgetSetContentHeight, height),
  onDesktopWidgetWindowStateChange: (listener) => {
    const wrappedListener = (_event, payload) => {
      listener(payload)
    }
    ipcRenderer.on(IPC_EVENTS.widgetStateChanged, wrappedListener)
    return () => {
      ipcRenderer.removeListener(IPC_EVENTS.widgetStateChanged, wrappedListener)
    }
  },
  closeCurrentWindow: () => ipcRenderer.invoke(IPC_CHANNELS.windowCloseCurrent),
  minimizeCurrentWindow: () => ipcRenderer.invoke(IPC_CHANNELS.windowMinimizeCurrent),
  toggleMaximizeCurrentWindow: () => ipcRenderer.invoke(IPC_CHANNELS.windowToggleMaximizeCurrent),
  getCurrentWindowState: () => ipcRenderer.invoke(IPC_CHANNELS.windowGetCurrentState),
  onCurrentWindowStateChange: (listener) => {
    const wrappedListener = (_event, payload) => {
      listener(payload)
    }
    ipcRenderer.on(IPC_EVENTS.windowStateChanged, wrappedListener)
    return () => {
      ipcRenderer.removeListener(IPC_EVENTS.windowStateChanged, wrappedListener)
    }
  },
  loadDesktopAuthToken: () => ipcRenderer.invoke(IPC_CHANNELS.authLoadToken),
  saveDesktopAuthToken: (token) => ipcRenderer.invoke(IPC_CHANNELS.authSaveToken, token),
  syncWidgetAuthToken: (payload) => ipcRenderer.invoke(IPC_CHANNELS.widgetSyncToken, payload),
  checkGitEnvironment: () => ipcRenderer.invoke(IPC_CHANNELS.utilityCheckGit),
  readMinecraftServerStorage: () => ipcRenderer.invoke(IPC_CHANNELS.minecraftReadStorage),
  writeMinecraftServerStorage: (data) => ipcRenderer.invoke(IPC_CHANNELS.minecraftWriteStorage, data),
  queryMinecraftServer: (request) => ipcRenderer.invoke(IPC_CHANNELS.minecraftQuery, request),
  convertFileSrc: (filePath) => ipcRenderer.invoke(IPC_CHANNELS.fileToUrl, filePath),
  imageToolsGetCapabilities: () => ipcRenderer.invoke(IPC_CHANNELS.imageToolsGetCapabilities),
  imageToolsSelectInputs: () => ipcRenderer.invoke(IPC_CHANNELS.imageToolsSelectInputs),
  imageToolsSelectOutputPath: (mode, options) => ipcRenderer.invoke(IPC_CHANNELS.imageToolsSelectOutputPath, mode, options),
  imageToolsImportFromPaths: (paths) => ipcRenderer.invoke(IPC_CHANNELS.imageToolsImportFromPaths, paths),
  imageToolsConvert: (request) => ipcRenderer.invoke(IPC_CHANNELS.imageToolsConvert, request),
  imageToolsEdit: (request) => ipcRenderer.invoke(IPC_CHANNELS.imageToolsEdit, request),
  imageToolsStitch: (request) => ipcRenderer.invoke(IPC_CHANNELS.imageToolsStitch, request),
  imageToolsRelease: (resourceIds) => ipcRenderer.invoke(IPC_CHANNELS.imageToolsRelease, resourceIds),
  checkImageClassifierEnvironment: () => ipcRenderer.invoke(IPC_CHANNELS.imageClassifierCheckEnvironment),
  selectImageClassifierInputs: (mode) => ipcRenderer.invoke(IPC_CHANNELS.imageClassifierSelectInputs, mode),
  selectImageClassifierOutputPath: (mode) => ipcRenderer.invoke(IPC_CHANNELS.imageClassifierSelectOutputPath, mode),
  discoverImageClassifierInputs: (request) => ipcRenderer.invoke(IPC_CHANNELS.imageClassifierDiscoverInputs, request),
  stopImageClassifier: () => ipcRenderer.invoke(IPC_CHANNELS.imageClassifierStop),
  imageClassifierAction: (request) => ipcRenderer.invoke(IPC_CHANNELS.imageClassifierAction, request),
  runImageClassifier: (request) => ipcRenderer.invoke(IPC_CHANNELS.imageClassifierRun, request),
  runImageClassifierResultAction: (request) => ipcRenderer.invoke(IPC_CHANNELS.imageClassifierResultAction, request),
  runImageClassifierStream: (request, onEvent) => {
    const channel = `${IPC_EVENTS.imageClassifierStreamPrefix}${randomUUID()}`
    const listener = (_event, payload) => {
      onEvent(payload)
    }
    ipcRenderer.on(channel, listener)
    return ipcRenderer.invoke(IPC_CHANNELS.imageClassifierRunStream, {
      ...request,
      eventChannel: channel,
    }).finally(() => {
      ipcRenderer.removeListener(channel, listener)
    })
  },
})
