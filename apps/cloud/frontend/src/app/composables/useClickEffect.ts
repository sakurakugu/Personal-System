import type { FireworkOptions } from 'mouse-firework/dist/types'
import { onMounted, onUnmounted, ref, watch } from 'vue'
import { getThemeClickEffectColors, useThemeStore } from '../../shared/stores/theme'

let cleanupFn: (() => void) | null = null
let fireworkModule: { default: (options: FireworkOptions) => () => void } | null = null

export function useClickEffect() {
  const theme = useThemeStore()
  const isMobile = ref(false)

  function 检查移动端() {
    isMobile.value = window.matchMedia('(max-width: 768px)').matches
  }

  async function 初始化烟花() {
    if (!theme.clickEffectEnabled || isMobile.value) {
      销毁烟花()
      return
    }

    if (!fireworkModule) {
      fireworkModule = await import('mouse-firework')
    }

    销毁烟花()

    const options: FireworkOptions = {
      excludeElements: ['a', 'button', 'input', 'textarea', 'select', 'label', 'svg', 'img', 'video'],
      particles: [
        {
          shape: 'circle',
          move: ['emit'],
          easing: 'easeOutExpo',
          colors: getThemeClickEffectColors(theme.hue, theme.isDark),
          number: 20,
          duration: [1200, 1800],
          shapeOptions: {
            radius: [16, 32],
            alpha: [0.3, 0.5],
          },
        },
      ],
    }

    cleanupFn = fireworkModule.default(options)
  }

  function 销毁烟花() {
    if (cleanupFn) {
      cleanupFn()
      cleanupFn = null
    }
  }

  onMounted(() => {
    检查移动端()
    window.addEventListener('resize', 检查移动端)
    void 初始化烟花()
  })

  onUnmounted(() => {
    window.removeEventListener('resize', 检查移动端)
    销毁烟花()
  })

  watch(() => theme.clickEffectEnabled, () => {
    void 初始化烟花()
  })

  watch(isMobile, () => {
    void 初始化烟花()
  })

  watch([() => theme.hue, () => theme.isDark], () => {
    void 初始化烟花()
  })
}
