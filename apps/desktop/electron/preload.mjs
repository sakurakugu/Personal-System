import { contextBridge, ipcRenderer } from 'electron'
import { randomUUID } from 'node:crypto'

contextBridge.exposeInMainWorld('personalSystemDesktop', {
  runtime: 'electron',
  openDesktopMainWindow: () => ipcRenderer.invoke('desktop:window:open-main'),
  openDesktopWidgetWindow: () => ipcRenderer.invoke('desktop:window:open-widget'),
  closeDesktopWidgetWindow: () => ipcRenderer.invoke('desktop:window:close-widget'),
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
