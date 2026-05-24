<script setup lang="ts">
/* global PointerEvent, HTMLElement */
import ProfileSubpageHeader from '@/modules/个人/components/个人子页面标题.vue'
import { 使用标签栏存储 } from '@/shared/stores/tab-bar'
import type { AppTabId } from '@/shared/tab-bar'
import { computed, reactive, ref } from 'vue'

const tabBar = 使用标签栏存储()
const tabBarSettingsItems = computed(() => tabBar.settingsItems)

interface PointerCardState {
  pointerId: number | null
  startY: number
  offsetY: number
  dragging: boolean
  reorderTriggered: boolean
  dragHandleActive: boolean
}

const cardStateMap = reactive<Record<string, PointerCardState>>({})
const draggingTabId = ref<AppTabId | null>(null)

const DRAG_START_THRESHOLD = 10
const DRAG_REORDER_STEP = 72

function 获取卡片状态(id: AppTabId) {
  if (!cardStateMap[id]) {
    cardStateMap[id] = {
      pointerId: null,
      startY: 0,
      offsetY: 0,
      dragging: false,
      reorderTriggered: false,
      dragHandleActive: false,
    }
  }

  return cardStateMap[id]
}

function canToggleTab(item: {
  visible: boolean
  canHide: boolean
  canShow: boolean
}) {
  return item.visible ? item.canHide : item.canShow
}

function handleToggleItem(item: {
  id: AppTabId
  visible: boolean
  canHide: boolean
  canShow: boolean
}) {
  if (!canToggleTab(item)) {
    return
  }
  handleToggleTab(item.id, !item.visible)
}

function handleToggleTab(id: AppTabId, visible: boolean) {
  tabBar.setTabVisible(id, visible)
}

function 重置卡片状态(id: AppTabId) {
  const state = 获取卡片状态(id)
  state.pointerId = null
  state.offsetY = 0
  state.dragging = false
  state.reorderTriggered = false
  state.dragHandleActive = false
  if (draggingTabId.value === id) {
    draggingTabId.value = null
  }
}

function 获取项目索引(id: AppTabId) {
  return tabBarSettingsItems.value.findIndex((item) => item.id === id)
}

function handlePointerDown(event: PointerEvent, id: AppTabId) {
  if (!event.isPrimary) {
    return
  }

  const target = event.target
  const state = 获取卡片状态(id)
  state.pointerId = event.pointerId
  state.startY = event.clientY
  state.offsetY = 0
  state.dragging = false
  state.reorderTriggered = false
  state.dragHandleActive = target instanceof HTMLElement && target.closest('[data-tabbar-drag-handle="true"]') !== null

  const currentTarget = event.currentTarget
  if (currentTarget instanceof HTMLElement) {
    currentTarget.setPointerCapture(event.pointerId)
  }
}

function handlePointerMove(event: PointerEvent, id: AppTabId) {
  const state = 获取卡片状态(id)
  if (state.pointerId !== event.pointerId) {
    return
  }

  const deltaY = event.clientY - state.startY

  if (!state.dragging) {
    if (!state.dragHandleActive || Math.abs(deltaY) < DRAG_START_THRESHOLD) {
      return
    }

    state.dragging = true
    draggingTabId.value = id
    console.info('[PhoneTabBarPage] 开始拖动标签卡片', { id })
  }

  if (state.dragging) {
    state.offsetY = deltaY
    event.preventDefault()

    const currentIndex = 获取项目索引(id)
    if (currentIndex < 0) {
      return
    }

    const steps = Math.trunc(state.offsetY / DRAG_REORDER_STEP)
    if (steps === 0) {
      return
    }

    const nextIndex = currentIndex + steps
    const moved = tabBar.moveTabTo(id, nextIndex)
    if (moved) {
      state.startY = event.clientY
      state.offsetY = 0
      state.reorderTriggered = true
    }
  }
}

function handlePointerEnd(event: PointerEvent, id: AppTabId) {
  const state = 获取卡片状态(id)
  if (state.pointerId !== event.pointerId) {
    return
  }

  const currentTarget = event.currentTarget
  if (currentTarget instanceof HTMLElement && currentTarget.hasPointerCapture(event.pointerId)) {
    currentTarget.releasePointerCapture(event.pointerId)
  }

  重置卡片状态(id)
}

function handleCardClick(item: {
  id: AppTabId
  visible: boolean
  canHide: boolean
  canShow: boolean
}) {
  const state = 获取卡片状态(item.id)
  if (state.dragging || state.reorderTriggered || Math.abs(state.offsetY) > 6) {
    return
  }

  handleToggleItem(item)
}

