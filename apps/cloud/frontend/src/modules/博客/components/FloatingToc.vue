<script setup lang="ts">
/* global HTMLElement, IntersectionObserver, MouseEvent, Node */
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { Icon } from '@iconify/vue'

const props = defineProps<{
  toc: Array<{ id: string; text: string; level: number }>
}>()

const showPanel = ref(false)
const tocContentRef = ref<HTMLElement | null>(null)
const tocScrollRef = ref<HTMLElement | null>(null)
const indicatorRef = ref<HTMLElement | null>(null)
const activeIds = ref<Set<string>>(new Set())
const observer = ref<IntersectionObserver | null>(null)
const scrollTimeout = ref<number | null>(null)

const minLevel = computed(() => {
  if (!props.toc.length) return 2
  return Math.min(...props.toc.map((t) => t.level))
})

function levelDepth(level: number) {
  return level === minLevel.value ? 0 : 1
}

function badgeFor(item: { level: number }, h2Index: number) {
  const depth = levelDepth(item.level)
  if (depth === 0) {
    return { type: 'index', text: String(h2Index) } as const
  }
  return { type: 'dot', small: true } as const
}

const tocWithBadge = computed(() => {
  let h2Count = 1
  return props.toc.map((item) => {
    const badge = badgeFor(item, h2Count)
    if (levelDepth(item.level) === 0) {
      h2Count++
    }
    return { ...item, badge }
  })
})

function togglePanel() {
  showPanel.value = !showPanel.value
}

function closePanel() {
  showPanel.value = false
}

function getHeadingElements(): HTMLElement[] {
  const list: HTMLElement[] = []
  for (const item of props.toc) {
    const el = document.getElementById(item.id)
    if (el) list.push(el)
  }
  return list
}

function updateActiveIndicator() {
  const indicator = indicatorRef.value
  const container = tocContentRef.value
  if (!indicator || !container) return

  const activeItems = Array.from(
    container.querySelectorAll('.toc-item.visible')
  ) as HTMLElement[]

  if (activeItems.length === 0) {
    indicator.style.opacity = '0'
    return
  }

  const contentRect = container.getBoundingClientRect()
  const first = activeItems[0]
  const last = activeItems[activeItems.length - 1]
  const top = first.getBoundingClientRect().top - contentRect.top
  const height = last.getBoundingClientRect().bottom - first.getBoundingClientRect().top

  indicator.style.top = `${top}px`
  indicator.style.height = `${height}px`
  indicator.style.opacity = '1'

  scrollToActiveItem(first)
}

function scrollToActiveItem(activeItem: HTMLElement) {
  const container = tocScrollRef.value
  if (!container) return

  if (scrollTimeout.value) {
    window.clearTimeout(scrollTimeout.value)
  }
  scrollTimeout.value = window.setTimeout(() => {
    const containerRect = container.getBoundingClientRect()
    const itemRect = activeItem.getBoundingClientRect()
    const isVisible = itemRect.top >= containerRect.top && itemRect.bottom <= containerRect.bottom
    if (!isVisible) {
      const offsetTop = activeItem.offsetTop
      const targetScroll = offsetTop - container.clientHeight / 2 + activeItem.clientHeight / 2
      container.scrollTo({ top: targetScroll, behavior: 'smooth' })
    }
  }, 100)
}

function updateActiveState() {
  const headings = getHeadingElements()
  const visible: string[] = []

  for (const h of headings) {
    const rect = h.getBoundingClientRect()
    if (rect.top < window.innerHeight && rect.bottom > 0) {
      visible.push(h.id)
    }
  }

  if (visible.length === 0 && headings.length > 0) {
    let closest: string | null = null
    let minDistance = Number.POSITIVE_INFINITY
    for (const h of headings) {
      const rect = h.getBoundingClientRect()
      const distance = Math.abs(rect.top)
      if (distance < minDistance) {
        minDistance = distance
        closest = h.id
      }
    }
    if (closest) visible.push(closest)
  }

  activeIds.value = new Set(visible)
  nextTick(updateActiveIndicator)
}

function setupObserver() {
  if (observer.value) {
    observer.value.disconnect()
  }
  const headings = getHeadingElements()
  if (!headings.length) return

  observer.value = new IntersectionObserver(() => {
    updateActiveState()
  }, {
    rootMargin: '0px 0px 0px 0px',
    threshold: 0,
  })

  headings.forEach((h) => observer.value?.observe(h))
}

