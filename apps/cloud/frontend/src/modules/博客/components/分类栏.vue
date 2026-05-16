<script setup lang="ts">
/* global HTMLElement, WheelEvent */
import { Icon } from '@iconify/vue'
import { ElBadge } from 'element-plus'
import { nextTick, onMounted, ref, watch } from 'vue'
import type { BlogViewMode } from '../../../modules/博客/view'
import type { CategoryRecord } from '@personal-system/module-articles'
import { useAnnouncementCenter } from '../../../modules/系统/announcement-center'

const props = defineProps<{
  categories: CategoryRecord[]
  activeCategory: string | null
  totalArticles: number
  viewMode?: BlogViewMode
  showAnnouncements?: boolean
  showFilterBar?: boolean
  hasActiveFilters?: boolean
}>()

const emit = defineEmits<{
  select: [slug: string | null]
  archive: []
  bangumi: []
  'toggle-announcements': []
  'announcement-click': []
  'toggle-filter': []
}>()

const { hasUnreadAnnouncement, announcements } = useAnnouncementCenter()

const LONG_PRESS_DURATION = 600
let pressTimer: number | null = null
let longPressTriggered = false

function onAnnouncementPointerDown() {
  longPressTriggered = false
  pressTimer = window.setTimeout(() => {
    longPressTriggered = true
    emit('toggle-announcements')
  }, LONG_PRESS_DURATION)
}

function onAnnouncementPointerUp() {
  if (pressTimer !== null) {
    window.clearTimeout(pressTimer)
    pressTimer = null
  }
}

function onAnnouncementClick() {
  if (longPressTriggered) {
    longPressTriggered = false
    return
  }
  emit('announcement-click')
}

const scrollRef = ref<HTMLElement | null>(null)
const showLeftFade = ref(false)
const showRightFade = ref(false)

function selectCategory(slug: string | null) {
  emit('select', slug)
}

function updateFade() {
  const el = scrollRef.value
  if (!el) return
  const hasOverflow = el.scrollWidth > el.clientWidth + 1
  showLeftFade.value = hasOverflow && el.scrollLeft > 1
  showRightFade.value = hasOverflow && el.scrollLeft + el.clientWidth < el.scrollWidth - 1
}

function onWheel(e: WheelEvent) {
  const el = scrollRef.value
  if (!el || el.scrollWidth <= el.clientWidth) return
  e.preventDefault()
  el.scrollLeft += e.deltaY
}

function scrollActiveIntoView() {
  nextTick(() => {
    const scroll = scrollRef.value
    if (!scroll) return
    const activePill = scroll.querySelector<HTMLElement>('.category-pill.active')
    if (!activePill) return
    const left = activePill.offsetLeft - scroll.offsetLeft - (scroll.clientWidth - activePill.offsetWidth) / 2
    scroll.scrollTo({ left: Math.max(0, left), behavior: 'smooth' })
  })
}

watch(() => props.activeCategory, scrollActiveIntoView, { immediate: true })

onMounted(() => {
  updateFade()
  window.addEventListener('resize', updateFade)
})
</script>

<template>
  <div class="category-bar">
    <div class="category-bar-inner">
      <button
        class="category-pill category-pill--icon"
        :class="{ active: props.viewMode === 'feed' && !activeCategory }"
        aria-label="首页"
        @click="selectCategory(null)"
      >
        <Icon icon="material-symbols:home" class="category-pill-icon" />
      </button>
      <button
        class="category-pill"
        :class="{ active: props.viewMode === 'archive' }"
        @click="emit('archive')"
      >
        归档
        <span class="category-pill-count">{{ totalArticles }}</span>
      </button>
      <div class="category-divider" />
      <button
        class="category-pill category-pill--icon filter-btn"
        :class="{ active: props.showFilterBar || props.hasActiveFilters }"
        aria-label="筛选"
        @click="emit('toggle-filter')"
      >
        <Icon icon="material-symbols:filter-list" class="category-pill-icon" />
      </button>
      <div class="scroll-area">
        <div
          class="scroll-fade scroll-fade-left"
          :data-visible="showLeftFade || undefined"
          aria-hidden="true"
        />
        <div
          ref="scrollRef"
          class="category-scroll"
          @scroll="updateFade"
          @wheel="onWheel"
        >
          <button
            v-for="cat in categories"
            :key="cat.id"
            class="category-pill"
            :class="{ active: activeCategory === cat.slug }"
            @click="selectCategory(cat.slug)"
          >
            {{ cat.name }}
            <span class="category-pill-count">{{ cat.article_count || 0 }}</span>
          </button>
        </div>
        <div
          class="scroll-fade scroll-fade-right"
          :data-visible="showRightFade || undefined"
          aria-hidden="true"
        />
      </div>

      <button
        v-if="announcements.length > 0"
        class="category-pill category-pill--icon announcement-btn"
        :class="{ 'announcement-btn--hidden': !props.showAnnouncements, active: props.viewMode === 'announcements' }"
        :data-tooltip="props.showAnnouncements ? '长按关闭公告显示' : '长按开启公告显示'"
        @pointerdown="onAnnouncementPointerDown"
        @pointerup="onAnnouncementPointerUp"
        @pointerleave="onAnnouncementPointerUp"
        @pointercancel="onAnnouncementPointerUp"
        @click="onAnnouncementClick"
        @contextmenu.prevent
      >
        <ElBadge v-if="hasUnreadAnnouncement && props.showAnnouncements" is-dot class="announcement-badge">
          <Icon icon="material-symbols:notifications-outline" class="category-pill-icon" />
        </ElBadge>
        <Icon v-else-if="props.showAnnouncements" icon="material-symbols:notifications-outline" class="category-pill-icon" />
        <Icon v-else icon="material-symbols:notifications-off-outline" class="category-pill-icon" />
      </button>
    </div>
  </div>
