<script setup lang="ts">
/* global Event, MouseEvent, TouchEvent */
import { Expand, Fold, Grid } from '@element-plus/icons-vue'
import { ElAside, ElButton, ElContainer, ElIcon, ElMain, ElMenu, ElMenuItem } from 'element-plus'
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useViewport } from '../../../shared/composables/useViewport'
import type { 控制台侧栏模式, 控制台菜单项 } from './console-layout'

const props = defineProps<{
  title: string
  storageKey: string
  menuItems: 控制台菜单项[]
}>()

const route = useRoute()

function 读取侧栏偏好状态(): 控制台侧栏模式 {
  const value = window.localStorage.getItem(props.storageKey)
  if (value === 'expanded' || value === 'compact' || value === 'hidden') {
    return value
  }
  return 'expanded'
}

function 保存侧栏偏好状态(mode: 控制台侧栏模式) {
  window.localStorage.setItem(props.storageKey, mode)
}

const userPreferredSiderMode = ref<控制台侧栏模式>('expanded')
const siderMode = ref<控制台侧栏模式>('expanded')
const autoCompact = ref(false)
const siderWidth = 200
const siderCompactWidth = 64
const siderHiddenWidth = 0
const collapseRatio = 0.22
const expandRatio = 0.2
const { width } = useViewport()

const isCompact = computed(() => siderMode.value === 'compact')
const isHidden = computed(() => siderMode.value === 'hidden')
const currentSiderWidth = computed(() => {
  if (siderMode.value === 'hidden') return siderHiddenWidth
  if (siderMode.value === 'compact') return siderCompactWidth
  return siderWidth
})
const triggerIcon = computed(() => (isHidden.value ? Expand : Fold))
const triggerText = computed(() => {
  if (isHidden.value) return '展开侧栏'
  if (isCompact.value) return '继续收起'
  return '收起侧栏'
})

function toggleSider() {
  if (isHidden.value) {
    const nextMode = width.value && siderWidth / width.value >= collapseRatio ? 'compact' : 'expanded'
    userPreferredSiderMode.value = nextMode
    保存侧栏偏好状态(nextMode)
    siderMode.value = nextMode
    autoCompact.value = false
    return
  }
  if (isCompact.value) {
    userPreferredSiderMode.value = 'hidden'
    保存侧栏偏好状态('hidden')
    siderMode.value = 'hidden'
    autoCompact.value = false
    return
  }
  userPreferredSiderMode.value = 'compact'
  保存侧栏偏好状态('compact')
  siderMode.value = 'compact'
  autoCompact.value = false
}

function applyAutoCollapse() {
  if (!width.value) return
  if (userPreferredSiderMode.value === 'hidden') {
    siderMode.value = 'hidden'
    autoCompact.value = false
    return
  }
  if (userPreferredSiderMode.value === 'compact') {
    siderMode.value = 'compact'
    autoCompact.value = false
    return
  }

  const ratio = siderWidth / width.value
  if (ratio >= collapseRatio) {
    siderMode.value = 'compact'
    autoCompact.value = true
    return
  }

  if (autoCompact.value && ratio <= expandRatio) {
    siderMode.value = 'expanded'
    autoCompact.value = false
  }
}

const HANDLE_MIN_BOTTOM = 80
const DEFAULT_BOTTOM_OFFSET = 12
const handleBottom = ref(DEFAULT_BOTTOM_OFFSET)
const isDragging = ref(false)
const hasMoved = ref(false)
const dragState = reactive({
  startY: 0,
  startBottom: 0,
})

function getSafeAreaBottom() {
  const safeArea = parseInt(window.getComputedStyle(document.documentElement).getPropertyValue('--app-safe-area-bottom') || '0')
  return safeArea || 0
}

function getMaxBottom() {
  return window.innerHeight - HANDLE_MIN_BOTTOM
}

function onHandleTouchStart(e: Event) {
  isDragging.value = true
  hasMoved.value = false
  dragState.startBottom = handleBottom.value

  if (e instanceof TouchEvent) {
    dragState.startY = e.touches[0].clientY
  } else if (e instanceof MouseEvent) {
    dragState.startY = e.clientY
  }
}

function onHandleTouchMove(e: Event) {
  if (!isDragging.value) return
  e.preventDefault()

  let clientY = 0
  if (e instanceof TouchEvent) {
    clientY = e.touches[0].clientY
  } else if (e instanceof MouseEvent) {
    clientY = e.clientY
  }

  if (Math.abs(clientY - dragState.startY) > 3) {
    hasMoved.value = true
  }

  const deltaY = dragState.startY - clientY
  const newBottom = dragState.startBottom + deltaY
  const maxBottom = getMaxBottom()
  const safeArea = getSafeAreaBottom()
  const minBottom = DEFAULT_BOTTOM_OFFSET + safeArea

  handleBottom.value = Math.max(minBottom, Math.min(maxBottom, newBottom))
}

