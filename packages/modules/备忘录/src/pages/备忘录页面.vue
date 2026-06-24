<script setup lang="ts">
/* global Event, KeyboardEvent */
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ElButton,
  ElEmpty,
  ElForm,
  ElFormItem,
  ElIcon,
  ElInput,
  ElMessage,
  ElMessageBox,
  ElOption,
  ElPopover,
  ElSelect,
  ElTag,
} from 'element-plus'
import {
  ArrowLeft,
  Collection,
  Delete,
  Document,
  EditPen,
  Finished,
  FolderChecked,
  MoreFilled,
  RefreshRight,
  Search,
  Select,
  Tickets,
} from '@element-plus/icons-vue'
import { BaseDialog, PageSectionShell, 使用路由搜索同步 } from '@personal-system/ui'
import { 获取API错误消息 } from '@personal-system/api'
import {
  创建备忘录,
  删除备忘录,
  恢复备忘录,
  更新备忘录,
  获取备忘录列表,
  转换备忘录为文章,
  转换备忘录为待办,
  转换备忘录为资料,
} from '../api'
import type { MemoListQuery, MemoListResponse, MemoRecord, MemoSource, MemoStatus } from '../types'

const props = withDefaults(defineProps<{
  showBack?: boolean
  backTo?: string
}>(), {
  showBack: false,
  backTo: '/',
})

type InputInstance = InstanceType<typeof ElInput>

const route = useRoute()
const router = useRouter()
const quickInputRef = ref<InputInstance | null>(null)
const editInputRef = ref<InputInstance | null>(null)
const loading = ref(false)
const saving = ref(false)
const convertingId = ref('')
const deletingId = ref('')
const showEditDialog = ref(false)
const showRecycleBin = ref(false)
const editingMemoId = ref('')
const quickContent = ref('')
const quickSource = ref<MemoSource>('manual')
const editContent = ref('')
const editSource = ref<MemoSource>('manual')
const editStatus = ref<MemoStatus>('inbox')
const memos = ref<MemoRecord[]>([])
const pagination = ref({ page: 1, pageSize: 20, total: 0, pageCount: 0 })
const filters = ref({
  keyword: '',
  status: 'inbox' as MemoStatus | '',
  source: '' as MemoSource | '',
})
const 路由搜索词 = computed({
  get: () => filters.value.keyword,
  set: (value: string) => {
    filters.value.keyword = value
  },
})
使用路由搜索同步(路由搜索词)

const 路由前缀 = computed(() => route.path.startsWith('/dashboard') ? '/dashboard' : '')
const 页面标题 = computed(() => showRecycleBin.value ? '备忘录回收站' : '备忘录')
const 有更多 = computed(() => pagination.value.page < pagination.value.pageCount)
const 有筛选 = computed(() => Boolean(filters.value.keyword.trim() || filters.value.status || filters.value.source))

const 状态选项: Array<{ label: string, value: MemoStatus }> = [
  { label: '待整理', value: 'inbox' },
  { label: '已处理', value: 'processed' },
  { label: '已归档', value: 'archived' },
  { label: '废弃', value: 'dropped' },
]

const 来源选项: Array<{ label: string, value: MemoSource }> = [
  { label: '手动输入', value: 'manual' },
  { label: '微信复制', value: 'wechat' },
  { label: '网页', value: 'web' },
  { label: '系统分享', value: 'share' },
  { label: '未知', value: 'unknown' },
]

function 获取状态文案(status: MemoStatus | ''): string {
  return 状态选项.find(item => item.value === status)?.label ?? status
}

function 获取来源文案(source: MemoSource | ''): string {
  return 来源选项.find(item => item.value === source)?.label ?? source
}

function 获取状态标签类型(status: MemoStatus): 'info' | 'warning' | 'success' | 'danger' {
  if (status === 'processed') return 'success'
  if (status === 'archived') return 'info'
  if (status === 'dropped') return 'danger'
  return 'warning'
}

function 获取转出文案(type: MemoRecord['converted_to_type']): string {
  if (type === 'material') return '资料库'
  if (type === 'article') return '文章'
  if (type === 'todo') return '待办'
  return ''
}

