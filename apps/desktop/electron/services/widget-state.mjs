import { app } from 'electron'
import path from 'node:path'

import { DEFAULT_WIDGET_WINDOW_STATE } from '../shared/constants.mjs'
import { readJsonFile, writePrettyJson } from '../shared/json-file.mjs'

function getWidgetWindowStatePath() {
  return path.join(app.getPath('userData'), 'desktop-widget', 'window-state.json')
}

function normalizeWidgetWindowState(value) {
  const normalizedSurfaceOpacity = Number(value?.surfaceOpacity)
  const surfaceOpacity = Number.isFinite(normalizedSurfaceOpacity)
    ? Math.max(0, Math.min(100, Math.round(normalizedSurfaceOpacity)))
    : DEFAULT_WIDGET_WINDOW_STATE.surfaceOpacity

  return {
    alwaysOnTop: typeof value?.alwaysOnTop === 'boolean'
      ? value.alwaysOnTop
      : DEFAULT_WIDGET_WINDOW_STATE.alwaysOnTop,
    movable: typeof value?.movable === 'boolean'
      ? value.movable
      : DEFAULT_WIDGET_WINDOW_STATE.movable,
    surfaceOpacity,
    showCloseButton: typeof value?.showCloseButton === 'boolean'
      ? value.showCloseButton
      : DEFAULT_WIDGET_WINDOW_STATE.showCloseButton,
  }
}

let widgetWindowState = { ...DEFAULT_WIDGET_WINDOW_STATE }
let widgetWindowStateInitialized = false
let widgetWindowStatePromise = null

async function ensureWidgetWindowStateLoaded() {
  if (widgetWindowStateInitialized) {
    return widgetWindowState
  }

  if (!widgetWindowStatePromise) {
    widgetWindowStatePromise = (async () => {
      const payload = await readJsonFile(getWidgetWindowStatePath(), DEFAULT_WIDGET_WINDOW_STATE)
      widgetWindowState = normalizeWidgetWindowState(payload)
      widgetWindowStateInitialized = true
      return widgetWindowState
    })().finally(() => {
      widgetWindowStatePromise = null
    })
  }

  return await widgetWindowStatePromise
}

async function saveWidgetWindowState(nextState) {
  widgetWindowState = normalizeWidgetWindowState(nextState)
  widgetWindowStateInitialized = true
  await writePrettyJson(getWidgetWindowStatePath(), widgetWindowState)
  return widgetWindowState
}

function getStoredWidgetWindowState() {
  return widgetWindowState
}

export {
  ensureWidgetWindowStateLoaded,
  getStoredWidgetWindowState,
  normalizeWidgetWindowState,
  saveWidgetWindowState,
}
