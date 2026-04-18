<script setup lang="ts">
import type { Component, ComponentPublicInstance } from 'vue'
import { ElCheckbox, ElIcon, ElTag } from 'element-plus'
import { Document, Folder, VideoPlay } from '@element-plus/icons-vue'
import type {
  FileFolderItem,
  FileItem,
  FileSearchFileItem,
  FileSearchFolderItem,
} from '../../types'

type 文件夹展示项 = FileFolderItem | FileSearchFolderItem
type 文件展示项 = FileItem | FileSearchFileItem
type 资源展示项 =
  | { type: 'folder'; id: string; item: 文件夹展示项 }
  | { type: 'file'; id: string; item: 文件展示项 }

const props = withDefaults(defineProps<{
  resource: 资源展示项
  selected: boolean
  isFolder: boolean
  isEditing: boolean
  isCreatingDraft: boolean
  isRenaming: boolean
  canDrag: boolean
  allowDropOnFolder: boolean
  isImage: boolean
  isVideo: boolean
  thumbnailUrl?: string
  displayName: string
  extraDescription?: string
  resourcePath?: string
  primaryTag: string
  purposeTag?: string
  fileSizeText?: string
  fileMimeType?: string
  timeText: string
  fileIcon?: Component
  creatingName?: string
  renamingName?: string
  creatingDisabled?: boolean
  renamingDisabled?: boolean
  setCreatingInputRef?: (element: globalThis.Element | ComponentPublicInstance | null) => void
  setRenamingInputRef?: (element: globalThis.Element | ComponentPublicInstance | null) => void
}>(), {
  thumbnailUrl: '',
  extraDescription: '',
  resourcePath: '',
  purposeTag: '',
  fileSizeText: '',
  fileMimeType: '',
  fileIcon: undefined,
  creatingName: '',
  renamingName: '',
  creatingDisabled: false,
  renamingDisabled: false,
  setCreatingInputRef: undefined,
  setRenamingInputRef: undefined,
})

const emit = defineEmits<{
  'select-change': [selected: boolean]
  'row-click': []
  contextmenu: [event: globalThis.MouseEvent]
  dragstart: [event: globalThis.DragEvent]
  dragend: []
  'drop-folder': [event: globalThis.DragEvent]
  'open-preview': []
  'open-file': []
  'update:creatingName': [value: string]
  'update:renamingName': [value: string]
  'creating-keydown': [event: globalThis.KeyboardEvent]
  'creating-blur': []
  'renaming-keydown': [event: globalThis.KeyboardEvent]
  'renaming-blur': []
}>()
</script>

<template>
  <div
    class="resource-row"
    :class="{
      'is-selected': selected,
      'resource-row--folder': isFolder,
      'resource-row--editing': isEditing,
    }"
    :draggable="canDrag && !isEditing"
    @click="!isEditing && isFolder ? emit('row-click') : null"
    @contextmenu="emit('contextmenu', $event)"
    @dragstart="emit('dragstart', $event)"
    @dragend="emit('dragend')"
    @dragover.prevent
    @drop="isFolder && allowDropOnFolder && !isEditing ? emit('drop-folder', $event) : null"
  >
    <div class="resource-selector" @click.stop>
      <ElCheckbox
        v-if="!isCreatingDraft"
        :model-value="selected"
        @change="emit('select-change', Boolean($event))"
      />
    </div>

    <div v-if="isFolder" class="resource-row__icon resource-row__icon--folder">
      <ElIcon><Folder /></ElIcon>
    </div>
    <div v-else-if="isImage" class="resource-row__preview">
      <img
        :src="thumbnailUrl"
        :alt="displayName"
        loading="lazy"
        decoding="async"
        @click.stop="emit('open-preview')"
      >
    </div>
    <button
      v-else-if="isVideo"
      type="button"
      class="resource-row__preview resource-row__preview--video"
      @click.stop="emit('open-preview')"
    >
      <ElIcon><VideoPlay /></ElIcon>
      <span class="resource-row__preview-badge">VIDEO</span>
    </button>
    <div v-else class="resource-row__icon">
      <ElIcon><component :is="fileIcon || Document" /></ElIcon>
    </div>

    <div class="resource-row__body">
      <input
        v-if="isCreatingDraft"
        :ref="setCreatingInputRef"
        :model-value="creatingName"
        class="resource-row__input"
        :disabled="creatingDisabled"
        placeholder="新建文件夹"
        @click.stop
        @mousedown.stop
        @input="emit('update:creatingName', ($event.target as HTMLInputElement).value)"
        @keydown="emit('creating-keydown', $event)"
        @blur="emit('creating-blur')"
      >
      <input
        v-else-if="isRenaming"
        :ref="setRenamingInputRef"
        :model-value="renamingName"
        class="resource-row__input"
        :disabled="renamingDisabled"
        @click.stop
        @mousedown.stop
        @input="emit('update:renamingName', ($event.target as HTMLInputElement).value)"
        @keydown="emit('renaming-keydown', $event)"
        @blur="emit('renaming-blur')"
      >
      <button
        v-else
        type="button"
        class="resource-row__name"
        @click.stop="isFolder ? emit('row-click') : emit('open-file')"
      >
        {{ displayName }}
      </button>

      <div v-if="!isCreatingDraft && extraDescription" class="resource-row__path">
        {{ extraDescription }}
      </div>
      <div v-if="!isCreatingDraft && resourcePath" class="resource-row__path">
        {{ resourcePath }}
      </div>

      <div class="resource-row__meta">
        <template v-if="isCreatingDraft">
          <ElTag size="small" effect="plain">文件夹</ElTag>
          <span>输入名称后按回车创建，按 Esc 取消</span>
        </template>
        <template v-else>
          <ElTag v-if="purposeTag" size="small" type="success" effect="plain">
            {{ purposeTag }}
          </ElTag>
          <ElTag size="small" effect="plain">{{ primaryTag }}</ElTag>
          <template v-if="!isFolder">
            <span>{{ fileSizeText }}</span>
            <span>{{ fileMimeType }}</span>
          </template>
          <span>{{ timeText }}</span>
        </template>
      </div>
    </div>
  </div>
