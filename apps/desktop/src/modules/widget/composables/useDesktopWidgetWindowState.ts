import {
  closeDesktopWidgetWindow,
  getDesktopWidgetWindowState,
  onDesktopWidgetWindowStateChange,
  openDesktopMainWindow,
  setDesktopWidgetWindowState,
} from '@/shared/window-manager'
import { ElMessage } from 'element-plus'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'

export function useDesktopWidgetWindowState() {
  const widgetAlwaysOnTop = ref(true)
  const widgetMovable = ref(false)
  const pinLongPressing = ref(false)
  const settingWidgetState = ref(false)
  const widgetSurfaceOpacity = ref(100)
  const widgetShowCloseButton = ref(true)
  const pinButtonIcon = 'mdi:pin'
  const pinLongPressDuration = 450
  const defaultWidgetSurfaceOpacity = 100

  let pinLongPressTimer: number | null = null
  let removeWidgetStateListener = () => {}
  let widgetSurfaceOpacitySyncTimer: number | null = null

  const pinButtonIconClass = computed(() => ({
    'pin-button__icon--movable': widgetMovable.value,
  }))
  const pinButtonIconShellClass = computed(() => ({
    'pin-button__icon-shell--unpinned': !widgetAlwaysOnTop.value,
  }))
  const pinButtonTitle = computed(() => {
    const movableText = widgetMovable.value ? '当前允许移动，长按后锁定位置' : '当前禁止移动，长按后允许移动'
    const alwaysOnTopText = widgetAlwaysOnTop.value ? '点击后取消置顶' : '点击后置顶'
    return `${movableText}；${alwaysOnTopText}`
  })
  const widgetSurfaceOpaque = computed(() => widgetSurfaceOpacity.value >= 100)

  function normalizeOpacity(value: number) {
    if (!Number.isFinite(value)) {
      return 100
    }
    return Math.max(50, Math.min(100, Math.round(value)))
  }

  async function syncWidgetState() {
    try {
      const state = await getDesktopWidgetWindowState()
      widgetAlwaysOnTop.value = state.alwaysOnTop
      widgetMovable.value = state.movable
      widgetSurfaceOpacity.value = normalizeOpacity(state.surfaceOpacity)
      widgetShowCloseButton.value = state.showCloseButton
    } catch (error) {
      console.error('读取小工具窗口状态失败', error)
    }
  }

  async function updateWidgetState(payload: {
    alwaysOnTop?: boolean
    movable?: boolean
    surfaceOpacity?: number
    showCloseButton?: boolean
  }) {
    if (settingWidgetState.value) {
      return
    }

    settingWidgetState.value = true
    try {
      const state = await setDesktopWidgetWindowState(payload)
      widgetAlwaysOnTop.value = state.alwaysOnTop
      widgetMovable.value = state.movable
      widgetSurfaceOpacity.value = normalizeOpacity(state.surfaceOpacity)
      widgetShowCloseButton.value = state.showCloseButton
    } catch (error) {
      console.error('更新小工具窗口状态失败', error)
      ElMessage.error('更新小工具窗口状态失败')
    } finally {
      settingWidgetState.value = false
    }
  }

  function clearPinLongPressTimer() {
    if (!pinLongPressTimer) {
      return
    }

    window.clearTimeout(pinLongPressTimer)
    pinLongPressTimer = null
  }

  function beginPinLongPress() {
    pinLongPressing.value = false
    clearPinLongPressTimer()
    pinLongPressTimer = window.setTimeout(() => {
      pinLongPressing.value = true
      void updateWidgetState({
        movable: !widgetMovable.value,
      })
    }, pinLongPressDuration)
  }

  function cancelPinLongPress() {
    clearPinLongPressTimer()
  }

  async function handlePinButtonClick() {
    if (pinLongPressing.value) {
      pinLongPressing.value = false
      return
    }

    await updateWidgetState({
      alwaysOnTop: !widgetAlwaysOnTop.value,
    })
  }

  async function handleOpenMainWindow() {
    try {
      await openDesktopMainWindow()
    } catch (error) {
      console.error('显示主窗口失败', error)
      ElMessage.error('显示主窗口失败')
    }
  }

  async function handleCloseWindow() {
    try {
      await closeDesktopWidgetWindow()
    } catch (error) {
      console.error('关闭小工具失败', error)
      ElMessage.error('关闭小工具失败')
    }
  }

  function scheduleSurfaceOpacitySync() {
    if (widgetSurfaceOpacitySyncTimer !== null) {
      window.clearTimeout(widgetSurfaceOpacitySyncTimer)
    }

    widgetSurfaceOpacitySyncTimer = window.setTimeout(() => {
      widgetSurfaceOpacitySyncTimer = null
      void updateWidgetState({
        surfaceOpacity: widgetSurfaceOpacity.value,
      })
    }, 120)
  }

  function resetWidgetSurfaceOpacity() {
    widgetSurfaceOpacity.value = defaultWidgetSurfaceOpacity
  }

  onMounted(() => {
    removeWidgetStateListener = onDesktopWidgetWindowStateChange((payload) => {
      widgetAlwaysOnTop.value = payload.alwaysOnTop
      widgetMovable.value = payload.movable
      widgetSurfaceOpacity.value = normalizeOpacity(payload.surfaceOpacity)
      widgetShowCloseButton.value = payload.showCloseButton
    })
    void syncWidgetState()
  })

  onBeforeUnmount(() => {
    clearPinLongPressTimer()
    if (widgetSurfaceOpacitySyncTimer !== null) {
      window.clearTimeout(widgetSurfaceOpacitySyncTimer)
      widgetSurfaceOpacitySyncTimer = null
    }
    removeWidgetStateListener()
  })

  watch(widgetSurfaceOpacity, (value) => {
    const normalized = normalizeOpacity(value)
    if (normalized !== value) {
      widgetSurfaceOpacity.value = normalized
      return
    }
    scheduleSurfaceOpacitySync()
  })

  watch(widgetShowCloseButton, (value) => {
    void updateWidgetState({
      showCloseButton: value,
    })
  })

  return {
    defaultWidgetSurfaceOpacity,
    pinButtonIcon,
    pinButtonIconClass,
    pinButtonIconShellClass,
    pinButtonTitle,
    settingWidgetState,
    widgetAlwaysOnTop,
    widgetMovable,
    widgetShowCloseButton,
    widgetSurfaceOpacity,
    widgetSurfaceOpaque,
    beginPinLongPress,
    cancelPinLongPress,
    handleCloseWindow,
    handleOpenMainWindow,
    handlePinButtonClick,
    resetWidgetSurfaceOpacity,
  }
}
