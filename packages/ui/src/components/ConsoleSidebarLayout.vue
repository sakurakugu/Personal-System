<script setup lang="ts">
import { Grid } from '@element-plus/icons-vue'
import { ElAside, ElContainer, ElIcon, ElMain, ElMenu, ElMenuItem } from 'element-plus'
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import SidebarBottomHandle from './SidebarBottomHandle.vue'
import { 使用侧栏布局 } from '../composables/使用侧栏布局'
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
} = 使用侧栏布局(props.storageKey, props.config)

const 当前激活菜单Key = computed(() => {
  const 精确匹配项 = props.menuItems.find((item) => item.exact && item.key === route.path)
  if (精确匹配项) {
    return 精确匹配项.key
  }

  const 前缀匹配项 = props.menuItems.find((item) => (
    !item.exact
    && (route.path === item.key || route.path.startsWith(`${item.key}/`))
  ))

  return 前缀匹配项?.key ?? route.path
})
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
          :default-active="当前激活菜单Key"
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
        <SidebarBottomHandle
          :hidden="isHidden"
          :compact="isCompact"
          :dragging="isHandleDragging"
          :bottom="handleBottom"
          :text="triggerText"
          @toggle="onHandleClick"
          @drag-start="onHandleTouchStart"
        />
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

.ps-console-sider__title-text {
  opacity: 1;
  transform: translateX(0);
  transition:
    opacity 0.16s ease,
    transform 0.2s ease;
}

.ps-console-sider__menu-icon {
  font-size: 18px;
  line-height: 1;
  position: relative;
  top: -1px;
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

.ps-console-sider.is-compact .ps-console-sider__title {
  padding-left: 24px;
}

.ps-console-sider.is-compact .ps-console-sider__title-text {
  opacity: 0;
  transform: translateX(-8px);
  pointer-events: none;
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

</style>