function 格式化时间(value: string | null): string {
  if (!value) return ''
  return new Date(value).toLocaleString()
}

function 提取预览标题(content: string): string {
  const firstLine = content.split(/\r?\n/).map(line => line.trim()).find(Boolean)
  return firstLine || '未命名备忘录'
}

function 构建查询(page: number, pageSize: number): MemoListQuery {
  return {
    page,
    page_size: pageSize,
    keyword: filters.value.keyword.trim() || undefined,
    status: filters.value.status,
    source: filters.value.source,
    is_deleted: showRecycleBin.value,
  }
}

function 应用列表响应(data: MemoListResponse, append: boolean) {
  memos.value = append ? [...memos.value, ...data.items] : data.items
  pagination.value = {
    page: data.page,
    pageSize: data.page_size,
    total: data.total,
    pageCount: data.pages,
  }
}

async function 加载备忘录(page = 1, append = false) {
  loading.value = true
  try {
    const data = await 获取备忘录列表(构建查询(page, pagination.value.pageSize))
    应用列表响应(data, append)
  } catch (error) {
    ElMessage.error(获取API错误消息(error, '加载备忘录失败'))
  } finally {
    loading.value = false
  }
}

async function 创建快速备忘录() {
  const content = quickContent.value.trim()
  if (!content) {
    ElMessage.warning('先写点内容再保存')
    return
  }

  saving.value = true
  try {
    await 创建备忘录({ content, source: quickSource.value })
    quickContent.value = ''
    ElMessage.success('备忘录已保存')
    await 加载备忘录(1)
    await nextTick()
    quickInputRef.value?.focus()
  } catch (error) {
    ElMessage.error(获取API错误消息(error, '保存备忘录失败'))
  } finally {
    saving.value = false
  }
}

function 处理快速输入按键(event: Event | KeyboardEvent) {
  if (event instanceof KeyboardEvent && event.ctrlKey && event.key === 'Enter') {
    event.preventDefault()
    void 创建快速备忘录()
  }
}

function 打开编辑弹窗(memo: MemoRecord) {
  editingMemoId.value = memo.id
  editContent.value = memo.content
  editSource.value = memo.source
  editStatus.value = memo.status
  showEditDialog.value = true
  void nextTick(() => editInputRef.value?.focus())
}

async function 保存编辑() {
  const content = editContent.value.trim()
  if (!content) {
    ElMessage.warning('备忘录内容不能为空')
    return
  }

  saving.value = true
  try {
    await 更新备忘录(editingMemoId.value, {
      content,
      source: editSource.value,
      status: editStatus.value,
    })
    showEditDialog.value = false
    ElMessage.success('备忘录已更新')
    await 加载备忘录(1)
  } catch (error) {
    ElMessage.error(获取API错误消息(error, '更新备忘录失败'))
  } finally {
    saving.value = false
  }
}

async function 更新状态(memo: MemoRecord, status: MemoStatus) {
  try {
    await 更新备忘录(memo.id, { status })
    ElMessage.success(status === 'archived' ? '备忘录已归档' : '备忘录状态已更新')
    await 加载备忘录(1)
  } catch (error) {
    ElMessage.error(获取API错误消息(error, '更新备忘录状态失败'))
  }
}

async function 删除当前备忘录(memo: MemoRecord) {
  const permanent = showRecycleBin.value
  try {
    await ElMessageBox.confirm(
      permanent ? '确定永久删除这条备忘录吗？此操作不可恢复。' : '确定将这条备忘录移至回收站吗？',
      permanent ? '永久删除备忘录' : '删除备忘录',
      {
        type: permanent ? 'error' : 'warning',
        confirmButtonText: permanent ? '永久删除' : '移至回收站',
        cancelButtonText: '取消',
      },
    )
  } catch {
    return
  }

  deletingId.value = memo.id
  try {
    await 删除备忘录(memo.id, permanent)
    ElMessage.success(permanent ? '备忘录已永久删除' : '备忘录已移至回收站')
    await 加载备忘录(1)
  } catch (error) {
    ElMessage.error(获取API错误消息(error, permanent ? '永久删除备忘录失败' : '删除备忘录失败'))
  } finally {
    deletingId.value = ''
  }
}

