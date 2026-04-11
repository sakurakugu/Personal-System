<script setup lang="ts">
/* global Event, HTMLInputElement */
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  ElButton,
  ElCard,
  ElEmpty,
  ElForm,
  ElFormItem,
  ElIcon,
  ElInput,
  ElMessage,
  ElOption,
  ElPagination,
  ElPopconfirm,
  ElSelect,
  ElSpace,
  ElTable,
  ElTableColumn,
  ElTag,
} from 'element-plus'
import { Collection, Upload, Van } from '@element-plus/icons-vue'
import BaseDialog from '../../components/BaseDialog.vue'
import {
  batchUpdateCollectionStatus,
  convertCollectionToArticle,
  convertCollectionToMomentDraft,
  convertCollectionToTodo,
  createCollection,
  deleteCollection,
  fetchCollectionTags,
  fetchCollections,
  updateCollection,
} from '../../features/collections/api'
import type {
  CollectionAssetPayload,
  CollectionAssetRecord,
  CollectionPayload,
  CollectionRecord,
  CollectionStatus,
  CollectionTagStat,
  CollectionType,
} from '../../features/collections/types'
import { uploadFile } from '../../features/files/api'
import { getApiErrorMessage } from '../../utils/api'

interface CollectionFormState {
  type: CollectionType
  title: string
  content_text: string
  note: string
  status: CollectionStatus
  tags_text: string
  assets: Array<{
    file_id: string
    sort_order: number
    file: CollectionAssetRecord['file']
  }>
}

const router = useRouter()
const uploadInputRef = ref<HTMLInputElement | null>(null)
const initialLoading = ref(true)
const tableLoading = ref(false)
const dialogLoading = ref(false)
const uploadLoading = ref(false)
const showDialog = ref(false)
const isEdit = ref(false)
const currentId = ref('')
const collections = ref<CollectionRecord[]>([])
const selectedCollections = ref<CollectionRecord[]>([])
const tagOptions = ref<CollectionTagStat[]>([])
const pagination = ref({ page: 1, pageSize: 12, total: 0, pageCount: 0 })
const filters = ref({
  keyword: '',
  status: '' as CollectionStatus | '',
  type: '' as CollectionType | '',
  tag: '',
})

function createEmptyForm(): CollectionFormState {
  return {
    type: 'link',
    title: '',
    content_text: '',
    note: '',
    status: 'inbox',
    tags_text: '',
    assets: [],
  }
}

const form = ref<CollectionFormState>(createEmptyForm())

const typeOptions: Array<{ label: string, value: CollectionType }> = [
  { label: '网页链接', value: 'link' },
  { label: '文本', value: 'text' },
  { label: '图片', value: 'image' },
  { label: '文件', value: 'file' },
]
const statusOptions: Array<{ label: string, value: CollectionStatus }> = [
  { label: '收件箱', value: 'inbox' },
  { label: '整理中', value: 'processing' },
  { label: '已就绪', value: 'ready' },
  { label: '已归档', value: 'archived' },
  { label: '已废弃', value: 'dropped' },
]
const hasSelection = computed(() => selectedCollections.value.length > 0)
const selectionIds = computed(() => selectedCollections.value.map(item => item.id))

function parseTagsText(tagsText: string): string[] | null {
  const tags = tagsText
    .replaceAll('，', ',')
    .split(',')
    .map(tag => tag.trim())
    .filter(Boolean)
  return tags.length > 0 ? Array.from(new Set(tags)) : null
}

function buildPayloadFromForm(): CollectionPayload {
  const assets: CollectionAssetPayload[] | null = form.value.assets.length > 0
    ? form.value.assets.map((asset, index) => ({
      file_id: asset.file_id,
      sort_order: index,
    }))
    : null

  return {
    type: form.value.type,
    title: form.value.title || null,
    content_text: form.value.content_text || null,
    note: form.value.note || null,
    status: form.value.status,
    tags: parseTagsText(form.value.tags_text),
    assets,
  }
}

function getTypeLabel(value: CollectionType): string {
  return typeOptions.find(item => item.value === value)?.label ?? value
}

function getStatusLabel(value: CollectionStatus): string {
  return statusOptions.find(item => item.value === value)?.label ?? value
}

function getStatusTagType(value: CollectionStatus): 'info' | 'warning' | 'success' | 'danger' {
  if (value === 'ready') return 'success'
  if (value === 'processing') return 'warning'
  if (value === 'dropped') return 'danger'
  return 'info'
}

function getPreviewText(record: CollectionRecord): string {
  return record.note || record.content_text || '暂无内容'
}

