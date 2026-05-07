<script setup lang="ts">
import { Expand, Fold, Grid } from '@element-plus/icons-vue'
import { ElAside, ElButton, ElContainer, ElIcon, ElMain, ElMenu, ElMenuItem } from 'element-plus'
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useSidebarLayout } from '../composables/useSidebarLayout'
import type { 侧栏布局配置, 侧栏菜单项 } from '../sidebar-layout'

const props = defineProps<{
  title: string
  storageKey: string
  menuItems: 侧栏菜单项[]
  mainClass?: string
  layoutClass?: string
  siderClass?: string
  mainBaseClass?: string
  config?: 侧栏布局配置
}>()

const route = useRoute()
const {
  handleBottom,
  isHandleDragging,
  isResizing,
  isCompact,
  isHidden,
  showResizeHandle,
  currentSiderWidth,
  triggerText,
  onHandleTouchStart,
  onHandleClick,
  onResizerPointerDown,
} = useSidebarLayout(props.storageKey, props.config)

const triggerIcon = computed(() => (isHidden.value ? Expand : Fold))
</script>

<template>
  <ElContainer class="ps-console-layout" :class="layoutClass">
    <ElAside
      class="ps-console-sider"
      :class="[
        siderClass,
        {
          'is-compact': isCompact,
          'is-hidden': isHidden,
          'is-resizing': isResizing,
        },
      ]"
      :width="`${currentSiderWidth}px`"
    >
      <div class="ps-console-sider__inner">
        <div class="ps-console-sider__title">
          <slot name="title-icon">
            <ElIcon><Grid /></ElIcon>
          </slot>
          <span class="ps-console-sider__title-text">{{ title }}</span>
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
              class="ps-console-sider__link-overlay"
              :aria-label="item.label"
            />
            <ElIcon class="ps-console-sider__menu-icon"><component :is="item.icon" /></ElIcon>
            <template #title>{{ item.label }}</template>
          </ElMenuItem>
        </ElMenu>
        <div
          class="ps-console-sider__footer"
          :style="isHidden ? { bottom: `calc(${handleBottom}px + var(--app-safe-area-bottom, 0px))` } : {}"
        >
          <ElButton
            text
            class="ps-console-sider__trigger"
            :class="{ 'is-dragging': isHandleDragging }"
            @click="onHandleClick"
            @mousedown="onHandleTouchStart"
            @touchstart="onHandleTouchStart"
          >
            <ElIcon class="ps-console-sider__trigger-icon">
              <component :is="triggerIcon" />
            </ElIcon>
            <span class="ps-console-sider__trigger-text">{{ triggerText }}</span>
          </ElButton>
        </div>
      </div>
      <button
        v-if="showResizeHandle"
        type="button"
        class="ps-console-sider__resizer"
        :class="{ 'is-dragging': isResizing }"
        aria-label="拖动调整侧栏宽度"
        @pointerdown="onResizerPointerDown"
      >
        <span class="ps-console-sider__resizer-handle" />
      </button>
    </ElAside>
    <ElMain class="ps-console-main" :class="[mainBaseClass, mainClass]">
      <slot />
    </ElMain>
  </ElContainer>
</template>

<style scoped>
.ps-console-layout {
  height: 100%;
  display: flex;
  overflow: hidden;
}

.ps-console-sider {
  align-self: stretch;
  overflow: hidden;
  transition: width 0.24s cubic-bezier(0.22, 1, 0.36, 1);
  border-right: 1px solid var(--el-border-color);
  will-change: width;
  position: relative;
}

.ps-console-sider.is-resizing {
  transition: none;
}

.ps-console-sider__resizer {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  width: 8px;
  padding: 0;
  border: none;
  background: transparent;
  cursor: col-resize;
  touch-action: none;
}

.ps-console-sider__resizer::before {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  width: 1px;
  background: var(--el-border-color);
  opacity: 0;
  transition: background-color 0.2s ease, box-shadow 0.2s ease;
}

.ps-console-sider__resizer-handle {
  position: absolute;
  top: 50%;
  right: 2px;
  width: 3px;
  height: 104px;
  border-radius: 999px;
  transform: translateY(-50%);
  background: linear-gradient(
    180deg,
    rgb(var(--el-color-primary-rgb) / 0.16),
    rgb(var(--el-color-primary-rgb) / 0.48),
    rgb(var(--el-color-primary-rgb) / 0.16)
  );
  opacity: 0;
  transition: transform 0.2s ease, opacity 0.2s ease;
}

.ps-console-sider__resizer:hover::before,
.ps-console-sider__resizer.is-dragging::before {
  background: rgb(var(--el-color-primary-rgb) / 0.56);
  opacity: 1;
  box-shadow: 0 0 0 1px rgb(var(--el-color-primary-rgb) / 0.12);
}

