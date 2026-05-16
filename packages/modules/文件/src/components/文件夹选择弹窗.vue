<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import {
  ElBreadcrumb,
  ElBreadcrumbItem,
  ElButton,
  ElEmpty,
  ElIcon,
  ElInput,
  ElMessage,
} from 'element-plus'
import { Folder } from '@element-plus/icons-vue'
import { 获取API错误消息 } from '@personal-system/api'
import { BaseDialog } from '@personal-system/ui'
import { 创建文件夹, 获取文件浏览器数据 } from '../api'
import type { FileBreadcrumbItem, FileExplorerData, FileFolderItem } from '../types'

const props = withDefaults(defineProps<{
  modelValue: boolean
  initialFolderId?: string | null
  title?: string
}>(), {
  initialFolderId: null,
  title: '选择文件夹',
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  confirm: [payload: { folderId: string | null, path: string }]
}>()

const 加载中 = ref(false)
const 创建目录中 = ref(false)
const 展开新建目录 = ref(false)
const 新目录名称 = ref('')
const 目录选择数据 = ref<FileExplorerData | null>(null)
const 新建目录输入框 = ref<InstanceType<typeof ElInput> | null>(null)

const 面包屑 = computed<FileBreadcrumbItem[]>(() => (
  目录选择数据.value?.breadcrumbs ?? [{ id: null, name: '全部文件' }]
))
const 子文件夹 = computed<FileFolderItem[]>(() => 目录选择数据.value?.folders ?? [])
const 当前目录ID = computed<string | null>(() => 目录选择数据.value?.current_folder?.id ?? null)
const 上一层目录ID = computed<string | null>(() => (
  面包屑.value.length > 1 ? (面包屑.value[面包屑.value.length - 2]?.id ?? null) : null
))
const 当前路径 = computed(() => 面包屑.value.map(item => item.name).join(' / '))

function 关闭弹窗() {
  emit('update:modelValue', false)
}

function 关闭新建目录输入框() {
  展开新建目录.value = false
  新目录名称.value = ''
}

async function 聚焦新建目录输入框() {
  await nextTick()
  window.requestAnimationFrame(() => {
    新建目录输入框.value?.focus()
  })
}

async function 打开新建目录输入框() {
  if (展开新建目录.value) {
    await 聚焦新建目录输入框()
    return
  }
  展开新建目录.value = true
  新目录名称.value = ''
  await 聚焦新建目录输入框()
}

async function 加载目录(folderId: string | null) {
  加载中.value = true
  try {
    目录选择数据.value = await 获取文件浏览器数据(folderId)
  } catch (error) {
    ElMessage.error(获取API错误消息(error, '加载目录失败'))
  } finally {
    加载中.value = false
  }
}

async function 进入目录(folderId: string | null) {
  关闭新建目录输入框()
  await 加载目录(folderId)
}

function 处理面包屑点击(item: FileBreadcrumbItem) {
  void 进入目录(item.id)
}

async function 创建当前目录下的新文件夹() {
  if (创建目录中.value) {
    return
  }

  const name = 新目录名称.value.trim()
  if (!name) {
    关闭新建目录输入框()
    return
  }

  创建目录中.value = true
  try {
    await 创建文件夹(name, 当前目录ID.value)
    关闭新建目录输入框()
    await 加载目录(当前目录ID.value)
    ElMessage.success('目录已创建')
  } catch (error) {
    ElMessage.error(获取API错误消息(error, '新建目录失败'))
    await 聚焦新建目录输入框()
  } finally {
    创建目录中.value = false
  }
}

async function 处理新建目录输入框失焦() {
  if (创建目录中.value) {
    return
  }
  await 创建当前目录下的新文件夹()
}

function 处理新建目录键盘事件(event: globalThis.Event | globalThis.KeyboardEvent) {
  if (!(event instanceof globalThis.KeyboardEvent) || event.isComposing) {
    return
  }
  if (event.key === 'Enter') {
    event.preventDefault()
    event.stopPropagation()
    void 创建当前目录下的新文件夹()
    return
  }
  if (event.key === 'Escape') {
    event.preventDefault()
    event.stopPropagation()
    关闭新建目录输入框()
  }
}

function 确认选择() {
  emit('confirm', {
    folderId: 当前目录ID.value,
    path: 当前路径.value,
  })
  关闭新建目录输入框()
  关闭弹窗()
}

watch(
  () => props.modelValue,
  (visible) => {
    if (!visible) {
      目录选择数据.value = null
      关闭新建目录输入框()
      return
    }
    void 加载目录(props.initialFolderId)
  },
)
</script>

<template>
  <BaseDialog
    :model-value="props.modelValue"
    :title="props.title"
    width="720px"
    style="max-width: 96vw"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <div v-loading="加载中" class="folder-picker">
      <div class="folder-picker__toolbar">
        <ElButton :disabled="加载中 || 创建目录中 || (上一层目录ID === null && 当前目录ID === null)" @click="进入目录(上一层目录ID)">
          返回上一级
        </ElButton>
        <div class="folder-picker__toolbar-actions">
          <ElButton :disabled="加载中 || 创建目录中" @click="打开新建目录输入框">
            新建文件夹
          </ElButton>
          <ElButton type="primary" :disabled="加载中" @click="确认选择">
            {{ 当前目录ID ? '选择当前文件夹' : '选择根目录' }}
          </ElButton>
        </div>
      </div>

      <div class="folder-picker__breadcrumbs">
        <ElBreadcrumb separator="/">
          <ElBreadcrumbItem v-for="item in 面包屑" :key="item.id ?? '__root__'">
            <button type="button" class="breadcrumb-button" @click="处理面包屑点击(item)">
              {{ item.name }}
            </button>
          </ElBreadcrumbItem>
        </ElBreadcrumb>
      </div>

      <ElEmpty v-if="子文件夹.length === 0 && !加载中 && !展开新建目录" description="当前目录下暂无子文件夹" />

      <div v-else class="folder-picker__list">
        <div v-if="展开新建目录" class="folder-picker__item folder-picker__item--draft">
          <span class="folder-picker__item-icon">
            <ElIcon><Folder /></ElIcon>
          </span>
          <span class="folder-picker__item-main">
            <ElInput
              ref="新建目录输入框"
              v-model="新目录名称"
              class="folder-picker__item-input"
              maxlength="120"
              placeholder="新建文件夹"
              :disabled="创建目录中"
              @keydown="处理新建目录键盘事件"
              @blur="处理新建目录输入框失焦"
            />
            <span class="folder-picker__item-meta">输入名称后按回车创建，留空则取消</span>
          </span>
        </div>

        <button
          v-for="folder in 子文件夹"
          :key="folder.id"
          type="button"
          class="folder-picker__item"
          @click="进入目录(folder.id)"
        >
          <span class="folder-picker__item-icon">
            <ElIcon><Folder /></ElIcon>
          </span>
          <span class="folder-picker__item-main">
            <span class="folder-picker__item-name">{{ folder.name }}</span>
          </span>
        </button>
      </div>
    </div>
  </BaseDialog>
</template>

<style scoped>
.folder-picker {
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-height: 360px;
}

.folder-picker__toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
}