function handleClick(id: string, event: MouseEvent) {
  event.preventDefault()
  const el = document.getElementById(id)
  if (el) {
    const top = el.getBoundingClientRect().top + window.pageYOffset - 80
    window.scrollTo({ top, behavior: 'smooth' })
  }
  closePanel()
}

function init() {
  nextTick(() => {
    setupObserver()
    updateActiveState()
  })
}

function cleanup() {
  if (observer.value) {
    observer.value.disconnect()
    observer.value = null
  }
  if (scrollTimeout.value) {
    window.clearTimeout(scrollTimeout.value)
    scrollTimeout.value = null
  }
}

watch(() => props.toc, () => {
  cleanup()
  activeIds.value = new Set()
  init()
}, { immediate: true })

onMounted(init)
onBeforeUnmount(cleanup)

function handleClickOutside(event: MouseEvent) {
  const wrapper = document.querySelector('.floating-toc')
  if (wrapper && !wrapper.contains(event.target as Node)) {
    closePanel()
  }
}

watch(showPanel, (show) => {
  if (show) {
    document.addEventListener('click', handleClickOutside)
    nextTick(() => {
      updateActiveState()
      const firstActive = tocContentRef.value?.querySelector('.toc-item.visible') as HTMLElement | null
      if (firstActive) scrollToActiveItem(firstActive)
    })
  } else {
    document.removeEventListener('click', handleClickOutside)
  }
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<template>
  <div v-if="toc.length" class="floating-toc">
    <button
      class="floating-btn toc-trigger"
      aria-label="文章目录"
      @click.stop="togglePanel"
    >
      <Icon icon="material-symbols:format-list-bulleted" />
    </button>

    <Transition name="toc-panel">
      <div v-show="showPanel" class="floating-toc-panel">
        <div class="panel-header">
          <h3 class="panel-title">文章目录</h3>
        </div>
        <div ref="tocScrollRef" class="toc-scroll-container">
          <div ref="tocContentRef" class="toc-content">
            <a
              v-for="item in tocWithBadge"
              :key="item.id"
              :href="`#${item.id}`"
              class="toc-item"
              :class="{
                [`toc-level-${levelDepth(item.level)}`]: true,
                visible: activeIds.has(item.id),
              }"
              @click="handleClick(item.id, $event)"
            >
              <div
                class="toc-badge"
                :class="{ 'toc-badge-index': item.badge.type === 'index' }"
              >
                <span v-if="item.badge.type === 'index'">{{ item.badge.text }}</span>
                <span v-else class="toc-badge-dot" :class="{ 'toc-badge-dot-sm': item.badge.small }" />
              </div>
              <div
                class="toc-label"
                :class="{
                  'toc-label-primary': levelDepth(item.level) === 0,
                  'toc-label-secondary': levelDepth(item.level) !== 0,
                }"
                :title="item.text"
              >
                {{ item.text }}
              </div>
            </a>
            <div ref="indicatorRef" class="toc-active-indicator" />
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.floating-toc {
  position: fixed;
  right: 1rem;
  bottom: 7.5rem;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.5rem;
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

.floating-toc-panel {
  position: absolute;
  bottom: calc(100% + 0.5rem);
  right: 0;
  width: 20rem;
  max-height: 24rem;
  display: flex;
  flex-direction: column;
  background: var(--card-bg-transparent);
  border: 1px solid rgba(255, 255, 255, 0.45);
  border-radius: 1rem;
  backdrop-filter: blur(18px);
  box-shadow: 0 10px 30px rgba(148, 163, 184, 0.14);
  pointer-events: auto;
  overflow: hidden;
  transform-origin: bottom right;
}

.dark .floating-toc-panel {
  border-color: rgba(148, 163, 184, 0.16);
  box-shadow: 0 12px 28px rgba(2, 6, 23, 0.28);
}

.toc-panel-enter-active,
.toc-panel-leave-active {
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.toc-panel-enter-from,
.toc-panel-leave-to {
  opacity: 0;
  transform: scale(0.9) translateY(10px);
}

.panel-header {
  display: flex;
  align-items: center;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  flex-shrink: 0;
}

.dark .panel-header {
  border-bottom-color: rgba(255, 255, 255, 0.08);
}

.panel-title {
  position: relative;
  font-size: 1rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 0 12px;
}

.panel-title::before {
  content: '';
  position: absolute;
  left: -12px;
  top: 50%;
  transform: translateY(-50%);
  width: 4px;
  height: 16px;
  border-radius: 2px;
  background: var(--el-color-primary);
}

.toc-scroll-container {
  overflow-y: auto;
  overflow-x: hidden;
  -webkit-overflow-scrolling: touch;
  scroll-behavior: smooth;
  padding: 0.5rem 1rem 1rem;
  max-height: calc(24rem - 3.5rem);
}

.toc-content {
  display: flex;
  flex-direction: column;
  gap: 0.28rem;
  position: relative;
  overflow: visible;
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  align-items: stretch;
}

.toc-item {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  text-decoration: none;
  color: inherit;
  border-radius: 0.875rem;
  transition:
    background-color 0.14s ease,
    transform 0.14s ease,
    color 0.14s ease;
  width: 100%;
  min-width: 0;
  flex-shrink: 0;
  max-width: 100%;
  overflow: hidden;
  box-sizing: border-box;
  position: relative;
  padding: 0.48rem 0.62rem;
  min-height: 2.2rem;
}

.toc-item:hover {
  background: rgba(0, 0, 0, 0.04);
  transform: translateX(1px);
}

.toc-item:active {
  background: rgba(0, 0, 0, 0.06);
}

.dark .toc-item:hover {
  background: rgba(255, 255, 255, 0.06);
}

.dark .toc-item:active {
  background: rgba(255, 255, 255, 0.08);
}

.toc-item.toc-level-0 {
  padding-left: 1.08rem;
}

.toc-item.toc-level-1 {
  padding-left: 1.62rem;
}

.toc-label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
  flex: 1;
  max-width: calc(100% - 2.4rem);
  box-sizing: border-box;
  font-size: 0.86rem;
  line-height: 1.3;
  letter-spacing: 0.01em;
}

.toc-label-primary {
  color: var(--text-secondary);
}

.toc-label-secondary {
  color: var(--text-tertiary);
}

.toc-badge {
  display: grid;
  place-items: center;
  flex-shrink: 0;
  width: 1.35rem;
  height: 1.35rem;
  border-radius: 0.5rem;
  font-size: 0.68rem;
  font-weight: 700;
  line-height: 1;
}

.toc-badge-index {
  background: var(--bg-hover);
  color: var(--el-color-primary);
}

.toc-badge-dot {
  width: 0.48rem;
  height: 0.48rem;
  border-radius: 999px;
  background: var(--border-color);
}

.toc-badge-dot-sm {
  width: 0.34rem;
  height: 0.34rem;
}

.toc-item.visible .toc-label {
  color: var(--el-color-primary);
  opacity: 1;
}

.toc-item.visible .toc-badge-dot,
.toc-item.visible .toc-badge-dot-sm {
  background: var(--el-color-primary);
}

.toc-active-indicator {
  position: absolute;
  left: 0;
  right: 0;
  background: rgba(0, 0, 0, 0.04);
  border-radius: 0.875rem;
  transition: top 0.18s ease, height 0.18s ease, opacity 0.14s ease;
  box-shadow: 0 6px 18px -14px rgba(0, 0, 0, 0.12);
  z-index: -1;
}

.dark .toc-active-indicator {
  background: rgba(255, 255, 255, 0.06);
  box-shadow: 0 6px 18px -14px rgba(0, 0, 0, 0.3);
}

/* 桌面端右侧栏可见时隐藏浮动目录 */
@media (min-width: 1280px) {
  .floating-toc {
    display: none;
  }
}

@media (max-width: 768px) {
  .floating-toc {
    right: 0.75rem;
    bottom: 7rem;
  }

  .floating-btn {
    width: 2.75rem;
    height: 2.75rem;
    font-size: 1.375rem;
    border-radius: 0.875rem;
  }

  .floating-toc-panel {
    width: calc(100vw - 2rem);
    max-width: 20rem;
    max-height: 20rem;
  }

  .toc-scroll-container {
    max-height: calc(20rem - 3.5rem);
  }
}

@media (max-width: 480px) {
  .floating-toc {
    right: 0.5rem;
    bottom: 6.5rem;
  }

  .floating-btn {
    width: 2.5rem;
    height: 2.5rem;
    font-size: 1.25rem;
    border-radius: 0.75rem;
  }

  .toc-item {
    padding: 0.44rem 0.58rem;
    border-radius: 0.78rem;
  }

  .toc-item.toc-level-0 {
    padding-left: 0.94rem;
  }

  .toc-item.toc-level-1 {
    padding-left: 1.34rem;
  }
}
</style>
