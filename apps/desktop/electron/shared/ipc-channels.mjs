const IPC_CHANNELS = {
  authLoadToken: 'desktop:auth:load-token',
  authSaveToken: 'desktop:auth:save-token',
  widgetGetState: 'desktop:widget:get-state',
  widgetSetContentHeight: 'desktop:widget:set-content-height',
  widgetSetState: 'desktop:widget:set-state',
  windowCloseCurrent: 'desktop:window:close-current',
  windowCloseWidget: 'desktop:window:close-widget',
  windowGetCurrentState: 'desktop:window:get-current-state',
  windowMinimizeCurrent: 'desktop:window:minimize-current',
  windowOpenMain: 'desktop:window:open-main',
  windowOpenWidget: 'desktop:window:open-widget',
  windowToggleMaximizeCurrent: 'desktop:window:toggle-maximize-current',
}

const IPC_EVENTS = {
  widgetStateChanged: 'desktop:widget:state-changed',
  windowStateChanged: 'desktop:window:state-changed',
}

export {
  IPC_CHANNELS,
  IPC_EVENTS,
}
