import { computed } from 'vue'
import { useWindowSize } from '@vueuse/core'
import { MOBILE_VIEWPORT_BREAKPOINT } from '../constants/breakpoints'

export function useViewport() {
  const { width, height } = useWindowSize()

  const isMobileViewport = computed(() => width.value <= MOBILE_VIEWPORT_BREAKPOINT)
  const isDesktopViewport = computed(() => width.value > MOBILE_VIEWPORT_BREAKPOINT)

  return {
    width,
    height,
    isMobileViewport,
    isDesktopViewport,
  }
}