</template>

<style scoped>
.resource-row {
  position: relative;
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px;
  border: 1px solid var(--el-border-color);
  border-radius: 16px;
  background: var(--el-fill-color-blank);
  transition: border-color 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease, background-color 0.2s ease;
}

.resource-row--folder {
  cursor: pointer;
}

.resource-row--editing {
  cursor: default;
}

.resource-row:hover {
  border-color: rgb(var(--el-color-primary-rgb) / 0.35);
  transform: translateY(-1px);
  box-shadow: 0 14px 28px rgba(15, 23, 42, 0.08);
}

.resource-row.is-selected {
  border-color: rgb(var(--el-color-primary-rgb) / 0.45);
  background: rgb(var(--el-color-primary-rgb) / 0.06);
}

.resource-selector {
  display: flex;
  align-items: center;
  align-self: flex-start;
  flex-shrink: 0;
}

.resource-row__preview,
.resource-row__icon {
  width: 72px;
  height: 72px;
  border-radius: 16px;
  overflow: hidden;
  flex-shrink: 0;
  background: var(--el-fill-color-light);
}

.resource-row__preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  cursor: zoom-in;
}

.resource-row__preview--video {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 0;
  border: none;
  color: #fff;
  background:
    linear-gradient(160deg, rgba(15, 23, 42, 0.92), rgba(30, 41, 59, 0.82)),
    radial-gradient(circle at top, rgb(var(--el-color-primary-rgb) / 0.36), transparent 60%);
  cursor: pointer;
}

.resource-row__preview--video .el-icon {
  font-size: 26px;
}

.resource-row__preview-badge {
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.12);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.resource-row__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--el-color-primary);
  font-size: 28px;
}

.resource-row__icon--folder {
  background: rgb(var(--el-color-primary-rgb) / 0.12);
  color: var(--el-color-primary);
}

.resource-row__body {
  min-width: 0;
  flex: 1;
}

.resource-row__name {
  display: inline-block;
  max-width: 100%;
  padding: 0;
  border: none;
  background: transparent;
  color: inherit;
  font: inherit;
  font-size: 15px;
  font-weight: 600;
  text-align: left;
  cursor: pointer;
}

.resource-row__name:hover {
  color: var(--el-color-primary);
}

.resource-row__input {
  width: min(420px, 100%);
  max-width: 100%;
  height: 32px;
  padding: 0 10px;
  border: 1px solid rgb(var(--el-color-primary-rgb) / 0.32);
  border-radius: 8px;
  background: var(--el-fill-color-blank);
  color: var(--el-text-color-primary);
  font: inherit;
  font-size: 15px;
  font-weight: 600;
  line-height: 32px;
}

.resource-row__input::placeholder {
  color: var(--el-text-color-placeholder);
}

.resource-row__input:focus {
  outline: none;
  border-color: rgb(var(--el-color-primary-rgb) / 0.78);
  box-shadow: 0 0 0 1px rgb(var(--el-color-primary-rgb) / 0.16);
}

.resource-row__input:disabled {
  opacity: 0.7;
  cursor: progress;
}

.resource-row__path {
  margin-top: 8px;
  color: var(--el-text-color-secondary);
  font-size: 13px;
  line-height: 1.5;
  word-break: break-all;
}

.resource-row__meta {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 8px;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

:global(.dark) .resource-row__input {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgb(var(--el-color-primary-rgb) / 0.34);
  color: #fff;
}

:global(.dark) .resource-row__input:focus {
  border-color: rgb(var(--el-color-primary-rgb) / 0.88);
  box-shadow: 0 0 0 1px rgb(var(--el-color-primary-rgb) / 0.22);
}

@media (max-width: 768px) {
  .resource-row {
    flex-direction: column;
    align-items: stretch;
  }

  .resource-selector {
    align-self: flex-start;
  }
}
</style>
