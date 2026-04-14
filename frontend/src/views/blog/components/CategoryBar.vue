<script setup lang="ts">
/* global HTMLElement, WheelEvent */
import { Icon } from '@iconify/vue'
import { nextTick, onMounted, ref, watch } from 'vue'
import type { CategoryRecord } from '../../../features/articles/types'

const props = defineProps<{
  categories: CategoryRecord[]
  activeCategory: string | null
  totalArticles: number
  viewMode?: 'feed' | 'archive'
}>()

const emit = defineEmits<{
  select: [slug: string | null]
  archive: []
}>()

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
        :class="{ active: !activeCategory }"
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
    </div>
  </div>
</template>

<style scoped>
.category-bar {
  background: var(--card-bg-transparent);
  border-radius: var(--radius-large);
  border: 1px solid rgba(255, 255, 255, 0.45);
  backdrop-filter: blur(18px);
  padding: 0.75rem;
  margin-bottom: 0.1rem;
  box-shadow: 0 10px 30px rgba(148, 163, 184, 0.14);
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
</style>
