import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

function 读取根节点色相(): number {
  if (typeof window === 'undefined') {
    return 0
  }

  const hueValue = window.getComputedStyle(document.documentElement).getPropertyValue('--hue').trim()
  const parsedHue = Number(hueValue)
  return Number.isFinite(parsedHue) ? parsedHue : 0
}

function 读取深色模式状态(): boolean {
  if (typeof document === 'undefined') {
    return false
  }

  return document.documentElement.classList.contains('dark')
}

export function 使用文章主题状态() {
  const isDark = ref(读取深色模式状态())
  const hue = ref(读取根节点色相())
  let observer: MutationObserver | null = null

  function 同步主题状态() {
    isDark.value = 读取深色模式状态()
    hue.value = 读取根节点色相()
  }

  onMounted(() => {
    同步主题状态()

    if (typeof window.MutationObserver === 'undefined') {
      return
    }

    observer = new window.MutationObserver(() => {
      同步主题状态()
    })
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['class', 'style'],
    })
  })

  onBeforeUnmount(() => {
    observer?.disconnect()
    observer = null
  })

  return {
    isDark: computed(() => isDark.value),
    hue: computed(() => hue.value),
  }
}
