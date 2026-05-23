import { IPC_EVENTS } from './ipc-channels.mjs'

const WINDOW_STATE_EVENT_CHANNEL = IPC_EVENTS.windowStateChanged
const WIDGET_STATE_EVENT_CHANNEL = IPC_EVENTS.widgetStateChanged
const WIDGET_WINDOW_WIDTH = 380
const WIDGET_WINDOW_MIN_HEIGHT = 46
const DEFAULT_WIDGET_WINDOW_STATE = {
  alwaysOnTop: true,
  movable: false,
  surfaceOpacity: 100,
  showCloseButton: true,
}

const IMAGE_CLASSIFIER_STOP_MESSAGE = '图片分类已停止。'
const IMAGE_CLASSIFIER_RELATIVE_DIR = ['apps', 'desktop', 'python', 'ai-media-processor']
const IMAGE_CLASSIFIER_STOP_ENV_KEY = 'PERSONAL_SYSTEM_IMAGE_CLASSIFIER_STOP_REQUESTED'
const IMAGE_TOOLS_RELATIVE_DIR = ['apps', 'desktop', 'python', 'image-tools']
const MINECRAFT_TOOL_RELATIVE_DIR = ['apps', 'desktop', 'python', 'minecraft-tool']
const DESKTOP_PYTHON_RESOURCE_DIR = 'python'
const DESKTOP_EMBEDDED_PYTHON_DIR = 'python-runtime'
const DESKTOP_PYTHON_MODE_ENV_KEY = 'PERSONAL_SYSTEM_DESKTOP_PYTHON_MODE'

const IMAGE_CLASSIFIER_MEDIA_EXTENSIONS = [
  '.png',
  '.jpg',
  '.jpeg',
  '.webp',
  '.bmp',
  '.gif',
  '.heic',
  '.heif',
  '.avif',
  '.mp4',
  '.mov',
  '.mkv',
  '.avi',
  '.webm',
  '.m4v',
]

export {
  DEFAULT_WIDGET_WINDOW_STATE,
  DESKTOP_EMBEDDED_PYTHON_DIR,
  DESKTOP_PYTHON_MODE_ENV_KEY,
  DESKTOP_PYTHON_RESOURCE_DIR,
  IMAGE_CLASSIFIER_MEDIA_EXTENSIONS,
  IMAGE_CLASSIFIER_RELATIVE_DIR,
  IMAGE_CLASSIFIER_STOP_ENV_KEY,
  IMAGE_CLASSIFIER_STOP_MESSAGE,
  IMAGE_TOOLS_RELATIVE_DIR,
  MINECRAFT_TOOL_RELATIVE_DIR,
  WIDGET_STATE_EVENT_CHANNEL,
  WIDGET_WINDOW_MIN_HEIGHT,
  WIDGET_WINDOW_WIDTH,
  WINDOW_STATE_EVENT_CHANNEL,
}
