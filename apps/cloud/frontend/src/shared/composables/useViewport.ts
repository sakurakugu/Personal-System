import { computed } from 'vue'
import { useWindowSize } from '@vueuse/core'

const 移动端视口断点 = 768

export function 使用视口() {
  const { width, height } = useWindowSize()

  const isMobileViewport = computed(() => width.value <= 移动端视口断点)
  const isDesktopViewport = computed(() => width.value > 移动端视口断点)

  return {
    width,
    height,
    isMobileViewport,
    isDesktopViewport,
  }
}