async function 恢复当前备忘录(memo: MemoRecord) {
  deletingId.value = memo.id
  try {
    await 恢复备忘录(memo.id)
    ElMessage.success('备忘录已恢复')
    await 加载备忘录(1)
  } catch (error) {
    ElMessage.error(获取API错误消息(error, '恢复备忘录失败'))
  } finally {
    deletingId.value = ''
  }
}

async function 执行转换(memo: MemoRecord, target: 'collection' | 'article' | 'todo') {
  convertingId.value = memo.id
  try {
    const result = target === 'collection'
      ? await 转换备忘录为资料(memo.id)
      : target === 'article'
        ? await 转换备忘录为文章(memo.id)
        : await 转换备忘录为待办(memo.id)
    ElMessage.success(result.message)
    await 加载备忘录(1)
    if (target === 'article') {
      await router.push(`${路由前缀.value}/articles/edit/${result.target_id}`)
    } else if (target === 'todo') {
      await router.push(`${路由前缀.value}/todos`)
    } else {
      await router.push(`${路由前缀.value}/materials`)
    }
  } catch (error) {
    ElMessage.error(获取API错误消息(error, '转换备忘录失败'))
  } finally {
    convertingId.value = ''
  }
}

function 重置筛选() {
  filters.value = {
    keyword: '',
    status: showRecycleBin.value ? '' : 'inbox',
    source: '',
  }
}

watch([showRecycleBin], () => {
  filters.value.status = showRecycleBin.value ? '' : 'inbox'
  void 加载备忘录(1)
})

watch(filters, () => {
  void 加载备忘录(1)
}, { deep: true })

onMounted(() => {
  void 加载备忘录(1)
  void nextTick(() => quickInputRef.value?.focus())
})
</script>

