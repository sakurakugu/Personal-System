<script setup lang="ts">
/* global HTMLElement, MouseEvent, Node */
import { Icon } from '@iconify/vue'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps<{
  isDetailView: boolean
  toc: Array<{ id: string; text: string; level: number }>
}>()

const router = useRouter()
const showBackToTop = ref(false)
const showTocPanel = ref(false)
const scrollContainer = ref<HTMLElement | globalThis.Window | null>(null)
const tocContentRef = ref<HTMLElement | null>(null)
const tocScrollRef = ref<HTMLElement | null>(null)
const indicatorRef = ref<HTMLElement | null>(null)
const activeIds = ref<Set<string>>(new Set())
const tocScrollTimeout = ref<number | null>(null)

const hasToc = computed(() => props.toc.length > 0)
const minLevel = computed(() => {
  if (!props.toc.length) return 2
  return Math.min(...props.toc.map((item) => item.level))
})

function 目录层级深度(level: number) {
  return Math.min(Math.max(level - minLevel.value, 0), 2)
}

function 获取目录标记(item: { level: number }, index: number) {
  if (目录层级深度(item.level) === 0) {
    return { type: 'index', text: String(index) } as const
  }
  return { type: 'dot' } as const
}

const 带标记目录 = computed(() => {
  let 一级序号 = 1
  return props.toc.map((item) => {
    const 标记 = 获取目录标记(item, 一级序号)
    if (目录层级深度(item.level) === 0) {
      一级序号 += 1
    }
    return { ...item, badge: 标记 }
  })
})

function 获取滚动容器() {
  return document.querySelector<HTMLElement>('.shell-main') ?? window
}

function 是元素滚动容器(target: HTMLElement | globalThis.Window | null): target is HTMLElement {
  return Boolean(target && target !== window)
}

function 获取滚动位置() {
  const target = scrollContainer.value
  if (是元素滚动容器(target)) {
    return target.scrollTop
  }
  return window.pageYOffset || document.documentElement.scrollTop
}

function 处理滚动() {
  showBackToTop.value = 获取滚动位置() > 160
  更新当前目录状态()
}

