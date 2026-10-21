const IPC_CHANNELS = {
  appOpenWebConsole: 'desktop:app:open-web-console',
  authLoadToken: 'desktop:auth:load-token',
  authSaveToken: 'desktop:auth:save-token',
  widgetGetState: 'desktop:widget:get-state',
  widgetSetContentHeight: 'desktop:widget:set-content-height',
  widgetSetState: 'desktop:widget:set-state',
  windowCloseWidget: 'desktop:window:close-widget',
}

const IPC_EVENTS = {
  widgetStateChanged: 'desktop:widget:state-changed',
}

export {
  IPC_CHANNELS,
  IPC_EVENTS,
}