.folder-picker__toolbar-actions {
  margin-left: auto;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
}

.folder-picker__breadcrumbs {
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px solid var(--el-border-color-lighter);
  background: var(--el-fill-color-extra-light);
}

.folder-picker__breadcrumbs :deep(.el-breadcrumb) {
  line-height: 1.8;
}

.folder-picker__list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.folder-picker__item {
  display: flex;
  align-items: center;
  gap: 14px;
  width: 100%;
  padding: 10px 14px;
  border: 1px solid var(--el-border-color);
  border-radius: 12px;
  background: var(--el-bg-color);
  cursor: pointer;
  text-align: left;
  transition: border-color 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease;
}

.folder-picker__item:hover {
  border-color: var(--el-color-primary-light-5);
  transform: translateY(-1px);
  box-shadow: 0 8px 20px rgba(15, 23, 42, 0.06);
}

.folder-picker__item--draft {
  cursor: default;
  background: var(--el-fill-color-extra-light);
  border-style: dashed;
}

.folder-picker__item--draft:hover {
  transform: none;
  box-shadow: none;
  border-color: var(--el-color-primary-light-5);
}

.folder-picker__item-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  color: var(--el-color-primary);
  flex-shrink: 0;
}

.folder-picker__item-main {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.folder-picker__item-input {
  max-width: 320px;
}

.folder-picker__item-name {
  color: var(--el-text-color-primary);
  font-size: 14px;
  font-weight: 600;
  line-height: 1.4;
}

.folder-picker__item-meta {
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

.breadcrumb-button {
  padding: 0;
  border: none;
  background: transparent;
  color: var(--el-color-primary);
  cursor: pointer;
  font-size: 13px;
}

.breadcrumb-button:hover {
  text-decoration: underline;
}
</style>