async function loadCollections(page = pagination.value.page) {
  tableLoading.value = true
  try {
    const data = await fetchCollections({
      page,
      page_size: pagination.value.pageSize,
      keyword: filters.value.keyword.trim() || undefined,
      status: filters.value.status,
      type: filters.value.type,
      tag: filters.value.tag.trim() || undefined,
    })
    collections.value = data.items
    pagination.value = {
      page: data.page,
      pageSize: data.page_size,
      total: data.total,
      pageCount: data.pages,
    }
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '加载收藏失败'))
  } finally {
    tableLoading.value = false
    initialLoading.value = false
  }
}

async function loadTags() {
  try {
    tagOptions.value = await fetchCollectionTags()
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '加载标签失败'))
  }
}

function openCreateDialog() {
  isEdit.value = false
  currentId.value = ''
  form.value = createEmptyForm()
  showDialog.value = true
}

function openEditDialog(record: CollectionRecord) {
  isEdit.value = true
  currentId.value = record.id
  form.value = {
    type: record.type,
    title: record.title || '',
    content_text: record.content_text || '',
    note: record.note || '',
    status: record.status,
    tags_text: (record.tags || []).join(', '),
    assets: record.assets.map(asset => ({
      file_id: asset.file_id,
      sort_order: asset.sort_order,
      file: asset.file,
    })),
  }
  showDialog.value = true
}

async function saveCollection() {
  dialogLoading.value = true
  try {
    const payload = buildPayloadFromForm()
    if (isEdit.value) {
      await updateCollection(currentId.value, payload)
      ElMessage.success('收藏已更新')
    } else {
      await createCollection(payload)
      ElMessage.success('收藏已创建')
    }
    showDialog.value = false
    await Promise.all([loadCollections(isEdit.value ? pagination.value.page : 1), loadTags()])
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '保存收藏失败'))
  } finally {
    dialogLoading.value = false
  }
}

async function removeCollection(id: string) {
  try {
    await deleteCollection(id)
    ElMessage.success('收藏已删除')
    await Promise.all([loadCollections(), loadTags()])
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '删除收藏失败'))
  }
}

async function archiveCollection(record: CollectionRecord) {
  try {
    await updateCollection(record.id, { status: 'archived' })
    ElMessage.success('已归档')
    await loadCollections()
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '归档失败'))
  }
}

async function archiveSelectedCollections() {
  if (!hasSelection.value) return
  try {
    await batchUpdateCollectionStatus({ ids: selectionIds.value, status: 'archived' })
    ElMessage.success(`已归档 ${selectionIds.value.length} 条收藏`)
    selectedCollections.value = []
    await loadCollections()
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '批量归档失败'))
  }
}

async function handleConvertToArticle(record: CollectionRecord) {
  try {
    const result = await convertCollectionToArticle(record.id)
    ElMessage.success(result.message)
    await router.push(`/dashboard/articles/edit/${result.target_id}`)
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '转文章失败'))
  }
}

async function handleConvertToMoment(record: CollectionRecord) {
  try {
    const result = await convertCollectionToMomentDraft(record.id)
    ElMessage.success(result.message)
    await router.push('/dashboard/moments')
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '转动态草稿失败'))
  }
}

async function handleConvertToTodo(record: CollectionRecord) {
  try {
    const result = await convertCollectionToTodo(record.id)
    ElMessage.success(result.message)
    await router.push('/dashboard/todos')
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '转待办失败'))
  }
}

function openUploadPicker() {
  uploadInputRef.value?.click()
}

async function handleUploadChange(event: Event) {
  const input = event.target as HTMLInputElement
  const files = Array.from(input.files || [])
  if (files.length === 0) {
    return
  }

  uploadLoading.value = true
  try {
    for (const file of files) {
      const uploaded = await uploadFile(file)
      form.value.assets.push({
        file_id: uploaded.id,
        sort_order: form.value.assets.length,
        file: uploaded,
      })
    }
    ElMessage.success(`已上传 ${files.length} 个附件`)
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '上传附件失败'))
  } finally {
    uploadLoading.value = false
    input.value = ''
  }
}

function removeAsset(index: number) {
  form.value.assets.splice(index, 1)
}

function moveAsset(index: number, direction: -1 | 1) {
  const targetIndex = index + direction
  if (targetIndex < 0 || targetIndex >= form.value.assets.length) {
    return
  }
  const [item] = form.value.assets.splice(index, 1)
  form.value.assets.splice(targetIndex, 0, item)
}

function handleSelectionChange(value: CollectionRecord[]) {
  selectedCollections.value = value
}

