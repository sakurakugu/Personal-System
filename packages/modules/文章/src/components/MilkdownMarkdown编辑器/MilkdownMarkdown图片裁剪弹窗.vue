<script setup lang="ts">
import { computed, ref } from 'vue'

export interface 图片裁剪矩形 {
  x: number
  y: number
  width: number
  height: number
}

interface 图片自然尺寸 {
  width: number
  height: number
}

interface 图片裁剪拖拽状态 {
  pointerId: number
  mode: 'move' | 'resize'
  startX: number
  startY: number
  startRect: 图片裁剪矩形
}

const props = withDefaults(defineProps<{
  visible: boolean
  previewUrl: string
  rect: 图片裁剪矩形
  naturalSize: 图片自然尺寸
  uploading?: boolean
}>(), {
  uploading: false,
})

const emit = defineEmits<{
  'update:rect': [value: 图片裁剪矩形]
  close: []
  reset: []
  confirm: []
}>()

const imageCropStageRef = ref<HTMLDivElement | null>(null)
const imageCropDragState = ref<图片裁剪拖拽状态 | null>(null)

const imageCropStyle = computed(() => ({
  left: `${props.rect.x * 100}%`,
  top: `${props.rect.y * 100}%`,
  width: `${props.rect.width * 100}%`,
  height: `${props.rect.height * 100}%`,
}))

function startImageCropDrag(mode: 'move' | 'resize', event: PointerEvent) {
  const stage = imageCropStageRef.value
  if (!stage) {
    return
  }

  imageCropDragState.value = {
    pointerId: event.pointerId,
    mode,
    startX: event.clientX,
    startY: event.clientY,
    startRect: { ...props.rect },
  }
  stage.setPointerCapture(event.pointerId)
}

function updateImageCropDrag(event: PointerEvent) {
  const stage = imageCropStageRef.value
  const dragState = imageCropDragState.value
  if (!stage || !dragState || dragState.pointerId !== event.pointerId) {
    return
  }

  const stageRect = stage.getBoundingClientRect()
  const deltaX = stageRect.width <= 0 ? 0 : (event.clientX - dragState.startX) / stageRect.width
  const deltaY = stageRect.height <= 0 ? 0 : (event.clientY - dragState.startY) / stageRect.height
  const minSize = 0.06

  if (dragState.mode === 'move') {
    emit('update:rect', {
      ...dragState.startRect,
      x: clampNumber(dragState.startRect.x + deltaX, 0, 1 - dragState.startRect.width),
      y: clampNumber(dragState.startRect.y + deltaY, 0, 1 - dragState.startRect.height),
    })
    return
  }

  emit('update:rect', {
    ...dragState.startRect,
    width: clampNumber(dragState.startRect.width + deltaX, minSize, 1 - dragState.startRect.x),
    height: clampNumber(dragState.startRect.height + deltaY, minSize, 1 - dragState.startRect.y),
  })
}

function finishImageCropDrag(event: PointerEvent) {
  const stage = imageCropStageRef.value
  const dragState = imageCropDragState.value
  if (!stage || !dragState || dragState.pointerId !== event.pointerId) {
    return
  }

  if (stage.hasPointerCapture(event.pointerId)) {
    stage.releasePointerCapture(event.pointerId)
  }
  imageCropDragState.value = null
}

function clampNumber(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value))
}
</script>

