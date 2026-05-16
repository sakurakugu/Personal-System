/* global Event, MouseEvent, PointerEvent, TouchEvent */
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import type { 侧栏布局配置, 侧栏模式 } from '../sidebar-layout'

const 默认配置: Required<侧栏布局配置> = {
  默认展开宽度: 200,
  紧凑宽度: 64,
  最小展开宽度: 140,
  最大展开宽度: 320,
  启用拖拽的最小视口宽度: 960,
  主内容最小宽度: 360,
  自动收紧比例: 0.22,
  自动展开比例: 0.2,
  隐藏触发器最小底部间距: 80,
  隐藏触发器默认底部偏移: 12,
}

export function useSidebarLayout(storageKey: string, config: 侧栏布局配置 = {}) {
  const 配置 = { ...默认配置, ...config }
  const viewportWidth = ref<number | null>(null)
  const userPreferredSiderMode = ref<侧栏模式>('expanded')
  const siderMode = ref<侧栏模式>('expanded')
  const autoCompact = ref(false)
  const expandedSiderWidth = ref(配置.默认展开宽度)
  const handleBottom = ref(配置.隐藏触发器默认底部偏移)
  const isHandleDragging = ref(false)
  const hasMoved = ref(false)
  const isResizing = ref(false)
  const dragState = reactive({
    startY: 0,
    startBottom: 0,
  })
  const resizeState = reactive({
    startX: 0,
    startWidth: 配置.默认展开宽度,
  })

  const isCompact = computed(() => siderMode.value === 'compact')
  const isHidden = computed(() => siderMode.value === 'hidden')
  const showResizeHandle = computed(() => (
    siderMode.value === 'expanded'
    && !autoCompact.value
    && (viewportWidth.value ?? 0) > 配置.启用拖拽的最小视口宽度
  ))
  const currentSiderWidth = computed(() => {
    if (siderMode.value === 'hidden') return 0
    if (siderMode.value === 'compact') return 配置.紧凑宽度
    return expandedSiderWidth.value
  })
  const triggerText = computed(() => {
    if (isHidden.value) return '展开侧栏'
    if (isCompact.value) return '继续收起'
    return '收起侧栏'
  })

  function 同步视口宽度() {
    viewportWidth.value = window.innerWidth
  }

  function 读取侧栏偏好状态(): 侧栏模式 {
    const value = window.localStorage.getItem(storageKey)
    if (value === 'expanded' || value === 'compact' || value === 'hidden') {
      return value
    }
    return 'expanded'
  }

  function 保存侧栏偏好状态(mode: 侧栏模式) {
    window.localStorage.setItem(storageKey, mode)
  }

  function 读取侧栏宽度偏好值() {
    const value = Number.parseInt(window.localStorage.getItem(`${storageKey}_width`) || '', 10)
    return Number.isFinite(value) ? value : null
  }

  function 保存侧栏宽度偏好值(nextWidth: number) {
    window.localStorage.setItem(`${storageKey}_width`, String(Math.round(nextWidth)))
  }

  function 切换侧栏() {
    if (isHidden.value) {
      const width = viewportWidth.value ?? 0
      const nextMode = width && expandedSiderWidth.value / width >= 配置.自动收紧比例 ? 'compact' : 'expanded'
      userPreferredSiderMode.value = nextMode
      保存侧栏偏好状态(nextMode)
      siderMode.value = nextMode
      autoCompact.value = false
      return
    }
    if (isCompact.value) {
      userPreferredSiderMode.value = 'hidden'
      保存侧栏偏好状态('hidden')
      siderMode.value = 'hidden'
      autoCompact.value = false
      return
    }
    userPreferredSiderMode.value = 'compact'
    保存侧栏偏好状态('compact')
    siderMode.value = 'compact'
    autoCompact.value = false
  }

  function 获取最大展开侧栏宽度() {
    if (!viewportWidth.value) {
      return 配置.最大展开宽度
    }
    return Math.max(
      配置.最小展开宽度,
      Math.min(配置.最大展开宽度, viewportWidth.value - 配置.主内容最小宽度),
    )
  }

  function 约束展开侧栏宽度(nextWidth: number) {
    return Math.min(Math.max(nextWidth, 配置.最小展开宽度), 获取最大展开侧栏宽度())
  }

  function 同步展开侧栏宽度() {
    expandedSiderWidth.value = 约束展开侧栏宽度(expandedSiderWidth.value)
  }

  function 应用自动收起() {
    if (!viewportWidth.value) return
    if (userPreferredSiderMode.value === 'hidden') {
      siderMode.value = 'hidden'
      autoCompact.value = false
      return
    }
    if (userPreferredSiderMode.value === 'compact') {
      siderMode.value = 'compact'
      autoCompact.value = false
      return
    }

    const ratio = expandedSiderWidth.value / viewportWidth.value
    if (ratio >= 配置.自动收紧比例) {
      siderMode.value = 'compact'
      autoCompact.value = true
      return
    }

    if (autoCompact.value && ratio <= 配置.自动展开比例) {
      siderMode.value = 'expanded'
      autoCompact.value = false
    }
  }

  function 获取安全区域底部() {
    const safeArea = parseInt(window.getComputedStyle(document.documentElement).getPropertyValue('--app-safe-area-bottom') || '0')
    return safeArea || 0
  }

  function 获取最大底部() {
    return window.innerHeight - 配置.隐藏触发器最小底部间距
  }

  function 处理手柄触摸开始(e: Event) {
    isHandleDragging.value = true
    hasMoved.value = false
    dragState.startBottom = handleBottom.value

    if (e instanceof TouchEvent) {
      dragState.startY = e.touches[0].clientY
    } else if (e instanceof MouseEvent) {
      dragState.startY = e.clientY
    }
  }

  function 处理手柄触摸移动(e: Event) {
    if (!isHandleDragging.value) return
    e.preventDefault()

    let clientY = 0
    if (e instanceof TouchEvent) {
      clientY = e.touches[0].clientY
    } else if (e instanceof MouseEvent) {
      clientY = e.clientY
    }

    if (Math.abs(clientY - dragState.startY) > 3) {
      hasMoved.value = true
    }

    const deltaY = dragState.startY - clientY
    const newBottom = dragState.startBottom + deltaY
    const maxBottom = 获取最大底部()
    const safeArea = 获取安全区域底部()
    const minBottom = 配置.隐藏触发器默认底部偏移 + safeArea

    handleBottom.value = Math.max(minBottom, Math.min(maxBottom, newBottom))
  }

  function 处理手柄触摸结束() {
    isHandleDragging.value = false
    setTimeout(() => {
      hasMoved.value = false
    }, 50)
  }

  function 处理调整器指针按下(event: PointerEvent) {
    if (!showResizeHandle.value) {
      return
    }
    event.preventDefault()
    isResizing.value = true
    resizeState.startX = event.clientX
    resizeState.startWidth = expandedSiderWidth.value
    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'
  }

  function 处理调整器指针移动(event: PointerEvent) {
    if (!isResizing.value) {
      return
    }
    const deltaX = event.clientX - resizeState.startX
    expandedSiderWidth.value = 约束展开侧栏宽度(resizeState.startWidth + deltaX)
  }

  function 处理调整器指针结束() {
    if (!isResizing.value) {
      return
    }
    isResizing.value = false
    document.body.style.cursor = ''
    document.body.style.userSelect = ''
    保存侧栏宽度偏好值(expandedSiderWidth.value)
  }

  function 处理手柄点击() {
    if (hasMoved.value) {
      return
    }
    切换侧栏()
  }

  onMounted(() => {
    同步视口宽度()
    userPreferredSiderMode.value = 读取侧栏偏好状态()
    expandedSiderWidth.value = 约束展开侧栏宽度(读取侧栏宽度偏好值() ?? 配置.默认展开宽度)
    siderMode.value = userPreferredSiderMode.value
    应用自动收起()

    document.body.style.overflow = 'hidden'

    window.addEventListener('resize', 同步视口宽度)
    window.addEventListener('mousemove', 处理手柄触摸移动)
    window.addEventListener('mouseup', 处理手柄触摸结束)
    window.addEventListener('touchmove', 处理手柄触摸移动, { passive: false })
    window.addEventListener('touchend', 处理手柄触摸结束)
    window.addEventListener('pointermove', 处理调整器指针移动)
    window.addEventListener('pointerup', 处理调整器指针结束)
    window.addEventListener('pointercancel', 处理调整器指针结束)
  })

  onBeforeUnmount(() => {
    document.body.style.overflow = ''

    window.removeEventListener('resize', 同步视口宽度)
    window.removeEventListener('mousemove', 处理手柄触摸移动)
    window.removeEventListener('mouseup', 处理手柄触摸结束)
    window.removeEventListener('touchmove', 处理手柄触摸移动)
    window.removeEventListener('touchend', 处理手柄触摸结束)
    window.removeEventListener('pointermove', 处理调整器指针移动)
    window.removeEventListener('pointerup', 处理调整器指针结束)
    window.removeEventListener('pointercancel', 处理调整器指针结束)
    处理调整器指针结束()
  })

  watch(viewportWidth, () => {
    if (isResizing.value && (viewportWidth.value ?? 0) <= 配置.启用拖拽的最小视口宽度) {
      处理调整器指针结束()
    }
    同步展开侧栏宽度()
    应用自动收起()
  }, { immediate: true })

  return {
    viewportWidth,
    siderMode,
    expandedSiderWidth,
    handleBottom,
    isHandleDragging,
    isResizing,
    isCompact,
    isHidden,
    showResizeHandle,
    currentSiderWidth,
    triggerText,
    toggleSider: 切换侧栏,
    onHandleTouchStart: 处理手柄触摸开始,
    onHandleClick: 处理手柄点击,
    onResizerPointerDown: 处理调整器指针按下,
  }
}
