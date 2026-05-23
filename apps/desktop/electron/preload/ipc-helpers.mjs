function createInvokeBridge(ipcRenderer, channel) {
  return (...args) => ipcRenderer.invoke(channel, ...args)
}

function createPayloadListenerBridge(ipcRenderer, channel) {
  return (listener) => {
    const wrappedListener = (_event, payload) => {
      listener(payload)
    }

    ipcRenderer.on(channel, wrappedListener)
    return () => {
      ipcRenderer.removeListener(channel, wrappedListener)
    }
  }
}

export {
  createInvokeBridge,
  createPayloadListenerBridge,
}
