<script setup lang="ts">
import { Expand, Fold } from '@element-plus/icons-vue';
import { ElButton, ElIcon } from 'element-plus';
import { computed } from 'vue';

const props = defineProps<{
  hidden: boolean
  compact: boolean
  dragging: boolean
  bottom: number
  text: string
}>()

const emit = defineEmits<{
  toggle: []
  'drag-start': [event: MouseEvent | TouchEvent]
}>()

const triggerIcon = computed(() => (props.hidden ? Expand : Fold))
const hiddenFooterStyle = computed(() => (
  props.hidden
    ? { bottom: `calc(${props.bottom}px + var(--app-safe-area-bottom, 0px))` }
    : undefined
))

function handleMouseDown(event: MouseEvent) {
  emit('drag-start', event)
}

function handleTouchStart(event: TouchEvent) {
  emit('drag-start', event)
}
</script>

<template>
  <div
    class="ps-sidebar-handle"
    :class="{
      'is-compact': compact,
      'is-hidden': hidden,
    }"
  >
    <div class="ps-sidebar-handle__footer" :style="hiddenFooterStyle">
      <ElButton
        text
        class="ps-sidebar-handle__trigger"
        :class="{ 'is-dragging': dragging }"
        :aria-label="text"
        @click="emit('toggle')"
        @mousedown="handleMouseDown"
        @touchstart="handleTouchStart"
      >
        <ElIcon class="ps-sidebar-handle__trigger-icon">
          <component :is="triggerIcon" />
        </ElIcon>
        <span class="ps-sidebar-handle__trigger-text">{{ text }}</span>
      </ElButton>
    </div>
  </div>
</template>

<style scoped>
.ps-sidebar-handle {
  margin-top: auto;
  overflow: hidden;
}

.ps-sidebar-handle__footer {
  padding: 12px 8px calc(6px + var(--app-safe-area-bottom));
  overflow: hidden;
}

.ps-sidebar-handle__trigger {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  overflow: hidden;
  white-space: nowrap;
}

.ps-sidebar-handle__trigger :deep(.el-button__text) {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  width: 100%;
  gap: 6px;
  overflow: visible;
  white-space: nowrap;
  padding-left: 20px;
  box-sizing: border-box;
}

.ps-sidebar-handle__trigger-text {
  opacity: 1;
  transform: translateX(0);
  transition:
    opacity 0.16s ease,
    transform 0.2s ease;
}

.ps-sidebar-handle__trigger-icon {
  font-size: 16px;
}

.ps-sidebar-handle.is-compact .ps-sidebar-handle__trigger-text {
  display: none;
}

.ps-sidebar-handle.is-compact .ps-sidebar-handle__trigger {
  justify-content: center;
}

.ps-sidebar-handle.is-compact :deep(.el-button.ps-sidebar-handle__trigger) {
  padding: 0;
}

.ps-sidebar-handle.is-compact :deep(.el-button.ps-sidebar-handle__trigger .el-button__text) {
  width: 100%;
  padding: 0;
  box-sizing: border-box;
}

.ps-sidebar-handle.is-compact .ps-sidebar-handle__trigger :deep(.el-button__text) {
  gap: 0;
  justify-content: center;
  padding-left: 0;
}

.ps-sidebar-handle.is-hidden {
  overflow: visible;
}

.ps-sidebar-handle.is-hidden .ps-sidebar-handle__footer {
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

.ps-sidebar-handle.is-hidden .ps-sidebar-handle__trigger {
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

.ps-sidebar-handle.is-hidden .ps-sidebar-handle__trigger.is-dragging {
  cursor: grabbing;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.18);
}

.ps-sidebar-handle.is-hidden .ps-sidebar-handle__trigger::before {
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

.ps-sidebar-handle.is-hidden :deep(.el-button.ps-sidebar-handle__trigger) {
  width: 43px;
  min-width: 43px;
  max-width: 43px;
  flex: 0 0 43px;
}

.ps-sidebar-handle.is-hidden :deep(.el-button.ps-sidebar-handle__trigger .el-button__text) {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
}

.ps-sidebar-handle.is-hidden .ps-sidebar-handle__trigger :deep(.el-button__text) {
  width: 100%;
  height: 100%;
  padding: 0 0 0 0px;
  gap: 0;
  justify-content: center;
}

.ps-sidebar-handle.is-hidden .ps-sidebar-handle__trigger-text {
  display: none;
}

.ps-sidebar-handle.is-hidden .ps-sidebar-handle__trigger-icon {
  font-size: 18px;
}
</style>