function 滚动到顶部() {
  const target = scrollContainer.value
  if (是元素滚动容器(target)) {
    target.scrollTo({ top: 0, behavior: 'smooth' })
    return
  }
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function 回到主页() {
  showTocPanel.value = false
  void router.push('/blog')
}

function 切换目录() {
  showTocPanel.value = !showTocPanel.value
}

function 关闭目录() {
  showTocPanel.value = false
}

function 获取标题元素列表(): HTMLElement[] {
  const list: HTMLElement[] = []
  for (const item of props.toc) {
    const element = document.getElementById(item.id)
    if (element) {
      list.push(element)
    }
  }
  return list
}

function 获取可视区域() {
  const target = scrollContainer.value
  if (是元素滚动容器(target)) {
    return target.getBoundingClientRect()
  }
  return {
    top: 0,
    bottom: window.innerHeight,
  }
}

function 滚动到活动目录项(activeItem: HTMLElement) {
  const container = tocScrollRef.value
  if (!container) return

  if (tocScrollTimeout.value) {
    window.clearTimeout(tocScrollTimeout.value)
  }

  tocScrollTimeout.value = window.setTimeout(() => {
    const containerRect = container.getBoundingClientRect()
    const itemRect = activeItem.getBoundingClientRect()
    const isVisible = itemRect.top >= containerRect.top && itemRect.bottom <= containerRect.bottom
    if (!isVisible) {
      const targetTop = activeItem.offsetTop - container.clientHeight / 2 + activeItem.clientHeight / 2
      container.scrollTo({ top: targetTop, behavior: 'smooth' })
    }
  }, 100)
}

function 更新活动指示器() {
  const indicator = indicatorRef.value
  const container = tocContentRef.value
  if (!indicator || !container) return

  const activeItems = Array.from(container.querySelectorAll('.toc-panel-item.is-active')) as HTMLElement[]
  if (activeItems.length === 0) {
    indicator.style.opacity = '0'
    return
  }

  const contentRect = container.getBoundingClientRect()
  const first = activeItems[0]
  const last = activeItems[activeItems.length - 1]
  indicator.style.top = `${first.getBoundingClientRect().top - contentRect.top}px`
  indicator.style.height = `${last.getBoundingClientRect().bottom - first.getBoundingClientRect().top}px`
  indicator.style.opacity = '1'

  if (showTocPanel.value) {
    滚动到活动目录项(first)
  }
}

function 更新当前目录状态() {
  const headings = 获取标题元素列表()
  const visible: string[] = []
  const viewport = 获取可视区域()

  for (const heading of headings) {
    const rect = heading.getBoundingClientRect()
    if (rect.top < viewport.bottom && rect.bottom > viewport.top) {
      visible.push(heading.id)
    }
  }

  if (visible.length === 0 && headings.length > 0) {
    let closest: string | null = null
    let minDistance = Number.POSITIVE_INFINITY
    for (const heading of headings) {
      const rect = heading.getBoundingClientRect()
      const distance = Math.abs(rect.top - viewport.top)
      if (distance < minDistance) {
        minDistance = distance
        closest = heading.id
      }
    }
    if (closest) {
      visible.push(closest)
    }
  }

  activeIds.value = new Set(visible)
  void nextTick(更新活动指示器)
}

function 滚动到章节(id: string, event: MouseEvent) {
  event.preventDefault()
  const element = document.getElementById(id)
  const target = scrollContainer.value
  if (!element) return

  if (是元素滚动容器(target)) {
    const containerRect = target.getBoundingClientRect()
    const elementRect = element.getBoundingClientRect()
    const top = target.scrollTop + elementRect.top - containerRect.top - 16
    target.scrollTo({ top, behavior: 'smooth' })
  } else {
    const top = element.getBoundingClientRect().top + window.pageYOffset - 80
    window.scrollTo({ top, behavior: 'smooth' })
  }
  关闭目录()
}

function 处理外部点击(event: MouseEvent) {
  const wrapper = document.querySelector('.phone-floating-controls')
  if (wrapper && !wrapper.contains(event.target as Node)) {
    关闭目录()
  }
}

function 绑定滚动监听() {
  scrollContainer.value = 获取滚动容器()
  scrollContainer.value.addEventListener('scroll', 处理滚动, { passive: true })
  处理滚动()
}

function 解绑滚动监听() {
  scrollContainer.value?.removeEventListener('scroll', 处理滚动)
}

onMounted(() => {
  nextTick(绑定滚动监听)
})

onBeforeUnmount(() => {
  解绑滚动监听()
  document.removeEventListener('click', 处理外部点击)
  if (tocScrollTimeout.value) {
    window.clearTimeout(tocScrollTimeout.value)
    tocScrollTimeout.value = null
  }
})

watch(showTocPanel, (visible) => {
  if (visible) {
    document.addEventListener('click', 处理外部点击)
    void nextTick(更新当前目录状态)
  } else {
    document.removeEventListener('click', 处理外部点击)
  }
})

watch(() => props.isDetailView, () => {
  关闭目录()
  处理滚动()
})

watch(() => props.toc, () => {
  if (!hasToc.value) {
    关闭目录()
  }
  activeIds.value = new Set()
  void nextTick(更新当前目录状态)
})
</script>

<template>
  <div class="phone-floating-controls">
    <Transition name="toc-panel">
      <div v-show="showTocPanel && hasToc" class="phone-floating-toc-panel">
        <div class="toc-panel-header">
          <span>文章目录</span>
        </div>
        <div ref="tocScrollRef" class="toc-panel-list">
          <div ref="tocContentRef" class="toc-panel-content">
            <a
              v-for="item in 带标记目录"
              :key="item.id"
              class="toc-panel-item"
              :class="{
                [`toc-panel-item--level-${目录层级深度(item.level)}`]: true,
                'is-active': activeIds.has(item.id),
              }"
              :href="`#${item.id}`"
              @click="滚动到章节(item.id, $event)"
            >
              <span
                class="toc-panel-badge"
                :class="{ 'toc-panel-badge--index': item.badge.type === 'index' }"
              >
                <span v-if="item.badge.type === 'index'">{{ item.badge.text }}</span>
                <span v-else class="toc-panel-dot" />
              </span>
              <span class="toc-panel-label" :title="item.text">{{ item.text }}</span>
            </a>
            <div ref="indicatorRef" class="toc-panel-active-indicator" />
          </div>
        </div>
      </div>
    </Transition>

    <button
      v-if="isDetailView"
      class="floating-btn"
      type="button"
      aria-label="回到首页"
      @click="回到主页"
    >
      <Icon icon="material-symbols:home-outline-rounded" />
    </button>
    <button
      v-if="isDetailView && hasToc"
      class="floating-btn"
      type="button"
      aria-label="文章目录"
      @click.stop="切换目录"
    >
      <Icon icon="material-symbols:format-list-bulleted" />
    </button>
    <button
      v-show="showBackToTop"
      class="floating-btn"
      type="button"
      aria-label="回到顶部"
      @click="滚动到顶部"
    >
      <Icon icon="material-symbols:keyboard-arrow-up-rounded" />
    </button>
  </div>
</template>

<style scoped>
.phone-floating-controls {
  position: fixed;
  right: 12px;
  bottom: calc(76px + env(safe-area-inset-bottom));
  z-index: 80;
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: flex-end;
  pointer-events: none;
}

