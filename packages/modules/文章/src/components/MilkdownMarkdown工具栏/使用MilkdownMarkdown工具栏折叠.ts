import { computed, nextTick, ref } from 'vue'
import type { ToolbarItem } from './MilkdownMarkdown工具栏类型'

interface 使用MilkdownMarkdown工具栏折叠选项 {
  toolbarItems: ToolbarItem[]
  getToolbarElement: () => HTMLElement | null
  getRootElement: () => HTMLElement | null
}

export function 使用MilkdownMarkdown工具栏折叠(options: 使用MilkdownMarkdown工具栏折叠选项) {
  const toolbarOverflowCount = ref(0)
  const toolbarItemWidthMap = ref<Record<number, number>>({})
  const toolbarMoreWidth = ref(36)
  const 工具栏更多键 = 'toolbar-overflow-more'
  const 工具栏公式索引 = options.toolbarItems.findIndex((item) => item.action === 'math')
  let 工具栏尺寸观察器: ResizeObserver | null = null
  let 工具栏折叠更新帧 = 0

  const 工具栏折叠候选索引 = computed(() => {
    if (工具栏公式索引 < 0) {
      return []
    }

    const indexes: number[] = []
    for (let index = 工具栏公式索引; index >= 0; index -= 1) {
      const item = options.toolbarItems[index]
      if (!item || item.type === 'separator' || item.type === 'spacer' || item.hidden?.()) {
        continue
      }
      indexes.push(index)
    }
    return indexes
  })
  const 溢出工具栏索引集合 = computed(() => new Set(工具栏折叠候选索引.value.slice(0, toolbarOverflowCount.value)))

  function shouldShowToolbarItem(item: ToolbarItem, index: number): boolean {
    return !item.hidden?.() && !溢出工具栏索引集合.value.has(index)
  }

  function shouldShowToolbarSeparator(index: number): boolean {
    const item = options.toolbarItems[index]
    if (!item || item.type !== 'separator' || !shouldShowToolbarItem(item, index)) {
      return false
    }

    if (!hasVisibleToolbarControlBefore(index) || !hasVisibleToolbarControlAfter(index)) {
      return false
    }

    const previousSeparatorIndex = findPreviousVisibleToolbarSeparatorIndex(index)
    return previousSeparatorIndex < 0 || hasVisibleToolbarControlBetween(previousSeparatorIndex, index)
  }

  function hasVisibleToolbarControlBefore(index: number): boolean {
    return hasVisibleToolbarControlBetween(-1, index)
  }

  function hasVisibleToolbarControlAfter(index: number): boolean {
    return hasVisibleToolbarControlBetween(index, options.toolbarItems.length)
  }

  function hasVisibleToolbarControlBetween(startIndex: number, endIndex: number): boolean {
    for (let index = startIndex + 1; index < endIndex; index += 1) {
      if (isVisibleToolbarControlIndex(index)) {
        return true
      }
    }
    return false
  }

  function findPreviousVisibleToolbarSeparatorIndex(index: number): number {
    for (let previousIndex = index - 1; previousIndex >= 0; previousIndex -= 1) {
      const item = options.toolbarItems[previousIndex]
      if (item?.type === 'separator' && shouldShowToolbarItem(item, previousIndex)) {
        return previousIndex
      }
    }
    return -1
  }

  function isVisibleToolbarControlIndex(index: number): boolean {
    if (toolbarOverflowCount.value > 0 && index === 工具栏公式索引) {
      return true
    }

    const item = options.toolbarItems[index]
    return Boolean(
      item
      && item.type !== 'separator'
      && item.type !== 'spacer'
      && shouldShowToolbarItem(item, index),
    )
  }

  function 初始化工具栏折叠监听() {
    if (typeof ResizeObserver === 'undefined') {
      return
    }

    工具栏尺寸观察器?.disconnect()
    工具栏尺寸观察器 = new ResizeObserver(() => 调度工具栏折叠更新())

    const toolbarElement = options.getToolbarElement()
    if (toolbarElement) {
      工具栏尺寸观察器.observe(toolbarElement)
    }

    const rootElement = options.getRootElement()
    if (rootElement) {
      工具栏尺寸观察器.observe(rootElement)
    }
  }

  function 清理工具栏折叠监听() {
    if (工具栏折叠更新帧) {
      cancelAnimationFrame(工具栏折叠更新帧)
      工具栏折叠更新帧 = 0
    }
    工具栏尺寸观察器?.disconnect()
    工具栏尺寸观察器 = null
  }

  function 调度工具栏折叠更新() {
    if (typeof window === 'undefined') {
      return
    }

    if (工具栏折叠更新帧) {
      cancelAnimationFrame(工具栏折叠更新帧)
    }

    工具栏折叠更新帧 = window.requestAnimationFrame(() => {
      工具栏折叠更新帧 = 0
      更新工具栏折叠状态()
    })
  }

  function 更新工具栏折叠状态() {
    更新工具栏宽度缓存()
    const nextOverflowCount = 计算工具栏折叠数量()
    if (nextOverflowCount === toolbarOverflowCount.value) {
      return
    }

    toolbarOverflowCount.value = nextOverflowCount
    void nextTick(() => {
      更新工具栏宽度缓存()
      调度工具栏折叠更新()
    })
  }

  function 更新工具栏宽度缓存() {
    const toolbarElement = options.getToolbarElement()
    if (!toolbarElement) {
      return
    }

    const nextWidthMap = { ...toolbarItemWidthMap.value }
    toolbarElement.querySelectorAll<HTMLElement>('[data-toolbar-index]').forEach((element) => {
      if (element.offsetParent === null) {
        return
      }

      const index = Number(element.dataset.toolbarIndex)
      if (!Number.isInteger(index)) {
        return
      }

      const width = 测量工具栏元素宽度(element)
      if (width > 0) {
        nextWidthMap[index] = width
      }
    })

    const moreElement = toolbarElement.querySelector<HTMLElement>('[data-toolbar-more]')
    if (moreElement && moreElement.offsetParent !== null) {
      const width = 测量工具栏元素宽度(moreElement)
      if (width > 0) {
        toolbarMoreWidth.value = width
      }
    }

    toolbarItemWidthMap.value = nextWidthMap
  }

  function 计算工具栏折叠数量(): number {
    const toolbarElement = options.getToolbarElement()
    if (!toolbarElement) {
      return 0
    }

    const availableWidth = toolbarElement.clientWidth
    if (availableWidth <= 0) {
      return 0
    }

    const widthMap = toolbarItemWidthMap.value
    const itemGap = 获取工具栏项目间距(toolbarElement)
    const maxOverflowCount = 工具栏折叠候选索引.value.length

    for (let overflowCount = 0; overflowCount <= maxOverflowCount; overflowCount += 1) {
      const nextWidth = 计算工具栏显示宽度(overflowCount, widthMap, itemGap)
      if (nextWidth <= availableWidth) {
        return overflowCount
      }
    }

    return maxOverflowCount
  }

  function 计算工具栏显示宽度(
    overflowCount: number,
    widthMap: Record<number, number>,
    itemGap: number,
  ): number {
    const overflowIndexes = new Set(工具栏折叠候选索引.value.slice(0, overflowCount))
    const visibleIndexes = options.toolbarItems.reduce<number[]>((indexes, item, index) => {
      if (item.hidden?.() || overflowIndexes.has(index)) {
        return indexes
      }

      if (item.type === 'separator' && !shouldShowEstimatedToolbarSeparator(index, overflowIndexes, overflowCount > 0)) {
        return indexes
      }

      indexes.push(index)
      return indexes
    }, [])
    const visibleItemsWidth = visibleIndexes.reduce(
      (sum, index) => sum + 获取工具栏项目宽度(options.toolbarItems[index], index, widthMap),
      0,
    )
    const moreWidth = overflowCount > 0 ? toolbarMoreWidth.value : 0
    const visibleItemCount = visibleIndexes.length + (overflowCount > 0 ? 1 : 0)
    const visibleGapWidth = Math.max(visibleItemCount - 1, 0) * itemGap

    return visibleItemsWidth + moreWidth + visibleGapWidth
  }

  function shouldShowEstimatedToolbarSeparator(
    index: number,
    overflowIndexes: Set<number>,
    hasMoreButton: boolean,
  ): boolean {
    if (!hasEstimatedVisibleToolbarControlBefore(index, overflowIndexes, hasMoreButton)) {
      return false
    }

    if (!hasEstimatedVisibleToolbarControlAfter(index, overflowIndexes, hasMoreButton)) {
      return false
    }

    const previousSeparatorIndex = findPreviousEstimatedVisibleToolbarSeparatorIndex(index, overflowIndexes, hasMoreButton)
    return previousSeparatorIndex < 0
      || hasEstimatedVisibleToolbarControlBetween(previousSeparatorIndex, index, overflowIndexes, hasMoreButton)
  }

  function hasEstimatedVisibleToolbarControlBefore(
    index: number,
    overflowIndexes: Set<number>,
    hasMoreButton: boolean,
  ): boolean {
    return hasEstimatedVisibleToolbarControlBetween(-1, index, overflowIndexes, hasMoreButton)
  }

  function hasEstimatedVisibleToolbarControlAfter(
    index: number,
    overflowIndexes: Set<number>,
    hasMoreButton: boolean,
  ): boolean {
    return hasEstimatedVisibleToolbarControlBetween(index, options.toolbarItems.length, overflowIndexes, hasMoreButton)
  }

  function hasEstimatedVisibleToolbarControlBetween(
    startIndex: number,
    endIndex: number,
    overflowIndexes: Set<number>,
    hasMoreButton: boolean,
  ): boolean {
    for (let index = startIndex + 1; index < endIndex; index += 1) {
      if (isEstimatedVisibleToolbarControlIndex(index, overflowIndexes, hasMoreButton)) {
        return true
      }
    }
    return false
  }

  function findPreviousEstimatedVisibleToolbarSeparatorIndex(
    index: number,
    overflowIndexes: Set<number>,
    hasMoreButton: boolean,
  ): number {
    for (let previousIndex = index - 1; previousIndex >= 0; previousIndex -= 1) {
      const item = options.toolbarItems[previousIndex]
      if (
        item?.type === 'separator'
        && !item.hidden?.()
        && !overflowIndexes.has(previousIndex)
        && shouldShowEstimatedToolbarSeparator(previousIndex, overflowIndexes, hasMoreButton)
      ) {
        return previousIndex
      }
    }
    return -1
  }

  function isEstimatedVisibleToolbarControlIndex(
    index: number,
    overflowIndexes: Set<number>,
    hasMoreButton: boolean,
  ): boolean {
    if (hasMoreButton && index === 工具栏公式索引) {
      return true
    }

    const item = options.toolbarItems[index]
    return Boolean(
      item
      && item.type !== 'separator'
      && item.type !== 'spacer'
      && !item.hidden?.()
      && !overflowIndexes.has(index),
    )
  }

  function 获取工具栏项目宽度(item: ToolbarItem | undefined, index: number, widthMap: Record<number, number>): number {
    if (!item) {
      return 0
    }

    if (item.type === 'spacer') {
      return 12
    }

    return widthMap[index] ?? 获取工具栏项目默认宽度(item)
  }

  function 获取工具栏项目默认宽度(item: ToolbarItem): number {
    if (item.type === 'separator') {
      return 13
    }

    return 28
  }

  function 获取工具栏项目间距(element: HTMLElement): number {
    const style = window.getComputedStyle(element)
    const columnGap = Number.parseFloat(style.columnGap)
    if (Number.isFinite(columnGap)) {
      return columnGap
    }

    const gap = Number.parseFloat(style.gap)
    return Number.isFinite(gap) ? gap : 0
  }

  function 测量工具栏元素宽度(element: HTMLElement): number {
    const style = window.getComputedStyle(element)
    const marginLeft = Number.parseFloat(style.marginLeft) || 0
    const marginRight = Number.parseFloat(style.marginRight) || 0
    return element.getBoundingClientRect().width + marginLeft + marginRight
  }

  return {
    toolbarOverflowCount,
    工具栏更多键,
    工具栏公式索引,
    工具栏折叠候选索引,
    溢出工具栏索引集合,
    shouldShowToolbarItem,
    shouldShowToolbarSeparator,
    初始化工具栏折叠监听,
    清理工具栏折叠监听,
    调度工具栏折叠更新,
  }
}