function onHandleTouchEnd() {
  isDragging.value = false
  setTimeout(() => {
    hasMoved.value = false
  }, 50)
}

function onHandleClick() {
  if (hasMoved.value) {
    return
  }
  toggleSider()
}

onMounted(() => {
  userPreferredSiderMode.value = 读取侧栏偏好状态()
  siderMode.value = userPreferredSiderMode.value
  applyAutoCollapse()

  document.body.style.overflow = 'hidden'

  window.addEventListener('mousemove', onHandleTouchMove)
  window.addEventListener('mouseup', onHandleTouchEnd)
  window.addEventListener('touchmove', onHandleTouchMove, { passive: false })
  window.addEventListener('touchend', onHandleTouchEnd)
})

onBeforeUnmount(() => {
  document.body.style.overflow = ''

  window.removeEventListener('mousemove', onHandleTouchMove)
  window.removeEventListener('mouseup', onHandleTouchEnd)
  window.removeEventListener('touchmove', onHandleTouchMove)
  window.removeEventListener('touchend', onHandleTouchEnd)
})

watch(width, () => {
  applyAutoCollapse()
}, { immediate: true })
</script>

<template>
  <ElContainer class="console-layout">
    <ElAside
      class="console-sider"
      :class="{
        'is-compact': isCompact,
        'is-hidden': isHidden,
      }"
      :width="`${currentSiderWidth}px`"
    >
      <div class="sider-inner">
        <div class="sider-title">
          <ElIcon><Grid /></ElIcon>
          <span class="sider-title-text">{{ title }}</span>
        </div>
        <ElMenu
          :collapse="isCompact"
          :collapse-transition="false"
          :default-active="route.path"
        >
          <ElMenuItem
            v-for="item in menuItems"
            :key="item.key"
            :index="item.key"
            :disabled="item.disabled"
            :class="{ 'menu-item--divider-before': item.dividerBefore }"
          >
            <RouterLink
              v-if="!item.disabled"
              :to="item.key"
              class="menu-link-overlay"
              :aria-label="item.label"
            />
            <ElIcon class="menu-icon"><component :is="item.icon" /></ElIcon>
            <template #title>{{ item.label }}</template>
          </ElMenuItem>
        </ElMenu>
        <div class="sider-footer" :style="isHidden ? { bottom: `calc(${handleBottom}px + var(--app-safe-area-bottom, 0px))` } : {}">
          <ElButton
            text
            class="sider-trigger"
            :class="{ 'is-dragging': isDragging }"
            @click="onHandleClick"
            @mousedown="onHandleTouchStart"
            @touchstart="onHandleTouchStart"
          >
            <ElIcon class="trigger-icon">
              <component :is="triggerIcon" />
            </ElIcon>
            <span class="sider-trigger-text">{{ triggerText }}</span>
          </ElButton>
        </div>
      </div>
    </ElAside>
    <ElMain class="console-main">
      <slot />
    </ElMain>
  </ElContainer>
</template>

<style scoped>
.console-layout {
  height: calc(var(--app-viewport-height) - var(--app-header-height));
  display: flex;
  overflow: hidden;
}

.console-sider {
  align-self: stretch;
  overflow: hidden;
  transition: width 0.24s cubic-bezier(0.22, 1, 0.36, 1);
  border-right: 1px solid var(--el-border-color);
  will-change: width;
  position: relative;
}

.sider-inner {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 8px 0;
  overflow: hidden;
}

.sider-inner :deep(.el-menu) {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  scrollbar-width: none;
  -ms-overflow-style: none;
  border-right: none;
}

.sider-inner :deep(.el-menu-item) {
  position: relative;
}

.sider-inner :deep(.el-menu::-webkit-scrollbar) {
  display: none;
}

.menu-link-overlay {
  position: absolute;
  inset: 0;
  z-index: 1;
  display: block;
}

.menu-link-overlay:focus-visible {
  outline: 2px solid var(--el-color-primary);
  outline-offset: -2px;
  border-radius: 6px;
}

.sider-title {
  padding: 8px 16px 16px 24px;
  font-weight: 600;
  font-size: 16px;
  display: flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
  overflow: hidden;
}

.sider-title-text,
.sider-trigger-text {
  opacity: 1;
  transform: translateX(0);
  transition:
    opacity 0.16s ease,
    transform 0.2s ease;
}

