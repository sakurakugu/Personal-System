import { nextTick, onBeforeUnmount, onMounted, watch } from 'vue'
import type { Ref } from 'vue'

type DropdownPanelItem = {
  isOpen: Ref<boolean>
  wrapperRef: Ref<HTMLElement | undefined>
}

type UseDropdownPanelsOptions = {
  gap?: number
  panelOffset?: number
  listenScroll?: boolean
}

const DEFAULT_GAP = 8
const DEFAULT_PANEL_OFFSET = 20

export function 使用下拉面板(
  panels: DropdownPanelItem[],
  options: UseDropdownPanelsOptions = {},
) {
  const gap = options.gap ?? DEFAULT_GAP
  const panelOffset = options.panelOffset ?? DEFAULT_PANEL_OFFSET
  const listenScroll = options.listenScroll ?? false

  function 调整面板位置(wrapperEl?: HTMLElement) {
    if (!wrapperEl) {
      return
    }
    const panel = wrapperEl.querySelector('.custom-dropdown-panel') as HTMLElement | null
    if (!panel) {
      return
    }

    const wrapperRect = wrapperEl.getBoundingClientRect()
    const panelRect = panel.getBoundingClientRect()
    const viewportWidth = window.innerWidth
    const viewportHeight = window.innerHeight

    let desiredLeft = wrapperRect.left + wrapperRect.width / 2 - panelRect.width / 2
    if (desiredLeft < gap) {
      desiredLeft = gap
    }
    if (desiredLeft + panelRect.width > viewportWidth - gap) {
      desiredLeft = viewportWidth - gap - panelRect.width
    }

    const relativeLeft = desiredLeft - wrapperRect.left
    const availableHeight = Math.max(0, viewportHeight - wrapperRect.bottom - panelOffset - gap)

    wrapperEl.style.setProperty('--panel-left', `${relativeLeft}px`)
    wrapperEl.style.setProperty('--panel-transform', 'none')
    wrapperEl.style.setProperty('--panel-max-height', `${availableHeight}px`)
    wrapperEl.style.setProperty('--panel-bridge-width', `${panelRect.width}px`)
  }

  function 调整打开的面板() {
    for (const panel of panels) {
      if (panel.isOpen.value) {
        调整面板位置(panel.wrapperRef.value)
      }
    }
  }

  function 关闭面板(event?: MouseEvent) {
    if (!event) {
      for (const panel of panels) {
        panel.isOpen.value = false
      }
      return
    }

    const path = event.composedPath ? event.composedPath() : []
    for (const panel of panels) {
      const wrapperEl = panel.wrapperRef.value
      if (wrapperEl && path.includes(wrapperEl)) {
        continue
      }
      panel.isOpen.value = false
    }
  }

  for (const panel of panels) {
    watch(panel.isOpen, async (value) => {
      if (!value) {
        return
      }
      await nextTick()
      调整面板位置(panel.wrapperRef.value)
    })
  }

  onMounted(() => {
    document.addEventListener('click', 关闭面板)
    window.addEventListener('resize', 调整打开的面板)
    if (listenScroll) {
      window.addEventListener('scroll', 调整打开的面板, { passive: true })
    }
  })

  onBeforeUnmount(() => {
    document.removeEventListener('click', 关闭面板)
    window.removeEventListener('resize', 调整打开的面板)
    if (listenScroll) {
      window.removeEventListener('scroll', 调整打开的面板)
    }
  })

  return {
    调整打开的面板,
    调整面板位置,
    关闭面板,
  }
}
