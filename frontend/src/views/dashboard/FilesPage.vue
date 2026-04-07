<script setup lang="ts">
import { computed, onMounted, ref, type Component } from 'vue'
import {
  ElButton,
  ElCard,
  ElEmpty,
  ElIcon,
  ElMessage,
  ElPopconfirm,
  ElSkeleton,
  ElSpace,
  ElTag,
  ElText,
  ElUpload,
  type UploadRequestOptions,
} from 'element-plus'
import { Document, Files, FolderOpened, Picture, UploadFilled } from '@element-plus/icons-vue'
import SegmentedSwitch from '../../components/SegmentedSwitch.vue'
import { deleteFile as requestDeleteFile, fetchFiles as requestFiles, uploadFile } from '../../features/files/api'
import type { FileItem } from '../../features/files/types'
import { getApiErrorMessage } from '../../utils/api'

type 文件夹键 = 'all' | 'image' | 'document' | 'archive' | 'other'
type 上传请求错误 = Error & {
  status: number
  method: string
  url: string
}

interface 文件夹定义 {
  key: 文件夹键
  label: string
  description: string
  emptyDescription: string
  icon: Component
}

interface 文件夹概览项 extends 文件夹定义 {
  count: number
}

interface 文件夹预览区块 extends 文件夹概览项 {
  files: FileItem[]
  hasMore: boolean
}

const 根目录预览上限 = 6
const 文件列表 = ref<FileItem[]>([])
const 加载中 = ref(true)
const 当前文件夹 = ref<文件夹键>('all')

const 文件夹定义列表: readonly 文件夹定义[] = [
  {
    key: 'all',
    label: '全部文件',
    description: '显示当前账号下的全部普通文件',
    emptyDescription: '暂无文件',
    icon: FolderOpened,
  },
  {
    key: 'image',
    label: '图片',
    description: '图片预览与截图类资源',
    emptyDescription: '图片区暂无文件',
    icon: Picture,
  },
  {
    key: 'document',
    label: '文稿',
    description: 'Markdown、文本与 PDF 文档',
    emptyDescription: '文稿区暂无文件',
    icon: Document,
  },
  {
    key: 'archive',
    label: '压缩包',
    description: 'ZIP 等归档文件',
    emptyDescription: '压缩包区暂无文件',
    icon: Files,
  },
  {
    key: 'other',
    label: '其他',
    description: '暂未归类的普通文件',
    emptyDescription: '其他分组暂无文件',
    icon: Files,
  },
] as const

const 文件夹选项 = 文件夹定义列表.map((item) => ({
  label: item.label,
  value: item.key,
  icon: item.icon,
}))

const 当前文件夹定义 = computed(() => (
  文件夹定义列表.find((item) => item.key === 当前文件夹.value) ?? 文件夹定义列表[0]
))

const 文件夹概览列表 = computed<文件夹概览项[]>(() => 文件夹定义列表.map((item) => ({
  ...item,
  count: item.key === 'all'
    ? 文件列表.value.length
    : 文件列表.value.filter((file) => 解析文件夹(file) === item.key).length,
})))

const 当前文件夹文件 = computed(() => {
  if (当前文件夹.value === 'all') {
    return 文件列表.value
  }
  return 文件列表.value.filter((file) => 解析文件夹(file) === 当前文件夹.value)
})

const 根目录预览区块 = computed<文件夹预览区块[]>(() => 文件夹概览列表.value
  .filter((item) => item.key !== 'all' && item.count > 0)
  .map((item) => {
    const matchedFiles = 文件列表.value.filter((file) => 解析文件夹(file) === item.key)
    return {
      ...item,
      files: matchedFiles.slice(0, 根目录预览上限),
      hasMore: matchedFiles.length > 根目录预览上限,
    }
  }))

onMounted(async () => {
  await 拉取文件列表()
})

async function 拉取文件列表() {
  加载中.value = true
  try {
    文件列表.value = await requestFiles()
    if (当前文件夹.value !== 'all' && 当前文件夹文件.value.length === 0) {
      当前文件夹.value = 'all'
    }
  } finally {
    加载中.value = false
  }
}

async function 处理上传(opt: UploadRequestOptions) {
  try {
    await uploadFile(opt.file)
    ElMessage.success('上传成功')
    await 拉取文件列表()
    opt.onSuccess({})
  } catch (error) {
    const uploadError = 转换上传错误(error)
    ElMessage.error(uploadError.message)
    opt.onError(uploadError)
  }
}