<template>
  <div
    v-if="visible"
    class="milkdown-markdown-editor__crop-dialog"
    role="dialog"
    aria-modal="true"
    aria-label="裁剪上传图片"
  >
    <div class="milkdown-markdown-editor__crop-panel">
      <div class="milkdown-markdown-editor__crop-header">
        <strong>裁剪上传图片</strong>
        <button
          class="milkdown-markdown-editor__crop-close"
          type="button"
          title="关闭"
          @click="emit('close')"
        >
          关闭
        </button>
      </div>
      <div class="milkdown-markdown-editor__crop-stage">
        <div
          ref="imageCropStageRef"
          class="milkdown-markdown-editor__crop-frame"
          @pointermove="updateImageCropDrag"
          @pointerup="finishImageCropDrag"
          @pointercancel="finishImageCropDrag"
        >
          <img
            class="milkdown-markdown-editor__crop-image"
            :src="previewUrl"
            alt="待裁剪图片"
            draggable="false"
          >
          <div
            class="milkdown-markdown-editor__crop-rect"
            :style="imageCropStyle"
            @pointerdown.stop.prevent="startImageCropDrag('move', $event)"
          >
            <span
              class="milkdown-markdown-editor__crop-rect-handle"
              @pointerdown.stop.prevent="startImageCropDrag('resize', $event)"
            />
          </div>
        </div>
      </div>
      <div class="milkdown-markdown-editor__crop-footer">
        <span>
          {{ Math.round(rect.width * naturalSize.width) }}
          ×
          {{ Math.round(rect.height * naturalSize.height) }}
        </span>
        <div class="milkdown-markdown-editor__crop-actions">
          <button type="button" @click="emit('reset')">重置</button>
          <button type="button" @click="emit('close')">取消</button>
          <button type="button" class="is-primary" :disabled="uploading" @click="emit('confirm')">
            上传
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.milkdown-markdown-editor__crop-dialog {
  position: fixed;
  inset: 0;
  z-index: 4100;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  box-sizing: border-box;
  background: rgba(15, 23, 42, 0.48);
}

.milkdown-markdown-editor__crop-panel {
  display: flex;
  flex-direction: column;
  width: min(860px, 100%);
  max-height: min(720px, 100%);
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  overflow: hidden;
  background: var(--el-bg-color-overlay);
  color: var(--el-text-color-primary);
  box-shadow: var(--el-box-shadow-dark);
}

.milkdown-markdown-editor__crop-header,
.milkdown-markdown-editor__crop-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  box-sizing: border-box;
  border-bottom: 1px solid var(--el-border-color-light);
}

.milkdown-markdown-editor__crop-footer {
  border-top: 1px solid var(--el-border-color-light);
  border-bottom: none;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.milkdown-markdown-editor__crop-stage {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 360px;
  max-height: 520px;
  padding: 16px;
  box-sizing: border-box;
  overflow: hidden;
  background:
    linear-gradient(45deg, color-mix(in srgb, var(--el-fill-color) 82%, transparent) 25%, transparent 25%),
    linear-gradient(-45deg, color-mix(in srgb, var(--el-fill-color) 82%, transparent) 25%, transparent 25%),
    linear-gradient(45deg, transparent 75%, color-mix(in srgb, var(--el-fill-color) 82%, transparent) 75%),
    linear-gradient(-45deg, transparent 75%, color-mix(in srgb, var(--el-fill-color) 82%, transparent) 75%);
  background-position: 0 0, 0 10px, 10px -10px, -10px 0;
  background-size: 20px 20px;
}

.milkdown-markdown-editor__crop-frame {
  position: relative;
  display: inline-flex;
  max-width: 100%;
  max-height: 488px;
  touch-action: none;
}

.milkdown-markdown-editor__crop-image {
  display: block;
  max-width: 100%;
  max-height: 488px;
  user-select: none;
}

.milkdown-markdown-editor__crop-rect {
  position: absolute;
  box-sizing: border-box;
  border: 2px solid var(--el-color-primary);
  background: rgba(64, 158, 255, 0.12);
  box-shadow: 0 0 0 9999px rgba(15, 23, 42, 0.38);
  cursor: move;
}

.milkdown-markdown-editor__crop-rect-handle {
  position: absolute;
  right: -7px;
  bottom: -7px;
  width: 14px;
  height: 14px;
  box-sizing: border-box;
  border: 2px solid #fff;
  border-radius: 50%;
  background: var(--el-color-primary);
  cursor: nwse-resize;
}

.milkdown-markdown-editor__crop-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.milkdown-markdown-editor__crop-close,
.milkdown-markdown-editor__crop-actions button {
  min-height: 28px;
  padding: 0 10px;
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
  background: var(--el-bg-color);
  color: var(--el-text-color-primary);
  cursor: pointer;
}

.milkdown-markdown-editor__crop-actions button.is-primary {
  border-color: var(--el-color-primary);
  background: var(--el-color-primary);
  color: #fff;
}

.milkdown-markdown-editor__crop-actions button:disabled {
  cursor: not-allowed;
  opacity: 0.62;
}
</style>