.ps-console-sider__resizer:hover .ps-console-sider__resizer-handle,
.ps-console-sider__resizer.is-dragging .ps-console-sider__resizer-handle {
  opacity: 1;
  transform: translateY(-50%) scaleX(1.08);
}

.ps-console-sider__inner {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 8px 0;
  overflow: hidden;
}

.ps-console-sider__inner :deep(.el-menu) {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  scrollbar-width: none;
  -ms-overflow-style: none;
  border-right: none;
}

.ps-console-sider__inner :deep(.el-menu-item) {
  position: relative;
}

.ps-console-sider__inner :deep(.el-menu::-webkit-scrollbar) {
  display: none;
}

.ps-console-sider__link-overlay {
  position: absolute;
  inset: 0;
  z-index: 1;
  display: block;
}

.ps-console-sider__link-overlay:focus-visible {
  outline: 2px solid var(--el-color-primary);
  outline-offset: -2px;
  border-radius: 6px;
}

.ps-console-sider__title {
  padding: 8px 16px 16px 24px;
  font-weight: 600;
  font-size: 16px;
  display: flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
  overflow: hidden;
}

.ps-console-sider__title-text,
.ps-console-sider__trigger-text {
  opacity: 1;
  transform: translateX(0);
  transition:
    opacity 0.16s ease,
    transform 0.2s ease;
}

.ps-console-sider__footer {
  margin-top: auto;
  padding: 12px 8px calc(6px + var(--app-safe-area-bottom));
  overflow: hidden;
}

.ps-console-sider__trigger {
  width: 100%;
  justify-content: flex-start;
  overflow: hidden;
  white-space: nowrap;
}

.ps-console-sider__menu-icon {
  font-size: 18px;
  line-height: 1;
  position: relative;
  top: -1px;
}

.ps-console-sider__trigger-icon {
  font-size: 16px;
}

.ps-console-main {
  padding: 0 !important;
  overflow: hidden;
  height: 100%;
  box-sizing: border-box;
}

.ps-console-main :deep(> *) {
  height: 100%;
}

.ps-console-sider__trigger :deep(.el-button) {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 6px;
  overflow: visible;
  white-space: nowrap;
  padding-left: 20px;
}

.ps-console-sider.is-compact .ps-console-sider__title {
  padding-left: 24px;
}

.ps-console-sider.is-compact .ps-console-sider__title-text,
.ps-console-sider.is-compact .ps-console-sider__trigger-text {
  opacity: 0;
  transform: translateX(-8px);
  pointer-events: none;
}

.ps-console-sider.is-compact .ps-console-sider__trigger :deep(.el-button) {
  gap: 0;
  justify-content: center;
  padding-left: 0;
}

.ps-console-sider__inner :deep(.el-menu-item.menu-item--divider-before) {
  position: relative;
  margin-top: 14px;
}

.ps-console-sider__inner :deep(.el-menu-item.menu-item--divider-before::before) {
  content: '';
  position: absolute;
  left: 16px;
  right: 16px;
  top: -8px;
  height: 1px;
  background-color: var(--el-border-color);
  opacity: 0.9;
}

.ps-console-sider.is-compact .ps-console-sider__inner :deep(.el-menu-item.menu-item--divider-before::before) {
  left: 12px;
  right: 12px;
}

.ps-console-sider.is-hidden {
  width: 0 !important;
  min-width: 0 !important;
  border-right: none;
  overflow: visible;
}

.ps-console-sider.is-hidden .ps-console-sider__inner {
  padding: 0;
  overflow: visible;
}

.ps-console-sider.is-hidden .ps-console-sider__title,
.ps-console-sider.is-hidden .ps-console-sider__inner :deep(.el-menu) {
  opacity: 0;
  pointer-events: none;
}

.ps-console-sider.is-hidden .ps-console-sider__footer {
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

.ps-console-sider.is-hidden .ps-console-sider__trigger {
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

.ps-console-sider.is-hidden .ps-console-sider__trigger.is-dragging {
  cursor: grabbing;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.18);
}

.ps-console-sider.is-hidden .ps-console-sider__trigger::before {
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

.ps-console-sider.is-hidden :deep(.el-button.ps-console-sider__trigger) {
  width: 43px;
  min-width: 43px;
  max-width: 43px;
  flex: 0 0 43px;
}

.ps-console-sider.is-hidden :deep(.el-button.ps-console-sider__trigger .el-button__text) {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
}

.ps-console-sider.is-hidden .ps-console-sider__trigger :deep(.el-button) {
  width: 100%;
  height: 100%;
  padding: 0 0 0 10px;
  gap: 0;
  justify-content: center;
}

.ps-console-sider.is-hidden .ps-console-sider__trigger-text {
  display: none;
}

.ps-console-sider.is-hidden .ps-console-sider__trigger-icon {
  font-size: 18px;
}
</style>