.sider-footer {
  margin-top: auto;
  padding: 12px 8px calc(6px + var(--app-safe-area-bottom));
  overflow: hidden;
}

.sider-trigger {
  width: 100%;
  justify-content: flex-start;
  overflow: hidden;
  white-space: nowrap;
}

.menu-icon {
  font-size: 18px;
  line-height: 1;
  position: relative;
  top: -1px;
}

.trigger-icon {
  font-size: 16px;
}

.console-main {
  --dashboard-panel-radius: 12px;
  padding: 0 !important;
  overflow: hidden;
  height: 100%;
  box-sizing: border-box;
}

.console-main :deep(> *) {
  height: 100%;
}

.console-main :deep(.el-card) {
  border-radius: var(--dashboard-panel-radius);
  overflow: hidden;
}

.sider-trigger :deep(.el-button) {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 6px;
  overflow: visible;
  white-space: nowrap;
  padding-left: 20px;
}

.console-sider.is-compact .sider-title {
  padding-left: 24px;
}

.console-sider.is-compact .sider-title-text,
.console-sider.is-compact .sider-trigger-text {
  opacity: 0;
  transform: translateX(-8px);
  pointer-events: none;
}

.console-sider.is-compact .sider-trigger :deep(.el-button) {
  gap: 0;
  justify-content: center;
  padding-left: 0;
}

.sider-inner :deep(.el-menu-item.menu-item--divider-before) {
  position: relative;
  margin-top: 14px;
}

.sider-inner :deep(.el-menu-item.menu-item--divider-before::before) {
  content: '';
  position: absolute;
  left: 16px;
  right: 16px;
  top: -8px;
  height: 1px;
  background-color: var(--el-border-color);
  opacity: 0.9;
}

.console-sider.is-compact .sider-inner :deep(.el-menu-item.menu-item--divider-before::before) {
  left: 12px;
  right: 12px;
}

.console-sider.is-hidden {
  width: 0 !important;
  min-width: 0 !important;
  border-right: none;
  overflow: visible;
}

.console-sider.is-hidden .sider-inner {
  padding: 0;
  overflow: visible;
}

.console-sider.is-hidden .sider-title,
.console-sider.is-hidden .sider-inner :deep(.el-menu) {
  opacity: 0;
  pointer-events: none;
}

.console-sider.is-hidden .sider-footer {
  position: fixed;
  left: 0;
  right: auto;
  bottom: auto;
  padding: 0;
  overflow: visible;
  display: flex;
  justify-content: flex-start;
  z-index: 1000;
  transition: none;
}

.console-sider.is-hidden .sider-trigger {
  width: 60px;
  min-width: 60px;
  max-width: 60px;
  flex: 0 0 60px;
  height: 36px;
  border-radius: 0 16px 16px 0;
  background-color: var(--el-bg-color-overlay);
  box-shadow: 0 6px 18px rgba(15, 23, 42, 0.12);
  border: 1px solid var(--el-border-color-light);
  border-left: none;
  position: relative;
  z-index: 10000;
  cursor: grab;
}

.console-sider.is-hidden .sider-trigger.is-dragging {
  cursor: grabbing;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.18);
}

.console-sider.is-hidden .sider-trigger::before {
  content: '';
  position: absolute;
  left: 10px;
  top: 50%;
  width: 4px;
  height: 16px;
  border-radius: 999px;
  background-color: color-mix(in srgb, var(--el-text-color-secondary) 22%, transparent);
  transform: translateY(-50%);
}

.console-sider.is-hidden :deep(.el-button.sider-trigger) {
  width: 43px;
  min-width: 43px;
  max-width: 43px;
  flex: 0 0 43px;
}

.console-sider.is-hidden :deep(.el-button.sider-trigger .el-button__text) {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
}

.console-sider.is-hidden .sider-trigger :deep(.el-button) {
  width: 100%;
  height: 100%;
  padding: 0 0 0 10px;
  gap: 0;
  justify-content: center;
}

.console-sider.is-hidden .sider-trigger-text {
  display: none;
}

.console-sider.is-hidden .trigger-icon {
  font-size: 18px;
}

.dark .console-sider {
  background-color: var(--sidebar-bg) !important;
  border-right-color: var(--border-color) !important;
}

.dark .sider-title {
  color: var(--text-primary);
}

.dark .sider-trigger:hover {
  background-color: var(--bg-hover) !important;
}

.dark .console-sider.is-hidden .sider-trigger {
  background-color: color-mix(in srgb, var(--sidebar-bg) 88%, #ffffff 12%);
  border-color: var(--border-color);
  box-shadow: 0 10px 28px rgba(2, 6, 23, 0.32);
}

.dark .console-main {
  background-color: var(--bg-primary);
}
</style>
