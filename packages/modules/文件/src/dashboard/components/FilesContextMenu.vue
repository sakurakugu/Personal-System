<script setup lang="ts">
import type {
  右键菜单状态,
  文件夹展示项,
  文件展示项,
} from '../../core/shared'
import {
  是否文章图片,
  是否内容图片,
  是否图片,
  是否可移动文件,
  是否可预览媒体,
  是否视频,
} from '../../core/resource'

defineProps<{
  右键菜单: 右键菜单状态
  右键菜单文件夹: 文件夹展示项 | null
  右键菜单文件: 文件展示项 | null
  已选资源总数: number
  当前选择可移动: boolean
  是否全局搜索模式: boolean
  已选资源下载菜单文案: string
  已选资源移动菜单文案: string
  已选资源重命名文案: string
  已选资源删除菜单文案: string
  当前右键菜单文件夹已选中: boolean
  当前右键菜单文件已选中: boolean
}>()

const emit = defineEmits<{
  'create-folder': []
  'upload-files': []
  'upload-folders': []
  'download-selected': []
  'move-selected': []
  'batch-rename': []
  'delete-selected': []
  'open-folder': [folderId: string]
  'download-folder': [folderId: string]
  'rename-folder': [folder: 文件夹展示项]
  'move-folder': [folderId: string]
  'toggle-folder-select': [folderId: string]
  'delete-folder': [folder: 文件夹展示项]
  'open-preview': [file: 文件展示项]
  'open-file': [url: string]
  'open-article': [articleId: string]
  'open-file-folder': [folderId: string | null]
  'download-file': [fileId: string]
  'rename-file': [file: 文件展示项]
  'move-file': [fileId: string]
  'copy-image-link': [url: string]
  'toggle-file-select': [fileId: string]
  'delete-file': [fileId: string]
}>()
</script>

<template>
  <div
    v-if="右键菜单.visible"
    class="context-menu"
    :style="{ left: `${右键菜单.x}px`, top: `${右键菜单.y}px` }"
    @click.stop
  >
    <template v-if="右键菜单.scope === 'blank'">
      <button type="button" class="context-menu__item" @click="emit('create-folder')">新建文件夹</button>
      <button type="button" class="context-menu__item" @click="emit('upload-files')">上传文件</button>
      <button type="button" class="context-menu__item" @click="emit('upload-folders')">上传目录</button>
      <button
        v-if="已选资源总数 > 0"
        type="button"
        class="context-menu__item"
        @click="emit('download-selected')"
      >
        {{ 已选资源下载菜单文案 }}
      </button>
      <button
        v-if="已选资源总数 > 0 && 当前选择可移动"
        type="button"
        class="context-menu__item"
        @click="emit('move-selected')"
      >
        {{ 已选资源移动菜单文案 }}
      </button>
      <button
        v-if="已选资源总数 > 0 && !是否全局搜索模式"
        type="button"
        class="context-menu__item"
        @click="emit('batch-rename')"
      >
        {{ 已选资源重命名文案 }}
      </button>
      <button
        v-if="已选资源总数 > 0"
        type="button"
        class="context-menu__item is-danger"
        @click="emit('delete-selected')"
      >
        {{ 已选资源删除菜单文案 }}
      </button>
    </template>

    <template v-else-if="右键菜单.scope === 'folder' && 右键菜单文件夹">
      <button type="button" class="context-menu__item" @click="emit('open-folder', 右键菜单文件夹.id)">打开文件夹</button>
      <button type="button" class="context-menu__item" @click="emit('download-folder', 右键菜单文件夹.id)">打包下载</button>
      <button type="button" class="context-menu__item" @click="emit('rename-folder', 右键菜单文件夹)">重命名</button>
      <button
        type="button"
        class="context-menu__item"
        @click="emit('move-folder', 右键菜单文件夹.id)"
      >
        移动到
      </button>
      <button
        type="button"
        class="context-menu__item"
        @click="emit('toggle-folder-select', 右键菜单文件夹.id)"
      >
        {{ 当前右键菜单文件夹已选中 ? '取消选择' : '选择此文件夹' }}
      </button>
      <button type="button" class="context-menu__item is-danger" @click="emit('delete-folder', 右键菜单文件夹)">
        删除
      </button>
    </template>

    <template v-else-if="右键菜单.scope === 'file' && 右键菜单文件">
      <button
        v-if="是否可预览媒体(右键菜单文件)"
        type="button"
        class="context-menu__item"
        @click="emit('open-preview', 右键菜单文件)"
      >
        {{ 是否图片(右键菜单文件) ? '查看图片' : (是否视频(右键菜单文件) ? '预览视频' : '预览媒体') }}
      </button>
      <button type="button" class="context-menu__item" @click="emit('open-file', 右键菜单文件.url)">打开文件</button>
      <button
        v-if="是否文章图片(右键菜单文件) && 右键菜单文件.article_id"
        type="button"
        class="context-menu__item"
        @click="emit('open-article', 右键菜单文件.article_id)"
      >
        编辑文章
      </button>
      <button
        v-else-if="是否全局搜索模式 && !是否内容图片(右键菜单文件)"
        type="button"
        class="context-menu__item"
        @click="emit('open-file-folder', 右键菜单文件.folder_id)"
      >
        打开所在目录
      </button>
      <button type="button" class="context-menu__item" @click="emit('download-file', 右键菜单文件.id)">直接下载</button>
      <button type="button" class="context-menu__item" @click="emit('rename-file', 右键菜单文件)">重命名</button>
      <button
        v-if="是否可移动文件(右键菜单文件)"
        type="button"
        class="context-menu__item"
        @click="emit('move-file', 右键菜单文件.id)"
      >
        移动到
      </button>
      <button
        v-if="是否内容图片(右键菜单文件)"
        type="button"
        class="context-menu__item"
        @click="emit('copy-image-link', 右键菜单文件.url)"
      >
        复制图片链接
      </button>
      <button
        type="button"
        class="context-menu__item"
        @click="emit('toggle-file-select', 右键菜单文件.id)"
      >
        {{ 当前右键菜单文件已选中 ? '取消选择' : '选择此文件' }}
      </button>
      <button type="button" class="context-menu__item is-danger" @click="emit('delete-file', 右键菜单文件.id)">
        删除
      </button>
    </template>
  </div>
</template>

<style scoped>
.context-menu {
  position: fixed;
  z-index: 3000;
  min-width: 180px;
  padding: 8px;
  border: 1px solid var(--el-border-color);
  border-radius: 14px;
  background: var(--el-bg-color);
  box-shadow: 0 20px 40px rgba(15, 23, 42, 0.18);
}

.context-menu__item {
  display: block;
  width: 100%;
  padding: 9px 12px;
  border: none;
  border-radius: 10px;
  background: transparent;
  text-align: left;
  color: var(--el-text-color-regular);
  cursor: pointer;
}

.context-menu__item:hover {
  background: var(--el-fill-color-light);
}

.context-menu__item.is-danger {
  color: var(--el-color-danger);
}
</style>
