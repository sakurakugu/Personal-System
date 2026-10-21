import { IPC_EVENTS } from './ipc-channels.mjs'

const WIDGET_STATE_EVENT_CHANNEL = IPC_EVENTS.widgetStateChanged
const WIDGET_WINDOW_WIDTH = 380
const WIDGET_WINDOW_MIN_HEIGHT = 46
const DEFAULT_WIDGET_WINDOW_STATE = {
  alwaysOnTop: true,
  movable: false,
  surfaceOpacity: 100,
  showCloseButton: true,
}

export {
  DEFAULT_WIDGET_WINDOW_STATE,
  WIDGET_STATE_EVENT_CHANNEL,
  WIDGET_WINDOW_MIN_HEIGHT,
  WIDGET_WINDOW_WIDTH,
}