onMounted(async () => {
  await Promise.all([loadCollections(1), loadTags()])
})
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">
        <ElIcon><Collection /></ElIcon>
        <span>收藏收纳库</span>
      </h2>
      <ElSpace wrap>
        <ElButton plain :disabled="!hasSelection" @click="archiveSelectedCollections">
          <ElIcon><Van /></ElIcon>
          <span>批量归档</span>
        </ElButton>
        <ElButton type="primary" @click="openCreateDialog">+ 新增收藏</ElButton>
      </ElSpace>
    </div>

    <ElCard class="filter-card">
      <div class="filters">
        <ElInput
          v-model="filters.keyword"
          class="filter-input"
          clearable
          placeholder="搜索标题、正文、备注"
          @keyup.enter="loadCollections(1)"
        />
        <ElSelect v-model="filters.status" clearable placeholder="状态" class="filter-select" @change="loadCollections(1)">
          <ElOption label="全部状态" value="" />
          <ElOption v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
        </ElSelect>
        <ElSelect v-model="filters.type" clearable placeholder="类型" class="filter-select" @change="loadCollections(1)">
          <ElOption label="全部类型" value="" />
          <ElOption v-for="item in typeOptions" :key="item.value" :label="item.label" :value="item.value" />
        </ElSelect>
        <ElSelect v-model="filters.tag" clearable placeholder="标签" class="filter-select" @change="loadCollections(1)">
          <ElOption label="全部标签" value="" />
          <ElOption v-for="item in tagOptions" :key="item.name" :label="`${item.name} (${item.count})`" :value="item.name" />
        </ElSelect>
        <ElButton type="primary" @click="loadCollections(1)">筛选</ElButton>
      </div>
    </ElCard>

    <div v-loading="tableLoading" class="table-wrap">
      <ElTable
        v-if="collections.length > 0"
        :data="collections"
        border
        stripe
        height="100%"
        @selection-change="handleSelectionChange"
      >
        <ElTableColumn type="selection" width="50" />
        <ElTableColumn label="标题 / 内容" min-width="280">
          <template #default="{ row }">
            <div class="record-main">
              <div class="record-title">{{ row.title || '未命名收藏' }}</div>
              <div class="record-preview">{{ getPreviewText(row) }}</div>
            </div>
          </template>
        </ElTableColumn>
        <ElTableColumn label="分类" width="220">
          <template #default="{ row }">
            <ElSpace wrap size="small">
              <ElTag size="small">{{ getTypeLabel(row.type) }}</ElTag>
              <ElTag :type="getStatusTagType(row.status)" size="small">{{ getStatusLabel(row.status) }}</ElTag>
            </ElSpace>
          </template>
        </ElTableColumn>
        <ElTableColumn label="标签" min-width="180">
          <template #default="{ row }">
            <ElSpace v-if="row.tags?.length" wrap size="small">
              <ElTag v-for="tag in row.tags" :key="tag" size="small" type="info" effect="plain">{{ tag }}</ElTag>
            </ElSpace>
            <span v-else class="muted-text">无标签</span>
          </template>
        </ElTableColumn>
        <ElTableColumn label="附件" width="86">
          <template #default="{ row }">
            <span>{{ row.assets.length }}</span>
          </template>
        </ElTableColumn>
        <ElTableColumn label="更新时间" width="170">
          <template #default="{ row }">
            {{ new Date(row.updated_at).toLocaleString() }}
          </template>
        </ElTableColumn>
        <ElTableColumn label="操作" width="330" fixed="right">
          <template #default="{ row }">
            <ElSpace wrap size="small">
              <ElButton size="small" @click="openEditDialog(row)">编辑</ElButton>
              <ElButton size="small" @click="handleConvertToArticle(row)">转文章</ElButton>
              <ElButton size="small" @click="handleConvertToMoment(row)">转动态</ElButton>
              <ElButton size="small" @click="handleConvertToTodo(row)">转待办</ElButton>
              <ElButton size="small" plain @click="archiveCollection(row)">归档</ElButton>
              <ElPopconfirm @confirm="removeCollection(row.id)">
                <template #reference>
                  <ElButton size="small" type="danger" text>删除</ElButton>
                </template>
                确定删除这条收藏？
              </ElPopconfirm>
            </ElSpace>
          </template>
        </ElTableColumn>
      </ElTable>

      <ElEmpty v-else-if="!initialLoading" description="还没有收藏内容" />
    </div>

    <div v-if="pagination.pageCount > 1" class="pagination-wrap">
      <ElPagination
        :current-page="pagination.page"
        :page-count="pagination.pageCount"
        layout="prev, pager, next"
        @update:current-page="loadCollections"
      />
    </div>

    <BaseDialog
      v-model="showDialog"
      :title="isEdit ? '编辑收藏' : '新增收藏'"
      width="760px"
      style="max-width: 96vw"
    >
      <ElForm label-position="top">
        <div class="dialog-grid">
          <ElFormItem label="类型">
            <ElSelect v-model="form.type">
              <ElOption v-for="item in typeOptions" :key="item.value" :label="item.label" :value="item.value" />
            </ElSelect>
          </ElFormItem>
          <ElFormItem label="状态">
            <ElSelect v-model="form.status">
              <ElOption v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
            </ElSelect>
          </ElFormItem>
        </div>

        <ElFormItem label="标题">
          <ElInput v-model="form.title" placeholder="收藏标题，可留空" maxlength="300" />
        </ElFormItem>
        <ElFormItem label="正文提取">
          <ElInput v-model="form.content_text" type="textarea" :rows="5" placeholder="网页正文或手动粘贴内容" />
        </ElFormItem>
        <ElFormItem label="备注">
          <ElInput v-model="form.note" type="textarea" :rows="4" placeholder="补充备注、整理思路、后续动作" />
        </ElFormItem>
        <ElFormItem label="标签">
          <ElInput v-model="form.tags_text" placeholder="多个标签请用逗号分隔" />
        </ElFormItem>

        <ElFormItem label="附件">
          <div class="asset-panel">
            <div class="asset-toolbar">
              <ElButton :loading="uploadLoading" @click="openUploadPicker">
                <ElIcon><Upload /></ElIcon>
                <span>上传附件</span>
              </ElButton>
              <span class="muted-text">图片或文件会先进入文件库，再挂到当前收藏</span>
              <input
                ref="uploadInputRef"
                class="hidden-upload"
                type="file"
                multiple
                @change="handleUploadChange"
              >
            </div>

            <div v-if="form.assets.length === 0" class="asset-empty">
              暂无附件
            </div>

            <div v-else class="asset-list">
              <div v-for="(asset, index) in form.assets" :key="asset.file_id" class="asset-item">
                <div class="asset-info">
                  <a :href="asset.file.url" target="_blank" class="asset-name">
                    {{ asset.file.original_name }}
                  </a>
                  <div class="asset-meta">
                    {{ asset.file.mime_type }} · {{ Math.max(1, Math.round(asset.file.size / 1024)) }} KB
                  </div>
                </div>
                <div class="asset-actions">
                  <ElButton text :disabled="index === 0" @click="moveAsset(index, -1)">上移</ElButton>
                  <ElButton text :disabled="index === form.assets.length - 1" @click="moveAsset(index, 1)">下移</ElButton>
                  <ElButton text type="danger" @click="removeAsset(index)">移除</ElButton>
                </div>
              </div>
            </div>
          </div>
        </ElFormItem>
      </ElForm>

      <template #footer>
        <ElButton @click="showDialog = false">取消</ElButton>
        <ElButton type="primary" :loading="dialogLoading" @click="saveCollection">
          {{ isEdit ? '保存修改' : '创建收藏' }}
        </ElButton>
      </template>
    </BaseDialog>
  </div>
