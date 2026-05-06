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

export function useDropdownPanels(
  panels: DropdownPanelItem[],
  options: UseDropdownPanelsOptions = {},
) {
  const gap = options.gap ?? DEFAULT_GAP
  const panelOffset = options.panelOffset ?? DEFAULT_PANEL_OFFSET
  const listenScroll = options.listenScroll ?? false

  function adjustPanelPosition(wrapperEl?: HTMLElement) {
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

  function adjustOpenPanels() {
    for (const panel of panels) {
      if (panel.isOpen.value) {
        adjustPanelPosition(panel.wrapperRef.value)
      }
    }
  }

  function closePanels(event?: MouseEvent) {
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
      adjustPanelPosition(panel.wrapperRef.value)
    })
  }

  onMounted(() => {
    document.addEventListener('click', closePanels)
    window.addEventListener('resize', adjustOpenPanels)
    if (listenScroll) {
      window.addEventListener('scroll', adjustOpenPanels, { passive: true })
    }
  })

  onBeforeUnmount(() => {
    document.removeEventListener('click', closePanels)
    window.removeEventListener('resize', adjustOpenPanels)
    if (listenScroll) {
      window.removeEventListener('scroll', adjustOpenPanels)
    }
  })

  return {
    adjustOpenPanels,
    adjustPanelPosition,
    closePanels,
  }
}
