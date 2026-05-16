import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

const 移动端视口断点 = 768

export function 使用视口() {
  const width = ref(typeof window === 'undefined' ? 0 : window.innerWidth)
  const height = ref(typeof window === 'undefined' ? 0 : window.innerHeight)

  function 同步窗口尺寸() {
    width.value = window.innerWidth
    height.value = window.innerHeight
  }

  onMounted(() => {
    同步窗口尺寸()
    window.addEventListener('resize', 同步窗口尺寸)
  })

  onBeforeUnmount(() => {
    window.removeEventListener('resize', 同步窗口尺寸)
  })

  const isMobileViewport = computed(() => width.value <= 移动端视口断点)
  const isDesktopViewport = computed(() => width.value > 移动端视口断点)

  return {
    width,
    height,
    isMobileViewport,
    isDesktopViewport,
  }
}
