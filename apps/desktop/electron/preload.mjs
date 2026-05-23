import { contextBridge, ipcRenderer } from 'electron'
import { randomUUID } from 'node:crypto'

contextBridge.exposeInMainWorld('personalSystemDesktop', {
  runtime: 'electron',
  openDesktopMainWindow: () => ipcRenderer.invoke('desktop:window:open-main'),
  openDesktopWidgetWindow: () => ipcRenderer.invoke('desktop:window:open-widget'),
  closeDesktopWidgetWindow: () => ipcRenderer.invoke('desktop:window:close-widget'),
  getDesktopWidgetWindowState: () => ipcRenderer.invoke('desktop:widget:get-state'),
  setDesktopWidgetWindowState: (payload) => ipcRenderer.invoke('desktop:widget:set-state', payload),
  setDesktopWidgetWindowContentHeight: (height) => ipcRenderer.invoke('desktop:widget:set-content-height', height),
  onDesktopWidgetWindowStateChange: (listener) => {
    const wrappedListener = (_event, payload) => {
      listener(payload)
    }
    ipcRenderer.on('desktop:widget:state-changed', wrappedListener)
    return () => {
      ipcRenderer.removeListener('desktop:widget:state-changed', wrappedListener)
    }
  },
  closeCurrentWindow: () => ipcRenderer.invoke('desktop:window:close-current'),
  minimizeCurrentWindow: () => ipcRenderer.invoke('desktop:window:minimize-current'),
  toggleMaximizeCurrentWindow: () => ipcRenderer.invoke('desktop:window:toggle-maximize-current'),
  getCurrentWindowState: () => ipcRenderer.invoke('desktop:window:get-current-state'),
  onCurrentWindowStateChange: (listener) => {
    const wrappedListener = (_event, payload) => {
      listener(payload)
    }
    ipcRenderer.on('desktop:window:state-changed', wrappedListener)
    return () => {
      ipcRenderer.removeListener('desktop:window:state-changed', wrappedListener)
    }
  },
  loadDesktopAuthToken: () => ipcRenderer.invoke('desktop:auth:load-token'),
  saveDesktopAuthToken: (token) => ipcRenderer.invoke('desktop:auth:save-token', token),
  syncWidgetAuthToken: (payload) => ipcRenderer.invoke('desktop:widget:sync-token', payload),
  checkGitEnvironment: () => ipcRenderer.invoke('desktop:windows:check-git'),
  readMinecraftServerStorage: () => ipcRenderer.invoke('desktop:minecraft:read-storage'),
  writeMinecraftServerStorage: (data) => ipcRenderer.invoke('desktop:minecraft:write-storage', data),
  queryMinecraftServer: (request) => ipcRenderer.invoke('desktop:minecraft:query', request),
  convertFileSrc: (filePath) => ipcRenderer.invoke('desktop:file:to-url', filePath),
  imageToolsGetCapabilities: () => ipcRenderer.invoke('desktop:image-tools:get-capabilities'),
  imageToolsSelectInputs: () => ipcRenderer.invoke('desktop:image-tools:select-inputs'),
  imageToolsSelectOutputPath: (mode, options) => ipcRenderer.invoke('desktop:image-tools:select-output-path', mode, options),
  imageToolsImportFromPaths: (paths) => ipcRenderer.invoke('desktop:image-tools:import-from-paths', paths),
  imageToolsConvert: (request) => ipcRenderer.invoke('desktop:image-tools:convert', request),
  imageToolsEdit: (request) => ipcRenderer.invoke('desktop:image-tools:edit', request),
  imageToolsStitch: (request) => ipcRenderer.invoke('desktop:image-tools:stitch', request),
  imageToolsRelease: (resourceIds) => ipcRenderer.invoke('desktop:image-tools:release', resourceIds),
  checkImageClassifierEnvironment: () => ipcRenderer.invoke('desktop:image-classifier:check-environment'),
  selectImageClassifierInputs: (mode) => ipcRenderer.invoke('desktop:image-classifier:select-inputs', mode),
  selectImageClassifierOutputPath: (mode) => ipcRenderer.invoke('desktop:image-classifier:select-output-path', mode),
  discoverImageClassifierInputs: (request) => ipcRenderer.invoke('desktop:image-classifier:discover-inputs', request),
  stopImageClassifier: () => ipcRenderer.invoke('desktop:image-classifier:stop'),
  imageClassifierAction: (request) => ipcRenderer.invoke('desktop:image-classifier:action', request),
  runImageClassifier: (request) => ipcRenderer.invoke('desktop:image-classifier:run', request),
  runImageClassifierResultAction: (request) => ipcRenderer.invoke('desktop:image-classifier:result-action', request),
  runImageClassifierStream: (request, onEvent) => {
    const channel = `desktop:image-classifier:stream:${randomUUID()}`
    const listener = (_event, payload) => {
      onEvent(payload)
    }
    ipcRenderer.on(channel, listener)
    return ipcRenderer.invoke('desktop:image-classifier:run-stream', {
      ...request,
      eventChannel: channel,
    }).finally(() => {
      ipcRenderer.removeListener(channel, listener)
    })
  },
})
