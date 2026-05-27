<script setup lang="ts">
import type { Ref } from 'vue'
import { Icon } from '@iconify/vue'
import type { TreeInstance } from 'element-plus'
import {
  ElIcon,
  ElTree,
} from 'element-plus'
import {
  Folder,
  FolderOpened,
  Picture,
} from '@element-plus/icons-vue'
import type { 目录树节点 } from '../../core/shared'

const props = defineProps<{
  正在上传: boolean
  目录树数据: 目录树节点[]
  选中目录树节点键: string
  当前目录Id: string | null
  重命名目录Id: string | null
  新建目录名称: string
  正在提交新建目录: boolean
  重命名目录名称: string
  正在提交重命名目录: boolean
  目录树引用: Ref<TreeInstance | null>
  新建目录输入框: Ref<globalThis.HTMLInputElement | null>
  重命名目录输入框: Ref<globalThis.HTMLInputElement | null>
  是否可拖拽目录树节点: (node: 目录树节点) => boolean
}>()

const emit = defineEmits<{
  (event: 'create-folder'): void
  (event: 'node-click', data: 目录树节点): void
  (event: 'folder-contextmenu', data: 目录树节点, mouseEvent: globalThis.MouseEvent): void
  (event: 'tree-folder-dragstart', data: 目录树节点, dragEvent: globalThis.DragEvent): void
  (event: 'drag-end'): void
  (event: 'drop-to-folder', folderId: string | null, dragEvent: globalThis.DragEvent): void
  (event: 'update:new-folder-name', value: string): void
  (event: 'update:rename-folder-name', value: string): void
  (event: 'create-keydown', keyboardEvent: globalThis.KeyboardEvent): void
  (event: 'create-blur'): void
  (event: 'rename-keydown', keyboardEvent: globalThis.KeyboardEvent): void
  (event: 'rename-blur'): void
}>()
</script>

<template>
  <aside class="explorer-sidebar">
    <div class="sidebar-card__header">
      <h3 class="sidebar-card__title">目录树</h3>
      <div class="sidebar-card__actions">
        <button
          type="button"
          class="sidebar-action-button"
          :disabled="正在上传"
          title="新建文件夹"
          aria-label="新建文件夹"
          @click="emit('create-folder')"
        >
          <Icon icon="codicon:new-folder" class="sidebar-action-button__icon" aria-hidden="true" />
        </button>
      </div>
    </div>

    <div class="explorer-tree">
      <ElTree
        :ref="目录树引用"
        :data="目录树数据"
        node-key="id"
        default-expand-all
        highlight-current
        :current-node-key="选中目录树节点键"
        :expand-on-click-node="false"
        empty-text="暂无文件夹"
        @node-click="(data: 目录树节点) => emit('node-click', data)"
      >
        <template #default="{ data, node }">
          <div
            class="tree-node"
            :class="{
              'tree-node--draft': data.isDraft,
              'tree-node--editing': 重命名目录Id === data.id,
            }"
            :draggable="是否可拖拽目录树节点(data)"
            @contextmenu="emit('folder-contextmenu', data, $event)"
            @dragstart="emit('tree-folder-dragstart', data, $event)"
            @dragend="emit('drag-end')"
            @dragover.prevent
            @drop="data.isArticleImages || data.isMomentImages || data.isMediaAssets || data.isDraft || 重命名目录Id === data.id ? null : emit('drop-to-folder', data.isRoot ? null : data.id, $event)"
          >
            <ElIcon class="tree-node__icon">
              <component
                :is="data.isArticleImages || data.isMomentImages || data.isMediaAssets
                  ? Picture
                  : (((data.isRoot && 当前目录Id === null) || data.id === 当前目录Id || (node.expanded && !node.isLeaf))
                    ? FolderOpened
                    : Folder)"
              />
            </ElIcon>
            <input
              v-if="data.isDraft"
              :ref="新建目录输入框"
              :value="新建目录名称"
              class="tree-node__input"
              :disabled="正在提交新建目录"
              placeholder="新建文件夹"
              @click.stop
              @mousedown.stop
              @input="emit('update:new-folder-name', ($event.target as HTMLInputElement).value)"
              @keydown="emit('create-keydown', $event)"
              @blur="emit('create-blur')"
            >
            <input
              v-else-if="重命名目录Id === data.id"
              :ref="重命名目录输入框"
              :value="重命名目录名称"
              class="tree-node__input"
              :disabled="正在提交重命名目录"
              @click.stop
              @mousedown.stop
              @input="emit('update:rename-folder-name', ($event.target as HTMLInputElement).value)"
              @keydown="emit('rename-keydown', $event)"
              @blur="emit('rename-blur')"
            >
            <span v-else class="tree-node__label">{{ data.name }}</span>
          </div>
        </template>
      </ElTree>
    </div>
  </aside>
</template>

<style scoped>
.explorer-sidebar {
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  padding-top: 12px;
  padding-right: 20px;
}

.sidebar-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 18px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.sidebar-card__actions {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.sidebar-card__title {
  margin: 0;
}

.sidebar-action-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  padding: 0;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--el-text-color-secondary);
  cursor: pointer;
  transition: background-color 0.18s ease, color 0.18s ease;
}

.sidebar-action-button:hover {
  background: var(--el-fill-color-light);
  color: var(--el-text-color-primary);
}

.sidebar-action-button:focus-visible {
  outline: 2px solid rgb(var(--el-color-primary-rgb) / 0.28);
  outline-offset: 2px;
}

.sidebar-action-button:disabled {
  opacity: 0.48;
  cursor: not-allowed;
}

.sidebar-action-button__icon {
  width: 16px;
  height: 16px;
}

.explorer-tree {
  flex: 1;
  min-height: 0;
  overflow: auto;
  padding-right: 4px;
}

.tree-node {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  min-width: 0;
  padding: 4px 0;
}

.tree-node--draft,
.tree-node--editing {
  padding-right: 6px;
}

.tree-node__icon {
  color: var(--el-color-primary);
  flex-shrink: 0;
}

.tree-node__label {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tree-node__input {
  width: 100%;
  min-width: 0;
  height: 22px;
  padding: 0 6px;
  border: 1px solid rgb(var(--el-color-primary-rgb) / 0.32);
  border-radius: 4px;
  background: var(--el-fill-color-blank);
  color: var(--el-text-color-primary);
  font: inherit;
  line-height: 22px;
}

.tree-node__input::placeholder {
  color: var(--el-text-color-placeholder);
}

.tree-node__input:focus {
  outline: none;
  border-color: rgb(var(--el-color-primary-rgb) / 0.78);
  box-shadow: 0 0 0 1px rgb(var(--el-color-primary-rgb) / 0.16);
}

.tree-node__input:disabled {
  opacity: 0.7;
  cursor: progress;
}

:global(.dark) .sidebar-action-button:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
}

:global(.dark) .tree-node__input {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgb(var(--el-color-primary-rgb) / 0.34);
  color: #fff;
}

:global(.dark) .tree-node__input:focus {
  border-color: rgb(var(--el-color-primary-rgb) / 0.88);
  box-shadow: 0 0 0 1px rgb(var(--el-color-primary-rgb) / 0.22);
}

@media (max-width: 960px) {
  .explorer-sidebar {
    padding-right: 0;
    padding-bottom: 20px;
    border-bottom: 1px solid var(--el-border-color-lighter);
  }
}
</style>
