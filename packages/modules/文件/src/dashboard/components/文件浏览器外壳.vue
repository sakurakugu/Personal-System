<script setup lang="ts">
import type { ComponentPublicInstance } from 'vue'
import { ElCard, ElSkeleton } from 'element-plus'

defineProps<{
  loading: boolean
  布局样式: Record<string, string>
  正在拖动分隔线: boolean
  设置布局容器引用: (element: globalThis.Element | ComponentPublicInstance | null) => void
}>()

const emit = defineEmits<{
  'resizer-pointerdown': [event: globalThis.PointerEvent]
}>()
</script>

<template>
  <div class="page-body">
    <ElSkeleton :loading="loading" animated class="page-skeleton">
      <ElCard shadow="never" class="explorer-shell">
        <div
          :ref="设置布局容器引用"
          class="explorer-layout"
          :style="布局样式"
        >
          <slot name="sidebar" />

          <button
            type="button"
            class="explorer-resizer"
            :class="{ 'is-dragging': 正在拖动分隔线 }"
            aria-label="拖动调整目录树宽度"
            @pointerdown="emit('resizer-pointerdown', $event)"
          >
            <span class="explorer-resizer__handle" />
          </button>

          <slot />
        </div>

        <slot name="footer" />
      </ElCard>
    </ElSkeleton>
  </div>
</template>

<style scoped>
.page-body {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.page-skeleton {
  height: 100%;
}

.explorer-shell {
  border-radius: 18px;
  height: 100%;
  min-height: 0;
}

.explorer-shell :deep(.el-card__body) {
  display: flex;
  flex-direction: column;
  padding: 4px 24px 12px;
  height: 100%;
  overflow: hidden;
  box-sizing: border-box;
}

.explorer-layout {
  display: grid;
  grid-template-columns: clamp(220px, var(--explorer-sidebar-width), 520px) 20px minmax(0, 1fr);
  gap: 0;
  align-items: stretch;
  flex: 1;
  min-height: 0;
}

.explorer-resizer {
  position: relative;
  width: 20px;
  padding: 0;
  border: none;
  background: transparent;
  cursor: col-resize;
  touch-action: none;
}

.explorer-resizer::before {
  content: '';
  position: absolute;
  top: 0;
  bottom: 0;
  left: 50%;
  width: 1px;
  transform: translateX(-50%);
  background: var(--el-border-color);
  transition: background-color 0.2s ease, box-shadow 0.2s ease;
}

.explorer-resizer__handle {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 6px;
  height: 128px;
  border-radius: 999px;
  transform: translate(-50%, -50%);
  background: linear-gradient(
    180deg,
    rgb(var(--el-color-primary-rgb) / 0.18),
    rgb(var(--el-color-primary-rgb) / 0.5),
    rgb(var(--el-color-primary-rgb) / 0.18)
  );
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.explorer-resizer:hover::before,
.explorer-resizer.is-dragging::before {
  background: rgb(var(--el-color-primary-rgb) / 0.56);
  box-shadow: 0 0 0 1px rgb(var(--el-color-primary-rgb) / 0.12);
}

.explorer-resizer:hover .explorer-resizer__handle,
.explorer-resizer.is-dragging .explorer-resizer__handle {
  transform: translate(-50%, -50%) scaleX(1.1);
}

@media (max-width: 960px) {
  .explorer-layout {
    grid-template-columns: 1fr;
    grid-template-rows: minmax(220px, 280px) minmax(0, 1fr);
  }

  .explorer-resizer {
    display: none;
  }
}

@media (max-width: 768px) {
  .explorer-shell :deep(.el-card__body) {
    padding: 4px 16px 10px;
  }
}
</style>
