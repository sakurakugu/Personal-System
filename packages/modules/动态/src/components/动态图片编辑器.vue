<script setup lang="ts">
import { Picture, Plus, Delete } from '@element-plus/icons-vue'
import { ElButton, ElEmpty, ElIcon, ElTag } from 'element-plus'
import { computed, ref } from 'vue'
import type { MomentImageRecord } from '../types'
import { 解析管理文件URL地址 } from '../managedFile'

const props = defineProps<{
  expanded: boolean
  items: MomentImageRecord[]
  loading: boolean
  uploading: boolean
  maxCount: number
}>()

const emit = defineEmits<{
  toggle: []
  'upload-files': [files: globalThis.File[]]
  delete: [imageId: string]
  reorder: [imageIds: string[]]
}>()

const fileInputRef = ref<globalThis.HTMLInputElement | null>(null)
const draggingImageId = ref<string | null>(null)
const isDraggingFiles = ref(false)
const remainingCount = computed(() => Math.max(0, props.maxCount - props.items.length))

function openFileDialog() {
  if (props.loading || props.uploading || props.items.length >= props.maxCount) {
    return
  }
  fileInputRef.value?.click()
}

function emitSelectedFiles(fileList: globalThis.FileList | null) {
  const files = fileList ? Array.from(fileList) : []
  if (files.length === 0) {
    return
  }
  emit('upload-files', files)
}

function handleFileInputChange(event: globalThis.Event) {
  const target = event.target as globalThis.HTMLInputElement
  emitSelectedFiles(target.files)
  target.value = ''
}

function handleDragEnter(event: globalThis.DragEvent) {
  if (event.dataTransfer?.types.includes('Files')) {
    isDraggingFiles.value = true
  }
}

function handleDragLeave(event: globalThis.DragEvent) {
  const relatedTarget = event.relatedTarget as globalThis.Node | null
  if (relatedTarget && (event.currentTarget as globalThis.HTMLElement | null)?.contains(relatedTarget)) {
    return
  }
  isDraggingFiles.value = false
}

function handleDragOver(event: globalThis.DragEvent) {
  if (event.dataTransfer?.types.includes('Files')) {
    event.preventDefault()
    isDraggingFiles.value = true
  }
}

function handleDropFiles(event: globalThis.DragEvent) {
  if (!event.dataTransfer?.files?.length) {
    return
  }
  event.preventDefault()
  isDraggingFiles.value = false
  emitSelectedFiles(event.dataTransfer.files)
}

function handleImageDragStart(imageId: string) {
  draggingImageId.value = imageId
}

function handleImageDrop(targetImageId: string) {
  const sourceImageId = draggingImageId.value
  draggingImageId.value = null
  if (!sourceImageId || sourceImageId === targetImageId) {
    return
  }

  const ids = props.items.map((item) => item.id)
  const sourceIndex = ids.indexOf(sourceImageId)
  const targetIndex = ids.indexOf(targetImageId)
  if (sourceIndex < 0 || targetIndex < 0) {
    return
  }

  ids.splice(sourceIndex, 1)
  ids.splice(targetIndex, 0, sourceImageId)
  emit('reorder', ids)
}

function getPreviewUrl(image: MomentImageRecord): string {
  return 解析管理文件URL地址(image.thumbnail_url || image.preview_url || image.url)
}
</script>