</template>

<style scoped>
@import '../../styles/media.css';

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
  margin-bottom: 20px;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
}

.filter-card {
  margin-bottom: 16px;
}

.filters {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.filter-input {
  flex: 1 1 260px;
}

.filter-select {
  width: 140px;
}

.table-wrap {
  height: calc(100% - 170px);
  min-height: 420px;
}

.record-main {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.record-title {
  font-size: 14px;
  font-weight: 600;
}

.record-preview {
  color: var(--el-text-color-secondary);
  font-size: 12px;
  line-height: 1.6;
  display: -webkit-box;
  line-clamp: 2;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.muted-text {
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

.pagination-wrap {
  display: flex;
  justify-content: center;
  margin-top: 16px;
}

.dialog-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.asset-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.asset-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
}

.asset-empty {
  padding: 16px;
  border: 1px dashed var(--el-border-color);
  border-radius: 10px;
  color: var(--el-text-color-secondary);
}

.asset-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.asset-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  border: 1px solid var(--el-border-color);
  border-radius: 10px;
  background: var(--el-fill-color-extra-light);
}

.asset-info {
  min-width: 0;
}

.asset-name {
  color: var(--el-color-primary);
  text-decoration: none;
}

.asset-meta {
  margin-top: 4px;
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

.asset-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
}

.hidden-upload {
  display: none;
}

@media (--mobile-viewport) {
  .page-container {
    padding: 16px;
  }

  .page-header {
    flex-direction: column;
    align-items: stretch;
  }

  .dialog-grid {
    grid-template-columns: 1fr;
  }

  .filter-select {
    width: 100%;
  }

  .table-wrap {
    height: auto;
    min-height: 360px;
  }

  .asset-item {
    flex-direction: column;
    align-items: stretch;
  }

  .asset-actions {
    justify-content: flex-start;
  }
}
</style>
