import {
  关闭桌面小工具窗口,
  获取桌面小工具窗口状态,
  监听桌面小工具窗口状态变更,
  打开桌面主窗口,
  设置桌面小工具窗口状态,
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

  function 标准化不透明度(value: number) {
    if (!Number.isFinite(value)) {
      return 100
    }
    return Math.max(50, Math.min(100, Math.round(value)))
  }

  async function 同步小工具状态() {
    try {
      const state = await 获取桌面小工具窗口状态()
      widgetAlwaysOnTop.value = state.alwaysOnTop
      widgetMovable.value = state.movable
      widgetSurfaceOpacity.value = 标准化不透明度(state.surfaceOpacity)
      widgetShowCloseButton.value = state.showCloseButton
    } catch (error) {
      console.error('读取小工具窗口状态失败', error)
    }
  }

  async function 更新小工具状态(payload: {
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
      const state = await 设置桌面小工具窗口状态(payload)
      widgetAlwaysOnTop.value = state.alwaysOnTop
      widgetMovable.value = state.movable
      widgetSurfaceOpacity.value = 标准化不透明度(state.surfaceOpacity)
      widgetShowCloseButton.value = state.showCloseButton
    } catch (error) {
      console.error('更新小工具窗口状态失败', error)
      ElMessage.error('更新小工具窗口状态失败')
    } finally {
      settingWidgetState.value = false
    }
  }

  function 清除长按置顶定时器() {
    if (!pinLongPressTimer) {
      return
    }

    window.clearTimeout(pinLongPressTimer)
    pinLongPressTimer = null
  }

  function 开始长按置顶() {
    pinLongPressing.value = false
    清除长按置顶定时器()
    pinLongPressTimer = window.setTimeout(() => {
      pinLongPressing.value = true
      void 更新小工具状态({
        movable: !widgetMovable.value,
      })
    }, pinLongPressDuration)
  }

  function 取消长按置顶() {
    清除长按置顶定时器()
  }

  async function 处理置顶按钮点击() {
    if (pinLongPressing.value) {
      pinLongPressing.value = false
      return
    }

    await 更新小工具状态({
      alwaysOnTop: !widgetAlwaysOnTop.value,
    })
  }

  async function 处理打开主窗口() {
    try {
      await 打开桌面主窗口()
    } catch (error) {
      console.error('显示主窗口失败', error)
      ElMessage.error('显示主窗口失败')
    }
  }

  async function 处理关闭窗口() {
    try {
      await 关闭桌面小工具窗口()
    } catch (error) {
      console.error('关闭小工具失败', error)
      ElMessage.error('关闭小工具失败')
    }
  }

  function 调度表面不透明度同步() {
    if (widgetSurfaceOpacitySyncTimer !== null) {
      window.clearTimeout(widgetSurfaceOpacitySyncTimer)
    }

    widgetSurfaceOpacitySyncTimer = window.setTimeout(() => {
      widgetSurfaceOpacitySyncTimer = null
      void 更新小工具状态({
        surfaceOpacity: widgetSurfaceOpacity.value,
      })
    }, 120)
  }

  function 重置小工具表面不透明度() {
    widgetSurfaceOpacity.value = defaultWidgetSurfaceOpacity
  }

  onMounted(() => {
    removeWidgetStateListener = 监听桌面小工具窗口状态变更((payload) => {
      widgetAlwaysOnTop.value = payload.alwaysOnTop
      widgetMovable.value = payload.movable
      widgetSurfaceOpacity.value = 标准化不透明度(payload.surfaceOpacity)
      widgetShowCloseButton.value = payload.showCloseButton
    })
    void 同步小工具状态()
  })

  onBeforeUnmount(() => {
    清除长按置顶定时器()
    if (widgetSurfaceOpacitySyncTimer !== null) {
      window.clearTimeout(widgetSurfaceOpacitySyncTimer)
      widgetSurfaceOpacitySyncTimer = null
    }
    removeWidgetStateListener()
  })

  watch(widgetSurfaceOpacity, (value) => {
    const normalized = 标准化不透明度(value)
    if (normalized !== value) {
      widgetSurfaceOpacity.value = normalized
      return
    }
    调度表面不透明度同步()
  })

  watch(widgetShowCloseButton, (value) => {
    void 更新小工具状态({
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
    beginPinLongPress: 开始长按置顶,
    cancelPinLongPress: 取消长按置顶,
    handleCloseWindow: 处理关闭窗口,
    handleOpenMainWindow: 处理打开主窗口,
    handlePinButtonClick: 处理置顶按钮点击,
    resetWidgetSurfaceOpacity: 重置小工具表面不透明度,
  }
}