</template>

<style scoped>
.category-bar {
  position: relative;
  z-index: 2;
  background: var(--card-bg-transparent);
  border-radius: var(--radius-large);
  border: 1px solid rgba(255, 255, 255, 0.45);
  backdrop-filter: blur(18px);
  padding: 0.75rem;
  margin-bottom: 0.1rem;
  box-shadow: 0 10px 30px rgba(148, 163, 184, 0.14);
  transition: transform 0.2s, box-shadow 0.2s, background-color 0.2s, border-color 0.2s;
}

.dark .category-bar {
  border-color: rgba(148, 163, 184, 0.16);
  box-shadow: 0 12px 28px rgba(2, 6, 23, 0.28);
}

.category-bar-inner {
  display: flex;
  align-items: center;
  gap: 8px;
}

.scroll-area {
  flex: 1;
  min-width: 0;
  position: relative;
}

.category-scroll {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  scrollbar-width: none;
  -ms-overflow-style: none;
  scroll-behavior: smooth;
}

.category-scroll::-webkit-scrollbar {
  display: none;
}

.category-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 0.25rem 0.75rem;
  border-radius: 0.5rem;
  border: 1.5px solid var(--line-divider);
  background: transparent;
  color: var(--btn-content);
  font-size: 0.875rem;
  line-height: 1.25rem;
  white-space: nowrap;
  flex-shrink: 0;
  cursor: pointer;
  transition: border-color 150ms ease-out, color 150ms ease-out, background-color 150ms ease-out;
}

.category-pill--icon {
  padding: 0.25rem 0.5rem;
}

.category-pill-icon {
  width: 1.125rem;
  height: 1.125rem;
}

.category-pill-count {
  font-size: 0.75rem;
  opacity: 0.6;
  margin-left: 0.25rem;
}

.category-pill:hover {
  border-color: var(--primary);
  color: var(--primary);
  background: transparent;
}

.category-pill.active {
  background: var(--primary);
  border-color: var(--primary);
  color: white;
}

.category-pill.active:hover {
  background: var(--primary);
  border-color: var(--primary);
  opacity: 0.9;
}

.category-divider {
  width: 1px;
  align-self: stretch;
  background: var(--line-divider);
  flex-shrink: 0;
}

.scroll-fade {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 2.5rem;
  pointer-events: none;
  opacity: 0;
  transition: opacity 300ms ease-in-out;
  z-index: 1;
}

.scroll-fade[data-visible] {
  opacity: 1;
}

.scroll-fade-left {
  left: 0;
  background: linear-gradient(to left, transparent, var(--card-bg));
}

.scroll-fade-right {
  right: 0;
  background: linear-gradient(to right, transparent, var(--card-bg));
}

.filter-btn {
  border: 1.5px solid var(--line-divider);
}

.announcement-btn {
  position: relative;
  border: none;
}

.announcement-btn--hidden {
  opacity: 0.55;
}

.announcement-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.announcement-btn::after {
  content: attr(data-tooltip);
  position: absolute;
  top: calc(100% + 6px);
  left: 50%;
  transform: translateX(-50%);
  padding: 4px 8px;
  background: rgba(0, 0, 0, 0.75);
  color: #fff;
  font-size: 12px;
  border-radius: 4px;
  white-space: nowrap;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.15s ease;
  z-index: 10;
}

.announcement-btn:hover::after {
  opacity: 1;
}

.dark .announcement-btn::after {
  background: rgba(255, 255, 255, 0.9);
  color: #0f172a;
}
</style>