function 获取卡片样式(id: AppTabId) {
  const state = 获取卡片状态(id)

  return {
    transform: `translate3d(0, ${state.offsetY}px, 0)`,
    transition: state.dragging ? 'none' : 'transform 0.22s ease, box-shadow 0.22s ease',
    zIndex: draggingTabId.value === id ? 2 : 1,
  }
}
</script>

<template>
  <section class="page tabbar-page">
    <ProfileSubpageHeader
      title="底部导航"
    />

    <section class="panel-card tabbar-panel">
      <strong class="section-title">已选 {{ tabBar.visibleTabIds.length }} / {{ tabBar.maximumVisibleTabCount }} 个标签</strong>
      <div class="tabbar-list-scroll">
        <div class="tabbar-settings-list">
          <article
            v-for="item in tabBarSettingsItems"
            :key="item.id"
            class="tabbar-settings-item"
            :class="{
              'tabbar-settings-item--visible': item.visible,
              'tabbar-settings-item--hidden': !item.visible,
              'tabbar-settings-item--locked': !canToggleTab(item),
              'tabbar-settings-item--dragging': draggingTabId === item.id,
            }"
            tabindex="0"
            :style="获取卡片样式(item.id)"
            @click="handleCardClick(item)"
            @keydown.enter.prevent="handleToggleItem(item)"
            @keydown.space.prevent="handleToggleItem(item)"
            @pointerdown="handlePointerDown($event, item.id)"
            @pointermove="handlePointerMove($event, item.id)"
            @pointerup="handlePointerEnd($event, item.id)"
            @pointercancel="handlePointerEnd($event, item.id)"
          >
            <div class="tabbar-settings-main">
              <span class="tabbar-settings-icon">
                <component :is="item.icon" />
              </span>
              <div class="tabbar-settings-text">
                <strong>{{ item.label }}</strong>
              </div>
            </div>
            <div class="tabbar-settings-actions">
              <span class="tabbar-settings-drag-handle" data-tabbar-drag-handle="true" aria-hidden="true" @click.stop>⋮⋮</span>
            </div>
          </article>
        </div>
      </div>
    </section>
  </section>
</template>
<style scoped>
.tabbar-page {
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.tabbar-panel {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 14px;
  overflow: hidden;
  padding-right: 0;
}

.tabbar-list-scroll {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overscroll-behavior-y: contain;
  -webkit-overflow-scrolling: touch;
  padding-right: 8px;
}

.tabbar-settings-list {
  display: grid;
  gap: 12px;
  padding-right: 12px;
}

.tabbar-settings-item {
  position: relative;
  overflow: hidden;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border: 1px solid var(--theme-card-border);
  border-radius: 18px;
  background: var(--theme-panel-subtle);
  cursor: pointer;
  touch-action: pan-y;
  user-select: none;
  transition: background-color 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease, transform 0.18s ease;
}

.tabbar-settings-item:focus-visible {
  outline: none;
  border-color: color-mix(in srgb, var(--el-color-primary) 36%, transparent);
  box-shadow: 0 0 0 3px var(--theme-focus-ring);
}

.tabbar-settings-item--visible {
  background: color-mix(in srgb, var(--theme-accent-soft) 68%, var(--theme-panel-subtle));
  border-color: color-mix(in srgb, var(--el-color-primary) 28%, var(--theme-card-border));
}

.tabbar-settings-item--hidden {
  opacity: 0.88;
}

.tabbar-settings-item--locked {
  cursor: default;
}

.tabbar-settings-item--dragging {
  box-shadow: 0 14px 30px color-mix(in srgb, var(--theme-card-shadow) 45%, transparent);
}

.tabbar-settings-item:not(.tabbar-settings-item--locked):active {
  transform: scale(0.992);
}

.tabbar-settings-main {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 12px;
}

.tabbar-settings-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 42px;
  height: 42px;
  border-radius: 14px;
  color: var(--theme-accent-strong);
  background: var(--theme-panel-soft);
  border: 1px solid var(--theme-card-border);
}

.tabbar-settings-icon :deep(svg) {
  width: 20px;
  height: 20px;
  color: currentColor;
  fill: currentColor;
}

.tabbar-settings-text {
  min-width: 0;
  display: grid;
  gap: 4px;
}

.tabbar-settings-actions {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 0 0 auto;
}

.tabbar-settings-drag-handle {
  touch-action: none;
  color: var(--text-quaternary);
  font-size: 16px;
  letter-spacing: 1px;
  cursor: grab;
}

.tabbar-settings-item--dragging .tabbar-settings-drag-handle {
  cursor: grabbing;
}

.tabbar-settings-item--visible .tabbar-settings-icon {
  background: color-mix(in srgb, var(--theme-accent-soft) 82%, white 18%);
}
</style>
