import type { FireworkOptions } from 'mouse-firework/dist/types'
import { onMounted, onUnmounted, ref, watch } from 'vue'
import { getThemeClickEffectColors, useThemeStore } from '../../shared/stores/theme'

let cleanupFn: (() => void) | null = null
let fireworkModule: { default: (options: FireworkOptions) => () => void } | null = null

export function useClickEffect() {
  const theme = useThemeStore()
  const isMobile = ref(false)

  function checkMobile() {
    isMobile.value = window.matchMedia('(max-width: 768px)').matches
  }

  async function initFirework() {
    if (!theme.clickEffectEnabled || isMobile.value) {
      destroyFirework()
      return
    }

    if (!fireworkModule) {
      fireworkModule = await import('mouse-firework')
    }

    destroyFirework()

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

  function destroyFirework() {
    if (cleanupFn) {
      cleanupFn()
      cleanupFn = null
    }
  }

  onMounted(() => {
    checkMobile()
    window.addEventListener('resize', checkMobile)
    void initFirework()
  })

  onUnmounted(() => {
    window.removeEventListener('resize', checkMobile)
    destroyFirework()
  })

  watch(() => theme.clickEffectEnabled, () => {
    void initFirework()
  })

  watch(isMobile, () => {
    void initFirework()
  })

  watch([() => theme.hue, () => theme.isDark], () => {
    void initFirework()
  })
}