<template>
  <section class="moment-image-composer">
    <div class="moment-image-composer__toolbar">
      <div class="moment-image-composer__meta">
        <ElButton text class="moment-image-composer__toggle" @click="emit('toggle')">
          <ElIcon><Picture /></ElIcon>
          <span>图片</span>
        </ElButton>
        <ElTag size="small" :type="items.length >= maxCount ? 'danger' : 'info'">
          {{ items.length }} / {{ maxCount }}
        </ElTag>
      </div>
      <ElButton
        size="small"
        type="primary"
        plain
        :disabled="loading || uploading || items.length >= maxCount"
        @click="openFileDialog"
      >
        <ElIcon><Plus /></ElIcon>
        <span>上传图片</span>
      </ElButton>
      <input
        ref="fileInputRef"
        class="moment-image-composer__input"
        type="file"
        accept="image/*"
        multiple
        @change="handleFileInputChange"
      >
    </div>

    <div
      v-if="expanded"
      class="moment-image-composer__panel"
      :class="{ 'is-dragging-files': isDraggingFiles }"
      @dragenter="handleDragEnter"
      @dragleave="handleDragLeave"
      @dragover="handleDragOver"
      @drop="handleDropFiles"
    >
      <div v-if="loading" class="moment-image-composer__placeholder">
        正在加载图片...
      </div>

      <div v-else-if="items.length === 0" class="moment-image-composer__empty">
        <ElEmpty description="当前动态还没有图片" />
      </div>

      <div v-else class="moment-image-composer__list">
        <article
          v-for="image in items"
          :key="image.id"
          class="moment-image-composer__card"
          :class="{ 'is-dragging': draggingImageId === image.id }"
          draggable="true"
          @dragstart="handleImageDragStart(image.id)"
          @dragover.prevent
          @drop.prevent="handleImageDrop(image.id)"
        >
          <img :src="getPreviewUrl(image)" :alt="image.original_name" class="moment-image-composer__preview">
          <button
            type="button"
            class="moment-image-composer__delete"
            :disabled="loading || uploading"
            @click="emit('delete', image.id)"
          >
            <ElIcon><Delete /></ElIcon>
          </button>
        </article>
      </div>

      <div class="moment-image-composer__footer">
        <span>剩余可上传 {{ remainingCount }} 张，拖动图片可调整顺序。</span>
      </div>
    </div>
  </section>
</template>

<style scoped>
.moment-image-composer {
  display: grid;
  gap: 12px;
}

.moment-image-composer__toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.moment-image-composer__meta {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.moment-image-composer__toggle {
  padding-inline: 0;
}

.moment-image-composer__hint,
.moment-image-composer__footer,
.moment-image-composer__placeholder {
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.moment-image-composer__input {
  display: none;
}

.moment-image-composer__panel {
  display: grid;
  gap: 12px;
  padding: 14px;
  border: 1px dashed color-mix(in srgb, var(--el-color-primary) 32%, var(--el-border-color));
  border-radius: 18px;
  background:
    linear-gradient(180deg, color-mix(in srgb, var(--el-color-primary-light-9) 45%, transparent), transparent 58%),
    color-mix(in srgb, var(--el-bg-color) 86%, transparent);
  transition: border-color 0.18s ease, background-color 0.18s ease;
}

.moment-image-composer__panel.is-dragging-files {
  border-color: var(--el-color-primary);
  background:
    linear-gradient(180deg, color-mix(in srgb, var(--el-color-primary-light-8) 62%, transparent), transparent 58%),
    color-mix(in srgb, var(--el-color-primary-light-9) 32%, var(--el-bg-color));
}

.moment-image-composer__empty {
  min-height: 140px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.moment-image-composer__list {
  display: flex;
  gap: 12px;
  overflow-x: auto;
  padding-bottom: 4px;
}

.moment-image-composer__card {
  position: relative;
  flex: 0 0 auto;
  width: 112px;
  aspect-ratio: 1;
  overflow: hidden;
  border: 1px solid color-mix(in srgb, var(--el-border-color) 86%, transparent);
  border-radius: 16px;
  background: var(--el-fill-color-light);
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
  cursor: grab;
}

.moment-image-composer__card.is-dragging {
  opacity: 0.58;
}

.moment-image-composer__preview {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.moment-image-composer__delete {
  position: absolute;
  top: 8px;
  right: 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.72);
  color: #fff;
  cursor: pointer;
}

.moment-image-composer__delete:disabled {
  cursor: not-allowed;
  opacity: 0.58;
}

@media (max-width: 767px) {
  .moment-image-composer__toolbar {
    align-items: stretch;
  }

  .moment-image-composer__list {
    gap: 10px;
  }

  .moment-image-composer__card {
    width: 96px;
  }
}
</style>