.floating-btn {
  width: 44px;
  height: 44px;
  display: grid;
  place-items: center;
  border: 1px solid rgba(255, 255, 255, 0.48);
  border-radius: 14px;
  color: var(--el-color-primary);
  background: var(--card-bg-transparent, var(--bg-card));
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.14);
  backdrop-filter: blur(16px);
  cursor: pointer;
  pointer-events: auto;
}

.floating-btn:active {
  transform: scale(0.94);
}

.floating-btn svg {
  width: 24px;
  height: 24px;
}

.dark .floating-btn {
  border-color: rgba(148, 163, 184, 0.18);
  color: var(--el-color-primary-light-3);
  box-shadow: 0 12px 26px rgba(0, 0, 0, 0.32);
}

.phone-floating-toc-panel {
  width: min(320px, calc(100vw - 24px));
  max-height: min(420px, calc(var(--app-viewport-height) - 180px));
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.48);
  border-radius: 16px;
  background: var(--card-bg-transparent, var(--bg-card));
  box-shadow: 0 16px 36px rgba(15, 23, 42, 0.16);
  backdrop-filter: blur(18px);
  pointer-events: auto;
  transform-origin: bottom right;
}

.dark .phone-floating-toc-panel {
  border-color: rgba(148, 163, 184, 0.18);
  box-shadow: 0 16px 36px rgba(0, 0, 0, 0.34);
}

.toc-panel-header {
  display: flex;
  align-items: center;
  flex: 0 0 auto;
  padding: 12px 16px 10px;
  color: var(--text-primary);
  font-size: 15px;
  font-weight: 700;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.dark .toc-panel-header {
  border-bottom-color: rgba(255, 255, 255, 0.08);
}

.toc-panel-header span {
  position: relative;
  padding-left: 12px;
}

.toc-panel-header span::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 0;
  width: 4px;
  height: 16px;
  border-radius: 999px;
  background: var(--el-color-primary);
  transform: translateY(-50%);
}

.toc-panel-list {
  overflow-y: auto;
  overflow-x: hidden;
  padding: 8px 10px 12px;
  -webkit-overflow-scrolling: touch;
  scroll-behavior: smooth;
}

.toc-panel-content {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.toc-panel-item {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  min-height: 34px;
  padding: 7px 10px;
  overflow: hidden;
  color: var(--text-secondary);
  text-decoration: none;
  border-radius: 10px;
  transition:
    background-color 0.14s ease,
    color 0.14s ease,
    transform 0.14s ease;
}

.toc-panel-item:active {
  color: var(--el-color-primary);
  background: var(--theme-accent-surface-active);
  transform: scale(0.98);
}

.toc-panel-item.is-active .toc-panel-label {
  color: var(--el-color-primary);
}

.toc-panel-item.is-active .toc-panel-dot {
  background: var(--el-color-primary);
}

.toc-panel-item--level-0 {
  padding-left: 10px;
}

.toc-panel-item--level-1 {
  padding-left: 24px;
}

.toc-panel-item--level-2 {
  padding-left: 38px;
}

.toc-panel-badge {
  display: grid;
  flex: 0 0 auto;
  place-items: center;
  width: 20px;
  height: 20px;
  color: var(--text-tertiary);
  font-size: 11px;
  font-weight: 700;
  line-height: 1;
  border-radius: 8px;
}

.toc-panel-badge--index {
  color: var(--el-color-primary);
  background: var(--theme-accent-surface);
}

.toc-panel-dot {
  width: 6px;
  height: 6px;
  border-radius: 999px;
  background: var(--text-tertiary);
  opacity: 0.7;
}

.toc-panel-label {
  flex: 1 1 auto;
  min-width: 0;
  overflow: hidden;
  font-size: 13px;
  line-height: 1.35;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.toc-panel-item--level-0 .toc-panel-label {
  color: var(--text-secondary);
  font-weight: 600;
}

.toc-panel-item--level-1 .toc-panel-label,
.toc-panel-item--level-2 .toc-panel-label {
  color: var(--text-tertiary);
}

.toc-panel-active-indicator {
  position: absolute;
  z-index: 0;
  right: 0;
  left: 0;
  border-radius: 10px;
  background: rgba(0, 0, 0, 0.04);
  opacity: 0;
  transition:
    top 0.18s ease,
    height 0.18s ease,
    opacity 0.14s ease;
}

.dark .toc-panel-active-indicator {
  background: rgba(255, 255, 255, 0.06);
}

.toc-panel-enter-active,
.toc-panel-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}

.toc-panel-enter-from,
.toc-panel-leave-to {
  opacity: 0;
  transform: translateY(8px) scale(0.96);
}
</style>