<template>
  <div class="memo-page">
    <PageSectionShell :title="页面标题">
      <template #prefix>
        <ElButton v-if="props.showBack" text class="back-button" @click="router.push(props.backTo)">
          <ElIcon><ArrowLeft /></ElIcon>
        </ElButton>
      </template>

      <template #actions>
        <ElButton :loading="loading" @click="加载备忘录(1)">
          <ElIcon><RefreshRight /></ElIcon>
          <span>刷新</span>
        </ElButton>
        <ElButton :type="showRecycleBin ? 'warning' : 'default'" @click="showRecycleBin = !showRecycleBin">
          <ElIcon><Delete /></ElIcon>
          <span>{{ showRecycleBin ? '返回列表' : '回收站' }}</span>
        </ElButton>
      </template>

      <div v-if="!showRecycleBin" class="quick-input-panel">
        <div class="quick-input-toolbar">
          <ElSelect v-model="quickSource" class="source-select" size="small">
            <ElOption v-for="item in 来源选项" :key="item.value" :label="item.label" :value="item.value" />
          </ElSelect>
          <ElButton type="primary" :loading="saving" @click="创建快速备忘录">
            <ElIcon><Finished /></ElIcon>
            <span>保存</span>
          </ElButton>
        </div>
        <ElInput
          ref="quickInputRef"
          v-model="quickContent"
          type="textarea"
          :rows="5"
          resize="none"
          placeholder="临时文本、网址、摘录或一句突然冒出来的想法"
          @keydown="处理快速输入按键"
        />
      </div>

      <div class="filter-bar">
        <ElInput v-model="filters.keyword" class="search-input" clearable placeholder="搜索备忘录">
          <template #prefix>
            <ElIcon><Search /></ElIcon>
          </template>
        </ElInput>
        <ElSelect v-model="filters.status" class="filter-select" clearable placeholder="状态">
          <ElOption v-for="item in 状态选项" :key="item.value" :label="item.label" :value="item.value" />
        </ElSelect>
        <ElSelect v-model="filters.source" class="filter-select" clearable placeholder="来源">
          <ElOption v-for="item in 来源选项" :key="item.value" :label="item.label" :value="item.value" />
        </ElSelect>
        <ElButton v-if="有筛选" text @click="重置筛选">清除筛选</ElButton>
      </div>

      <div class="memo-list-wrap">
        <ElEmpty
          v-if="!loading && memos.length === 0"
          :description="showRecycleBin ? '回收站里还没有备忘录' : '还没有符合条件的备忘录'"
        />

        <div v-else class="memo-list">
          <article v-for="memo in memos" :key="memo.id" class="memo-item">
            <div class="memo-item__main" @click="打开编辑弹窗(memo)">
              <div class="memo-item__header">
                <h3 class="memo-item__title">{{ 提取预览标题(memo.content) }}</h3>
                <div class="memo-item__badges">
                  <ElTag size="small" :type="获取状态标签类型(memo.status)" effect="plain">
                    {{ 获取状态文案(memo.status) }}
                  </ElTag>
                  <ElTag size="small" effect="plain">{{ 获取来源文案(memo.source) }}</ElTag>
                  <ElTag v-if="memo.converted_to_type" size="small" type="success" effect="plain">
                    已转{{ 获取转出文案(memo.converted_to_type) }}
                  </ElTag>
                </div>
              </div>
              <p class="memo-item__content">{{ memo.content }}</p>
              <div class="memo-item__meta">
                <span>创建于 {{ 格式化时间(memo.created_at) }}</span>
                <span v-if="memo.archived_at">归档于 {{ 格式化时间(memo.archived_at) }}</span>
                <span v-if="memo.deleted_at">删除于 {{ 格式化时间(memo.deleted_at) }}</span>
              </div>
            </div>

            <div class="memo-item__actions">
              <template v-if="showRecycleBin">
                <ElButton :loading="deletingId === memo.id" @click="恢复当前备忘录(memo)">
                  <ElIcon><RefreshRight /></ElIcon>
                  <span>恢复</span>
                </ElButton>
                <ElButton type="danger" :loading="deletingId === memo.id" @click="删除当前备忘录(memo)">
                  <ElIcon><Delete /></ElIcon>
                  <span>删除</span>
                </ElButton>
              </template>
              <template v-else>
                <ElButton @click="打开编辑弹窗(memo)">
                  <ElIcon><EditPen /></ElIcon>
                  <span>编辑</span>
                </ElButton>
                <ElPopover placement="bottom-end" trigger="click" width="180">
                  <template #reference>
                    <ElButton :loading="convertingId === memo.id">
                      <ElIcon><MoreFilled /></ElIcon>
                      <span>整理</span>
                    </ElButton>
                  </template>
                  <div class="action-menu">
                    <button type="button" class="action-menu__item" @click="执行转换(memo, 'collection')">
                      <ElIcon><Collection /></ElIcon>
                      <span>转资料库</span>
                    </button>
                    <button type="button" class="action-menu__item" @click="执行转换(memo, 'article')">
                      <ElIcon><Document /></ElIcon>
                      <span>转文章草稿</span>
                    </button>
                    <button type="button" class="action-menu__item" @click="执行转换(memo, 'todo')">
                      <ElIcon><Tickets /></ElIcon>
                      <span>转待办</span>
                    </button>
                    <button
                      type="button"
                      class="action-menu__item"
                      @click="更新状态(memo, memo.status === 'archived' ? 'inbox' : 'archived')"
                    >
                      <ElIcon><FolderChecked /></ElIcon>
                      <span>{{ memo.status === 'archived' ? '取消归档' : '归档' }}</span>
                    </button>
                    <button type="button" class="action-menu__item action-menu__item--danger" @click="删除当前备忘录(memo)">
                      <ElIcon><Delete /></ElIcon>
                      <span>删除</span>
                    </button>
                  </div>
                </ElPopover>
              </template>
            </div>
          </article>
        </div>

        <div v-if="有更多" class="load-more-row">
          <ElButton :loading="loading" @click="加载备忘录(pagination.page + 1, true)">加载更多</ElButton>
        </div>
      </div>
    </PageSectionShell>

    <BaseDialog v-model="showEditDialog" title="编辑备忘录" width="720px" style="max-width: 96vw">
      <ElForm label-position="top">
        <div class="edit-grid">
          <ElFormItem label="状态">
            <ElSelect v-model="editStatus">
              <ElOption v-for="item in 状态选项" :key="item.value" :label="item.label" :value="item.value" />
            </ElSelect>
          </ElFormItem>
          <ElFormItem label="来源">
            <ElSelect v-model="editSource">
              <ElOption v-for="item in 来源选项" :key="item.value" :label="item.label" :value="item.value" />
            </ElSelect>
          </ElFormItem>
        </div>
        <ElFormItem label="内容">
          <ElInput
            ref="editInputRef"
            v-model="editContent"
            type="textarea"
            :rows="12"
            resize="vertical"
            placeholder="备忘录内容"
          />
        </ElFormItem>
      </ElForm>
      <template #footer>
        <div class="dialog-actions">
          <ElButton @click="showEditDialog = false">取消</ElButton>
          <ElButton type="primary" :loading="saving" @click="保存编辑">
            <ElIcon><Select /></ElIcon>
            <span>保存修改</span>
          </ElButton>
        </div>
      </template>
    </BaseDialog>
  </div>
