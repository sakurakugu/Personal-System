<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Icon } from '@iconify/vue'

const route = useRoute()
const router = useRouter()

const showBackToTop = ref(false)

const isHome = () => route.path === '/blog' || route.path === '/'

function handleScroll() {
  const scrollTop = window.pageYOffset || document.documentElement.scrollTop
  showBackToTop.value = scrollTop > 200
}

function backToTop() {
  window.scroll({ top: 0, behavior: 'smooth' })
}

function backToHome() {
  router.push('/blog')
}

let scrollHandler: () => void

onMounted(() => {
  scrollHandler = handleScroll
  window.addEventListener('scroll', scrollHandler, { passive: true })
  handleScroll()
})

onUnmounted(() => {
  window.removeEventListener('scroll', scrollHandler)
})
</script>

<template>
  <div class="floating-controls">
    <button
      v-if="!isHome()"
      class="floating-btn"
      aria-label="回到首页"
      @click="backToHome"
    >
      <Icon icon="material-symbols:home-outline-rounded" />
    </button>
    <button
      v-show="showBackToTop"
      class="floating-btn"
      aria-label="回到顶部"
      @click="backToTop"
    >
      <Icon icon="material-symbols:keyboard-arrow-up-rounded" />
    </button>
  </div>
</template>

<style scoped>
.floating-controls {
  position: fixed;
  right: 1rem;
  bottom: calc(4rem + var(--app-safe-area-bottom, 0px));
  z-index: 1200;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  align-items: flex-end;
  pointer-events: none;
}

.floating-btn {
  width: 3rem;
  height: 3rem;
  border-radius: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  color: var(--el-color-primary);
  background: var(--bg-card);
  border: 1px solid rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(12px);
  cursor: pointer;
  pointer-events: auto;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.floating-btn:hover {
  background: var(--bg-hover);
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.12);
}

.floating-btn:active {
  transform: scale(0.9);
}

.dark .floating-btn {
  background: oklch(0.22 0.015 var(--hue));
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: var(--el-color-primary-light-3);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.dark .floating-btn:hover {
  background: oklch(0.28 0.02 var(--hue));
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.4);
}

@media (max-width: 768px) {
  .floating-controls {
    right: 0.75rem;
    bottom: calc(3.5rem + var(--app-safe-area-bottom, 0px));
  }

  .floating-btn {
    width: 2.75rem;
    height: 2.75rem;
    font-size: 1.375rem;
    border-radius: 0.875rem;
  }
}

@media (max-width: 480px) {
  .floating-controls {
    right: 0.5rem;
    bottom: calc(3rem + var(--app-safe-area-bottom, 0px));
  }

  .floating-btn {
    width: 2.5rem;
    height: 2.5rem;
    font-size: 1.25rem;
    border-radius: 0.75rem;
  }
}
</style>
