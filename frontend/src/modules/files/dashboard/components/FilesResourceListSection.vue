<script setup lang="ts">
import type { ComponentPublicInstance } from 'vue'
import { ElButton, ElEmpty } from 'element-plus'
import FilesResourceRow from './FilesResourceRow.vue'
import {
  获取资源时间,
} from '../../core/shared'
import type {
  文件展示项,
  资源展示项,
} from '../../core/shared'
import {
  获取图片缩略图链接,
  格式化大小,
  格式化时间,
  是否图片,
  是否视频,
  获取文件图标,
  是否文件夹资源,
  是否文件资源,
  获取资源附加说明,
  获取资源路径,
  获取资源主标签,
  获取资源用途标签,
  是否可拖拽资源,
} from '../../core/resource'

defineProps<{
  当前页资源总数: number
  当前空状态描述: string
  当前渲染资源列表: 资源展示项[]
  是否全局搜索模式: boolean
  右侧新建文件夹名称: string
  列表重命名名称: string
  正在提交右侧新建文件夹: boolean
  正在提交列表重命名: boolean
  是否还有更多资源待渲染: boolean
  当前已渲染资源总数: number
  剩余待渲染资源数: number
  获取增量渲染资源数量: () => number
  是否资源已选中: (resource: 资源展示项) => boolean
  是否资源处于右侧编辑态: (resource: 资源展示项) => boolean
  是否资源是右侧新建文件夹草稿: (resource: 资源展示项) => boolean
  是否资源正在右侧重命名: (resource: 资源展示项) => boolean
  设置右侧新建文件夹输入框引用: (element: globalThis.Element | ComponentPublicInstance | null) => void
  设置列表重命名输入框引用: (element: globalThis.Element | ComponentPublicInstance | null) => void
  设置加载更多哨兵引用: (element: globalThis.Element | ComponentPublicInstance | null) => void
}>()

const emit = defineEmits<{
  'select-change': [payload: { resource: 资源展示项; selected: boolean }]
  'folder-click': [folderId: string]
  contextmenu: [payload: { resource: 资源展示项; mouseEvent: globalThis.MouseEvent }]
  dragstart: [payload: { resource: 资源展示项; dragEvent: globalThis.DragEvent }]
  dragend: []
  'drop-to-folder': [payload: { folderId: string; dragEvent: globalThis.DragEvent }]
  'open-preview': [file: 文件展示项]
  'open-file': [url: string]
  'update:creating-name': [value: string]
  'update:renaming-name': [value: string]
  'creating-keydown': [event: globalThis.KeyboardEvent]
  'creating-blur': []
  'renaming-keydown': [event: globalThis.KeyboardEvent]
  'renaming-blur': []
  'load-more': []
}>()
</script>

<template>
  <div v-if="当前页资源总数 === 0" class="empty-state empty-state--inner">
    <ElEmpty :description="当前空状态描述" />
  </div>

  <section v-else class="resource-section">
    <div class="resource-list">
      <FilesResourceRow
        v-for="resource in 当前渲染资源列表"
        :key="`${resource.type}-${resource.id}`"
        :resource="resource"
        :selected="是否资源已选中(resource)"
        :is-folder="是否文件夹资源(resource)"
        :is-editing="是否资源处于右侧编辑态(resource)"
        :is-creating-draft="是否资源是右侧新建文件夹草稿(resource)"
        :is-renaming="是否资源正在右侧重命名(resource)"
        :can-drag="是否可拖拽资源(resource, 是否全局搜索模式)"
        :allow-drop-on-folder="!是否全局搜索模式"
        :is-image="是否文件资源(resource) && 是否图片(resource.item)"
        :is-video="是否文件资源(resource) && 是否视频(resource.item)"
        :thumbnail-url="是否文件资源(resource) ? 获取图片缩略图链接(resource.item) : ''"
        :display-name="是否文件夹资源(resource) ? resource.item.name : resource.item.original_name"
        :extra-description="获取资源附加说明(resource)"
        :resource-path="获取资源路径(resource, 是否全局搜索模式)"
        :primary-tag="获取资源主标签(resource)"
        :purpose-tag="获取资源用途标签(resource)"
        :file-size-text="是否文件资源(resource) ? 格式化大小(resource.item.size) : ''"
        :file-mime-type="是否文件资源(resource) ? resource.item.mime_type : ''"
        :time-text="格式化时间(获取资源时间(resource))"
        :file-icon="是否文件资源(resource) ? 获取文件图标(resource.item) : undefined"
        :creating-name="右侧新建文件夹名称"
        :renaming-name="列表重命名名称"
        :creating-disabled="正在提交右侧新建文件夹"
        :renaming-disabled="正在提交列表重命名"
        :set-creating-input-ref="设置右侧新建文件夹输入框引用"
        :set-renaming-input-ref="设置列表重命名输入框引用"
        @select-change="emit('select-change', { resource, selected: $event })"
        @row-click="是否文件夹资源(resource) ? emit('folder-click', resource.item.id) : null"
        @contextmenu="emit('contextmenu', { resource, mouseEvent: $event })"
        @dragstart="emit('dragstart', { resource, dragEvent: $event })"
        @dragend="emit('dragend')"
        @drop-folder="是否文件夹资源(resource) ? emit('drop-to-folder', { folderId: resource.item.id, dragEvent: $event }) : null"
        @open-preview="是否文件资源(resource) ? emit('open-preview', resource.item) : null"
        @open-file="是否文件资源(resource) ? emit('open-file', resource.item.url) : null"
        @update:creating-name="emit('update:creating-name', $event)"
        @update:renaming-name="emit('update:renaming-name', $event)"
        @creating-keydown="emit('creating-keydown', $event)"
        @creating-blur="emit('creating-blur')"
        @renaming-keydown="emit('renaming-keydown', $event)"
        @renaming-blur="emit('renaming-blur')"
      />

      <div
        v-if="是否还有更多资源待渲染"
        :ref="设置加载更多哨兵引用"
        class="resource-list__load-more"
      >
        <ElButton @click="emit('load-more')">
          继续加载 {{ Math.min(获取增量渲染资源数量(), 剩余待渲染资源数) }} 项
        </ElButton>
        <span class="resource-list__load-more-text">
          已渲染 {{ 当前已渲染资源总数 }} / {{ 当前页资源总数 }} 项
        </span>
      </div>
    </div>
  </section>
</template>

<style scoped>
.resource-section {
  margin-top: 24px;
}

.resource-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.resource-list__load-more {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 8px 0 4px;
  flex-wrap: wrap;
}

.resource-list__load-more-text {
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 220px;
}

.empty-state--inner {
  min-height: 160px;
  border: 1px dashed var(--el-border-color);
  border-radius: 16px;
  background: var(--el-fill-color-lighter);
}
</style>