function 转换上传错误(error: unknown): 上传请求错误 {
  const message = getApiErrorMessage(error, '上传失败')
  const uploadError = error instanceof Error ? (error as 上传请求错误) : (new Error(message) as 上传请求错误)
  uploadError.message = message
  uploadError.status ??= 0
  uploadError.method ??= 'POST'
  uploadError.url ??= '/files'
  return uploadError
}

async function 删除文件(id: string) {
  await requestDeleteFile(id)
  文件列表.value = 文件列表.value.filter((file) => file.id !== id)
  if (当前文件夹.value !== 'all' && 当前文件夹文件.value.length === 0) {
    当前文件夹.value = 'all'
  }
  ElMessage.success('已删除')
}

function 选择文件夹(folderKey: 文件夹键) {
  当前文件夹.value = folderKey
}

function 返回全部文件() {
  当前文件夹.value = 'all'
}

function 格式化大小(bytes: number) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1048576).toFixed(1) + ' MB'
}

function 提取扩展名(filename: string) {
  const extension = filename.split('.').pop()?.trim().toLowerCase()
  return extension || ''
}

function 解析文件夹(file: FileItem): Exclude<文件夹键, 'all'> {
  const extension = 提取扩展名(file.original_name)
  if (file.mime_type.startsWith('image/')) {
    return 'image'
  }
  if (
    file.mime_type === 'application/pdf'
    || file.mime_type === 'text/plain'
    || file.mime_type === 'text/markdown'
    || extension === 'pdf'
    || extension === 'txt'
    || extension === 'md'
  ) {
    return 'document'
  }
  if (
    file.mime_type === 'application/zip'
    || ['zip', '7z', 'rar', 'tar', 'gz'].includes(extension)
  ) {
    return 'archive'
  }
  return 'other'
}

function 是否图片(file: FileItem) {
  return 解析文件夹(file) === 'image'
}

function 获取卡片标签(file: FileItem) {
  const extension = 提取扩展名(file.original_name)
  if (extension) {
    return extension.toUpperCase()
  }
  if (file.mime_type.startsWith('image/')) {
    return 'IMG'
  }
  return 'FILE'
}