</template>

<style scoped>
@import '@personal-system/ui/styles/media.css';

.memo-page {
  height: 100%;
  overflow-y: auto;
  padding: 24px 24px 120px;
  box-sizing: border-box;
}

.back-button {
  padding: 0;
}

.quick-input-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 18px;
  padding: 14px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  background: var(--el-bg-color);
}

.quick-input-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.source-select {
  width: 148px;
}

.filter-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}

.search-input {
  width: min(320px, 100%);
}

.filter-select {
  width: 136px;
}

.memo-list-wrap {
  min-height: 320px;
}

.memo-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.memo-item {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 16px;
  padding: 16px;
  border: 1px solid var(--el-border-color-lighter);
  border-left: 3px solid var(--el-color-primary);
  border-radius: 8px;
  background: var(--el-bg-color);
  transition: border-color 0.18s ease, box-shadow 0.18s ease;
}

.memo-item:hover {
  border-color: var(--el-color-primary-light-5);
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
}

.memo-item__main {
  min-width: 0;
  cursor: pointer;
}

.memo-item__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
}

.memo-item__title {
  min-width: 0;
  margin: 0;
  font-size: 17px;
  line-height: 1.45;
  font-weight: 700;
  color: var(--el-text-color-primary);
  word-break: break-word;
}

.memo-item__badges {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 6px;
  flex-shrink: 0;
}

.memo-item__content {
  margin: 10px 0 0;
  color: var(--el-text-color-regular);
  font-size: 14px;
  line-height: 1.8;
  white-space: pre-wrap;
  word-break: break-word;
  display: -webkit-box;
  line-clamp: 4;
  -webkit-line-clamp: 4;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.memo-item__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 12px;
  color: var(--el-text-color-secondary);
  font-size: 12px;
  line-height: 1.6;
}

.memo-item__actions {
  display: flex;
  align-items: flex-start;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 8px;
}

.action-menu {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.action-menu__item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: var(--el-text-color-primary);
  text-align: left;
  cursor: pointer;
}

.action-menu__item:hover {
  background: var(--el-fill-color-light);
}

.action-menu__item--danger {
  color: var(--el-color-danger);
}

.load-more-row {
  display: flex;
  justify-content: center;
  padding: 18px 0 0;
}

.edit-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

:global(.dark) .memo-item,
:global(.dark) .quick-input-panel {
  background: rgba(28, 32, 38, 0.96);
  border-color: rgba(255, 255, 255, 0.08);
}

@media (--mobile-viewport) {
  .memo-page {
    padding: 16px 16px 136px;
  }

  .quick-input-toolbar,
  .memo-item,
  .memo-item__header {
    align-items: stretch;
    flex-direction: column;
  }

  .source-select,
  .search-input,
  .filter-select {
    width: 100%;
  }

  .memo-item {
    display: flex;
  }

  .memo-item__badges,
  .memo-item__actions {
    justify-content: flex-start;
  }

  .memo-item__actions :deep(.el-button) {
    flex: 1 1 calc(50% - 4px);
    margin-left: 0;
  }

  .edit-grid {
    grid-template-columns: 1fr;
  }

  .dialog-actions {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
