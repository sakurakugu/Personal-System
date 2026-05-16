import {
  computed,
  nextTick,
  onBeforeUnmount,
  onMounted,
  ref,
  watch,
  type ComputedRef,
  type Ref,
} from 'vue'
import {
  分隔线宽度,
  最大目录树宽度,
  最小主区域宽度,
  最小目录树宽度,
  桌面端初始渲染资源数量,
  桌面端增量渲染资源数量,
  移动端初始渲染资源数量,
  移动端增量渲染资源数量,
} from '../../core/shared'
import type {
  排序方式,
  资源展示项,
} from '../../core/shared'

export function 使用文件页面视口(options: {
  当前展示资源列表: Ref<资源展示项[]> | ComputedRef<资源展示项[]>
  当前排序: Ref<排序方式> | ComputedRef<排序方式>
  关闭右键菜单: () => void
  初始化加载: () => void | Promise<void>
}) {
  const 浏览器布局容器 = ref<globalThis.HTMLElement | null>(null)
  const 资源列表底部哨兵 = ref<globalThis.HTMLDivElement | null>(null)
  const 目录树宽度 = ref(280)
  const 正在拖动分隔线 = ref(false)
  const 当前渲染资源数量 = ref(桌面端初始渲染资源数量)
  let 资源列表观察器: globalThis.IntersectionObserver | null = null

  const 当前渲染资源列表 = computed<资源展示项[]>(() => (
    options.当前展示资源列表.value.slice(0, 当前渲染资源数量.value)
  ))
  const 当前页资源总数 = computed(() => options.当前展示资源列表.value.length)
  const 当前已渲染资源总数 = computed(() => 当前渲染资源列表.value.length)
  const 是否还有更多资源待渲染 = computed(() => 当前已渲染资源总数.value < 当前页资源总数.value)
  const 剩余待渲染资源数 = computed(() => (
    Math.max(0, 当前页资源总数.value - 当前已渲染资源总数.value)
  ))
  const 浏览器布局样式 = computed<Record<string, string>>(() => ({
    '--explorer-sidebar-width': `${目录树宽度.value}px`,
  }))

  function 计算最大目录树宽度() {
    const layoutWidth = 浏览器布局容器.value?.clientWidth ?? 0
    if (layoutWidth <= 0) {
      return 最大目录树宽度
    }
    return Math.max(
      最小目录树宽度,
      Math.min(最大目录树宽度, layoutWidth - 最小主区域宽度 - 分隔线宽度),
    )
  }

  function 约束目录树宽度(width: number) {
    return Math.min(Math.max(width, 最小目录树宽度), 计算最大目录树宽度())
  }

  function 同步目录树宽度() {
    目录树宽度.value = 约束目录树宽度(目录树宽度.value)
  }

  function 获取初始渲染资源数量() {
    if (typeof window !== 'undefined' && window.innerWidth <= 768) {
      return 移动端初始渲染资源数量
    }
    return 桌面端初始渲染资源数量
  }

  function 获取增量渲染资源数量() {
    if (typeof window !== 'undefined' && window.innerWidth <= 768) {
      return 移动端增量渲染资源数量
    }
    return 桌面端增量渲染资源数量
  }

  function 重置资源列表渲染进度() {
    当前渲染资源数量.value = 获取初始渲染资源数量()
  }

  function 加载更多资源() {
    if (!是否还有更多资源待渲染.value) {
      return
    }
    当前渲染资源数量.value = Math.min(
      当前页资源总数.value,
      当前渲染资源数量.value + 获取增量渲染资源数量(),
    )
  }

  function 销毁资源列表观察器() {
    资源列表观察器?.disconnect()
    资源列表观察器 = null
  }

  function 更新资源列表观察器() {
    销毁资源列表观察器()
    if (!是否还有更多资源待渲染.value || !资源列表底部哨兵.value || typeof window.IntersectionObserver === 'undefined') {
      return
    }

    资源列表观察器 = new window.IntersectionObserver((entries) => {
      if (entries.some((entry) => entry.isIntersecting)) {
        加载更多资源()
      }
    }, {
      root: null,
      rootMargin: '240px 0px',
      threshold: 0,
    })
    资源列表观察器.observe(资源列表底部哨兵.value)
  }

  function 开始拖动分隔线(event: globalThis.PointerEvent) {
    if (window.innerWidth <= 960) {
      return
    }
    event.preventDefault()
    正在拖动分隔线.value = true
    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'
  }

  function 处理拖动分隔线(event: globalThis.PointerEvent) {
    if (!正在拖动分隔线.value || !浏览器布局容器.value) {
      return
    }
    const layoutRect = 浏览器布局容器.value.getBoundingClientRect()
    目录树宽度.value = 约束目录树宽度(event.clientX - layoutRect.left)
  }

  function 停止拖动分隔线() {
    if (!正在拖动分隔线.value) {
      return
    }
    正在拖动分隔线.value = false
    document.body.style.cursor = ''
    document.body.style.userSelect = ''
  }

  function 处理窗口尺寸变化() {
    options.关闭右键菜单()
    if (window.innerWidth <= 960) {
      停止拖动分隔线()
    }
    同步目录树宽度()
  }

  function 处理窗口失焦() {
    options.关闭右键菜单()
    停止拖动分隔线()
  }

  onMounted(() => {
    window.addEventListener('click', options.关闭右键菜单)
    window.addEventListener('resize', 处理窗口尺寸变化)
    window.addEventListener('blur', 处理窗口失焦)
    window.addEventListener('pointermove', 处理拖动分隔线)
    window.addEventListener('pointerup', 停止拖动分隔线)
    window.addEventListener('pointercancel', 停止拖动分隔线)
    window.requestAnimationFrame(同步目录树宽度)
    void options.初始化加载()
  })

  onBeforeUnmount(() => {
    window.removeEventListener('click', options.关闭右键菜单)
    window.removeEventListener('resize', 处理窗口尺寸变化)
    window.removeEventListener('blur', 处理窗口失焦)
    window.removeEventListener('pointermove', 处理拖动分隔线)
    window.removeEventListener('pointerup', 停止拖动分隔线)
    window.removeEventListener('pointercancel', 停止拖动分隔线)
    停止拖动分隔线()
    销毁资源列表观察器()
  })

  watch(
    [
      () => options.当前展示资源列表.value,
      options.当前排序,
    ],
    async () => {
      重置资源列表渲染进度()
      await nextTick()
      更新资源列表观察器()
    },
    { immediate: true },
  )

  watch(
    [当前渲染资源数量, 资源列表底部哨兵],
    async () => {
      await nextTick()
      更新资源列表观察器()
    },
  )

  return {
    浏览器布局容器,
    资源列表底部哨兵,
    目录树宽度,
    正在拖动分隔线,
    当前渲染资源数量,
    当前渲染资源列表,
    当前页资源总数,
    当前已渲染资源总数,
    是否还有更多资源待渲染,
    剩余待渲染资源数,
    浏览器布局样式,
    获取增量渲染资源数量,
    加载更多资源,
    开始拖动分隔线,
  }
}