function 获取目录文案(file: FileItem) {
  try {
    const url = new window.URL(file.url, window.location.origin)
    const relativePath = decodeURIComponent(url.pathname.replace(/^\/files\//, ''))
    const segments = relativePath.split('/').filter(Boolean)
    if (segments.length <= 1) {
      return '根目录'
    }
    return segments.slice(0, -1).join(' / ')
  } catch {
    return '根目录'
  }
}

async function 复制链接(url: string) {
  try {
    const resolvedUrl = /^https?:\/\//.test(url) ? url : new window.URL(url, window.location.origin).href
    await navigator.clipboard.writeText(resolvedUrl)
    ElMessage.success('链接已复制')
  } catch {
    ElMessage.error('复制失败，请检查浏览器权限')
  }
}
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <div>
        <h2 class="page-title">
          <ElIcon><FolderOpened /></ElIcon>
          <span>文件管理</span>
        </h2>
        <p class="page-subtitle">
          按分类文件夹整理普通文件，文章图片不会出现在这里。
        </p>
      </div>
      <div class="page-actions">
        <ElUpload
          :http-request="处理上传"
          :show-file-list="false"
          accept="image/*,.pdf,.zip,.md,.txt"
        >
          <ElButton type="primary">
            <ElIcon style="margin-right: 6px"><UploadFilled /></ElIcon>
            <span>上传文件</span>
          </ElButton>
        </ElUpload>
      </div>
    </div>

    <ElSkeleton :loading="加载中" animated>
      <div v-if="文件列表.length === 0 && !加载中" class="empty-state">
        <ElEmpty description="暂无文件" />
      </div>

      <template v-else>
        <div class="folder-toolbar">
          <SegmentedSwitch
            v-model="当前文件夹"
            aria-label="文件夹切换"
            :options="文件夹选项"
            active-color="#18a058"
            size="small"
          />
          <ElText type="info" class="folder-toolbar__count">
            当前显示 {{ 当前文件夹文件.length }} 个文件
          </ElText>
        </div>

        <div class="folder-summary-grid">
          <button
            v-for="folder in 文件夹概览列表"
            :key="folder.key"
            type="button"
            class="folder-summary-card"
            :class="{ 'is-active': 当前文件夹 === folder.key }"
            @click="选择文件夹(folder.key)"
          >
            <div class="folder-summary-card__icon">
              <ElIcon><component :is="folder.icon" /></ElIcon>
            </div>
            <div class="folder-summary-card__body">
              <span class="folder-summary-card__title">{{ folder.label }}</span>
              <span class="folder-summary-card__meta">{{ folder.count }} 个文件</span>
            </div>
          </button>
        </div>

        <ElCard class="folder-panel" shadow="never">
          <div v-if="当前文件夹 === 'all'" class="folder-panel__header">
            <div>
              <h3 class="folder-panel__title">全部文件</h3>
              <p class="folder-panel__description">按分组预览当前账号下的普通文件资源</p>
            </div>
            <ElTag effect="plain">{{ 文件列表.length }} 个文件</ElTag>
          </div>

          <div v-if="当前文件夹 === 'all' && 根目录预览区块.length === 0" class="empty-state empty-state--inner">
            <ElEmpty description="暂无可预览的文件" />
          </div>

          <div v-else-if="当前文件夹 === 'all'" class="folder-section-list">
            <section
              v-for="section in 根目录预览区块"
              :key="section.key"
              class="folder-section"
            >
              <div class="folder-section__header">
                <div class="folder-section__title-wrap">
                  <div class="folder-section__icon">
                    <ElIcon><component :is="section.icon" /></ElIcon>
                  </div>
                  <div>
                    <h3 class="folder-section__title">{{ section.label }}</h3>
                    <p class="folder-section__description">
                      {{ section.description }} · {{ section.count }} 个文件
                    </p>
                  </div>
                </div>
                <ElButton text type="primary" @click="选择文件夹(section.key)">
                  查看全部
                </ElButton>
              </div>

              <div class="file-grid">
                <ElCard v-for="file in section.files" :key="file.id" class="file-card" shadow="hover">
                  <div v-if="是否图片(file)" class="file-preview">
                    <img :src="file.url" :alt="file.original_name">
                  </div>
                  <div v-else class="file-icon">
                    <ElIcon><component :is="section.icon" /></ElIcon>
                  </div>

                  <div class="file-info">
                    <div class="file-info__meta">
                      <ElTag size="small" effect="plain">{{ 获取卡片标签(file) }}</ElTag>
                      <ElText type="info" class="file-info__path">{{ 获取目录文案(file) }}</ElText>
                    </div>
                    <ElText tag="b" class="file-info__name">{{ file.original_name }}</ElText>
                    <ElText type="info" class="file-info__desc">
                      {{ 格式化大小(file.size) }} · {{ new Date(file.created_at).toLocaleDateString() }}
                    </ElText>
                  </div>

                  <ElSpace size="small" class="file-actions">
                    <ElButton size="small" @click="复制链接(file.url)">复制链接</ElButton>
                    <ElPopconfirm @confirm="删除文件(file.id)">
                      <template #reference><ElButton size="small" type="danger" text>删除</ElButton></template>
                      确定删除此文件？
                    </ElPopconfirm>
                  </ElSpace>
                </ElCard>
              </div>

              <div v-if="section.hasMore" class="folder-section__footer">
                <ElButton text type="primary" @click="选择文件夹(section.key)">
                  该分组还有更多文件，继续查看
                </ElButton>
              </div>
            </section>
          </div>

          <template v-else>
            <div class="folder-panel__header">
              <div>
                <div class="folder-detail__breadcrumb">
                  <button type="button" class="folder-detail__back" @click="返回全部文件">
                    全部文件
                  </button>
                  <span>/</span>
                  <span>{{ 当前文件夹定义.label }}</span>
                </div>
                <h3 class="folder-panel__title">{{ 当前文件夹定义.label }}</h3>
                <p class="folder-panel__description">{{ 当前文件夹定义.description }}</p>
              </div>
              <ElTag effect="plain">{{ 当前文件夹文件.length }} 个文件</ElTag>
            </div>

            <div v-if="当前文件夹文件.length === 0" class="empty-state empty-state--inner">
              <ElEmpty :description="当前文件夹定义.emptyDescription" />
            </div>

            <div v-else class="file-grid">
              <ElCard v-for="file in 当前文件夹文件" :key="file.id" class="file-card" shadow="hover">
                <div v-if="是否图片(file)" class="file-preview">
                  <img :src="file.url" :alt="file.original_name">
                </div>
                <div v-else class="file-icon">
                  <ElIcon><component :is="当前文件夹定义.icon" /></ElIcon>
                </div>

                <div class="file-info">
                  <div class="file-info__meta">
                    <ElTag size="small" effect="plain">{{ 获取卡片标签(file) }}</ElTag>
                    <ElText type="info" class="file-info__path">{{ 获取目录文案(file) }}</ElText>
                  </div>
                  <ElText tag="b" class="file-info__name">{{ file.original_name }}</ElText>
                  <ElText type="info" class="file-info__desc">
                    {{ 格式化大小(file.size) }} · {{ new Date(file.created_at).toLocaleString() }}
                  </ElText>
                </div>

                <ElSpace size="small" class="file-actions">
                  <ElButton size="small" @click="复制链接(file.url)">复制链接</ElButton>
                  <ElPopconfirm @confirm="删除文件(file.id)">
                    <template #reference><ElButton size="small" type="danger" text>删除</ElButton></template>
                    确定删除此文件？
                  </ElPopconfirm>
                </ElSpace>
              </ElCard>
            </div>
          </template>
        </ElCard>
      </template>
    </ElSkeleton>
  </div>
</template>

<style scoped>
.page-container {
  height: 100%;
  overflow-y: auto;
  padding: 24px;
  box-sizing: border-box;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 24px;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
}

.page-subtitle {
  margin: 8px 0 0;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.page-actions {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.folder-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.folder-toolbar__count {
  font-size: 13px;
}

.folder-summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
  margin-bottom: 20px;
}

.folder-summary-card {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 14px 16px;
  border: 1px solid var(--el-border-color);
  border-radius: 12px;
  background: var(--el-fill-color-blank);
  text-align: left;
  cursor: pointer;
  transition: border-color 0.2s ease, background-color 0.2s ease;
}

.folder-summary-card:hover {
  border-color: rgba(24, 160, 88, 0.28);
}

.folder-summary-card.is-active {
  border-color: #18a058;
  background: rgba(24, 160, 88, 0.08);
}

.folder-summary-card__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: rgba(24, 160, 88, 0.1);
  color: #18a058;
  font-size: 18px;
  flex-shrink: 0;
}

.folder-summary-card__body {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.folder-summary-card__title {
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.folder-summary-card__meta {
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

.folder-panel {
  border-radius: 14px;
}

.folder-panel :deep(.el-card__body) {
  padding: 20px;
}

.folder-panel__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

.folder-panel__title {
  margin: 0;
  font-size: 18px;
  color: var(--el-text-color-primary);
}

.folder-panel__description {
  margin: 6px 0 0;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.folder-section-list {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.folder-section {
  padding: 18px 0;
}

.folder-section + .folder-section {
  border-top: 1px solid var(--el-border-color-lighter);
}

.folder-section__header,
.folder-panel__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 14px;
}

.folder-section__title-wrap {
  display: flex;
  align-items: center;
  gap: 12px;
}

.folder-section__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: var(--el-fill-color-light);
  color: #18a058;
  font-size: 17px;
}

.folder-section__title,
.folder-panel__title {
  margin: 0;
  font-size: 16px;
  color: var(--el-text-color-primary);
}

.folder-section__description,
.folder-panel__description {
  margin: 6px 0 0;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.folder-section__footer {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}

.folder-detail__breadcrumb {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.folder-detail__back {
  padding: 0;
  border: none;
  background: none;
  color: #18a058;
  cursor: pointer;
}

.empty-state {
  min-height: 240px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty-state--inner {
  min-height: 200px;
}

.file-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 12px;
}

.file-card {
  border-radius: 12px;
}

.file-preview,
.file-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 128px;
  margin-bottom: 12px;
  border-radius: 10px;
  background: var(--el-fill-color-light);
  overflow: hidden;
}

.file-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.file-icon {
  color: #18a058;
  font-size: 42px;
}

.file-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.file-info__meta {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.file-info__path {
  min-width: 0;
  font-size: 11px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-info__name {
  font-size: 13px;
  line-height: 1.5;
  word-break: break-all;
}

.file-info__desc {
  font-size: 12px;
}

.file-actions {
  margin-top: 10px;
  flex-wrap: wrap;
}

.file-actions :deep(.el-space__item) {
  display: inline-flex;
}

:global(.dark .folder-summary-card) {
  background: var(--bg-secondary);
  border-color: var(--border-color);
}

:global(.dark .folder-summary-card.is-active) {
  background: rgba(24, 160, 88, 0.14);
}

:global(.dark .folder-panel) {
  background: var(--bg-secondary);
  border-color: var(--border-color);
}

:global(.dark .file-preview),
:global(.dark .file-icon) {
  background: var(--bg-hover);
}

@media (max-width: 768px) {
  .page-container {
    padding: 16px;
  }

  .page-header,
  .folder-section__header,
  .folder-panel__header {
    flex-direction: column;
    align-items: stretch;
  }

  .page-actions {
    width: 100%;
  }

  .page-actions :deep(.el-upload),
  .page-actions :deep(.el-upload .el-button) {
    width: 100%;
  }

  .folder-panel :deep(.el-card__body) {
    padding: 16px;
  }

  .folder-summary-grid {
    grid-template-columns: 1fr;
  }
}
</style>
