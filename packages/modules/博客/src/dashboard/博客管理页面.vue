<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  DocumentAdd,
  Download,
  Edit,
  MoreFilled,
  Refresh,
  Search,
  Upload,
  View,
} from '@element-plus/icons-vue'
import {
  ElButton,
  ElDialog,
  ElDropdown,
  ElDropdownItem,
  ElDropdownMenu,
  ElEmpty,
  ElInput,
  ElMessage,
  ElMessageBox,
  ElPagination,
  ElPopconfirm,
  ElSelect,
  ElOption,
  ElSkeleton,
  ElTable,
  ElTableColumn,
  ElTag,
  ElTooltip,
} from 'element-plus'
import { PageSectionShell, SegmentedSwitch } from '@personal-system/ui'
import { 获取API错误消息 } from '@personal-system/api'
import { 根据ID获取我的文章, type ArticleRecord } from '@personal-system/module-articles'
import MarkdownRenderer from '@personal-system/module-articles/components/Markdown渲染器.vue'
import {
  获取博客管理列表,
  获取博客发布快照,
  发布博客文章,
  设置博客可见性,
  撤下博客发布,
  type BlogManageItem,
  type BlogManageState,
  type BlogVisibility,
} from '../publication'

const route = useRoute()
const router = useRouter()
const prefix = computed(() => (route.path.startsWith('/dashboard') ? '/dashboard' : ''))
const items = ref<BlogManageItem[]>([])
const page = ref(1)
const total = ref(0)
const state = ref<BlogManageState>('all')
const search = ref('')
const loading = ref(false)
const pendingId = ref('')
const errorMessage = ref('')
const dialogVisible = ref(false)
const previewLoading = ref(false)
const selectedItem = ref<BlogManageItem | null>(null)
const draft = ref<ArticleRecord | null>(null)
const snapshot = ref<ArticleRecord | null>(null)
const previewMode = ref<'draft' | 'snapshot'>('draft')
const visibilityChoices = ref<Record<string, BlogVisibility>>({})
const isMobileViewport = ref(false)
const preview = computed(() => (previewMode.value === 'draft' ? draft.value : snapshot.value))
const previewOptions = [
  { label: '文章', value: 'draft' },
  { label: '发布版本', value: 'snapshot' },
]
let requestSequence = 0
let previewSequence = 0

async function load() {
  const sequence = ++requestSequence
  loading.value = true
  errorMessage.value = ''
  try {
    const result = await 获取博客管理列表(page.value, state.value, search.value)
    if (sequence !== requestSequence) return
    items.value = result.items
    total.value = result.total
    if (page.value > Math.max(result.pages, 1)) {
      page.value = Math.max(result.pages, 1)
      return
    }
  } catch (error) {
    if (sequence !== requestSequence) return
    errorMessage.value = 获取API错误消息(error, '加载博客管理失败')
    console.error('[博客管理] 加载失败', error)
  } finally {
    if (sequence === requestSequence) loading.value = false
  }
}

function filter() {
  if (page.value !== 1) page.value = 1
  else void load()
}

function statusLabel(item: BlogManageItem) {
  if (!item.publication) return '未发布'
  if (!item.publication.is_published) return '已撤下'
  return item.has_unpublished_changes ? '有未发布修改' : '已发布'
}

async function openPreview(item: BlogManageItem, mode: 'draft' | 'snapshot') {
  const sequence = ++previewSequence
  selectedItem.value = item
  previewMode.value = mode
  draft.value = null
  snapshot.value = null
  dialogVisible.value = true
  previewLoading.value = true
  try {
    const [draftResult, snapshotResult] = await Promise.all([
      根据ID获取我的文章(item.id),
      item.publication ? 获取博客发布快照(item.id) : Promise.resolve(null),
    ])
    if (sequence !== previewSequence) return
    draft.value = draftResult
    snapshot.value = snapshotResult
  } catch (error) {
    if (sequence !== previewSequence) return
    ElMessage.error(获取API错误消息(error, '加载预览失败'))
    dialogVisible.value = false
  } finally {
    if (sequence === previewSequence) previewLoading.value = false
  }
}

function getVisibility(item: BlogManageItem): BlogVisibility {
  return visibilityChoices.value[item.id] ?? item.publication?.visibility ?? 'public'
}

function publishLabel(item: BlogManageItem) {
  if (item.publication?.is_published) return '更新发布'
  return item.publication ? '重新发布' : '发布'
}

function canPublish(item: BlogManageItem) {
  return !item.publication?.is_published || item.has_unpublished_changes
}

async function publish(item: BlogManageItem) {
  if (pendingId.value) return
  pendingId.value = item.id
  try {
    await 发布博客文章(item.id, item.revision, getVisibility(item))
    delete visibilityChoices.value[item.id]
    console.info('[博客管理] 发布完成', { articleId: item.id, revision: item.revision })
    ElMessage.success(item.publication?.is_published ? '博客发布版本已更新' : '博客已发布')
    await load()
  } catch (error) {
    ElMessage.error(获取API错误消息(error, '发布失败'))
    console.error('[博客管理] 发布失败', error)
    await load()
  } finally {
    pendingId.value = ''
  }
}

async function changeVisibility(item: BlogManageItem, value: BlogVisibility) {
  if (pendingId.value) return
  if (!item.publication) {
    visibilityChoices.value[item.id] = value
    return
  }
  if (value === item.publication.visibility) return
  pendingId.value = item.id
  try {
    await 设置博客可见性(item.id, value)
    item.publication.visibility = value
    console.info('[博客管理] 可见性已更新', { articleId: item.id, visibility: value })
    ElMessage.success('博客可见性已更新')
  } catch (error) {
    ElMessage.error(获取API错误消息(error, '修改可见性失败'))
    console.error('[博客管理] 修改可见性失败', error)
  } finally {
    pendingId.value = ''
  }
}

async function withdraw(item: BlogManageItem) {
  if (pendingId.value) return
  try {
    await ElMessageBox.confirm(
      `确定撤下《${item.publication?.title || item.title}》？`,
      '撤下博客',
      {
        type: 'warning',
        confirmButtonText: '撤下',
        cancelButtonText: '取消',
      },
    )
  } catch {
    return
  }
  if (pendingId.value) return
  pendingId.value = item.id
  try {
    await 撤下博客发布(item.id)
    console.info('[博客管理] 已撤下', { articleId: item.id })
    ElMessage.success('博客已撤下')
    await load()
  } catch (error) {
    ElMessage.error(获取API错误消息(error, '撤下失败'))
    console.error('[博客管理] 撤下失败', error)
  } finally {
    pendingId.value = ''
  }
}

function formatTime(value: string | undefined) {
  return value ? new Date(value).toLocaleString() : '-'
}

function formatWordCount(value: number) {
  return `${Math.max(0, value).toLocaleString()} 字`
}

function syncViewport() {
  isMobileViewport.value = window.innerWidth <= 768
}

watch(page, () => void load())
watch(state, filter)
onMounted(() => {
  syncViewport()
  window.addEventListener('resize', syncViewport)
  void load()
})
onBeforeUnmount(() => window.removeEventListener('resize', syncViewport))
</script>

<template>
  <div class="blog-manage-page">
    <PageSectionShell title="博客管理">
      <template #actions>
        <ElButton :icon="DocumentAdd" @click="router.push(`${prefix}/articles/edit`)"
          >写文章</ElButton
        >
        <ElButton
          :icon="Refresh"
          circle
          title="刷新"
          aria-label="刷新"
          :loading="loading"
          @click="load"
        />
      </template>
      <div class="blog-manage-filters">
        <ElSelect v-model="state" aria-label="发布状态">
          <ElOption label="全部文章" value="all" />
          <ElOption label="已发布" value="published" />
          <ElOption label="未发布／已撤下" value="unpublished" />
          <ElOption label="有未发布修改" value="changed" />
        </ElSelect>
        <ElInput
          v-model="search"
          clearable
          placeholder="搜索文章标题"
          :prefix-icon="Search"
          @keyup.enter="filter"
          @clear="filter"
        />
        <ElButton :icon="Search" circle title="搜索" aria-label="搜索" @click="filter" />
      </div>
      <div v-if="errorMessage" class="blog-manage-error">
        {{ errorMessage }}
        <ElButton link type="primary" @click="load">重试</ElButton>
      </div>
      <ElSkeleton :loading="loading && !items.length" animated :rows="6">
        <ElTable :data="items" class="blog-manage-table">
          <ElTableColumn label="文章" :min-width="isMobileViewport ? 160 : 240">
            <template #default="{ row }">
              <div class="blog-manage-title">{{ row.title || '未命名文章' }}</div>
              <div
                v-if="row.publication && row.title !== row.publication.title"
                class="blog-manage-muted"
              >
                发布标题：{{ row.publication.title }}
              </div>
            </template>
          </ElTableColumn>
          <ElTableColumn label="发布状态" width="145">
            <template #default="{ row }">
              <ElTag
                :type="
                  row.publication?.is_published
                    ? row.has_unpublished_changes
                      ? 'warning'
                      : 'success'
                    : 'info'
                "
              >
                {{ statusLabel(row as BlogManageItem) }}
              </ElTag>
            </template>
          </ElTableColumn>
          <ElTableColumn label="可见性" width="135">
            <template #default="{ row }">
              <ElSelect
                :model-value="getVisibility(row as BlogManageItem)"
                :disabled="!!pendingId"
                :aria-label="`${row.title}的可见性`"
                size="small"
                @change="changeVisibility(row as BlogManageItem, $event)"
              >
                <ElOption label="公开" value="public" />
                <ElOption label="登录可见" value="login_required" />
              </ElSelect>
            </template>
          </ElTableColumn>
          <ElTableColumn label="字数" width="135">
            <template #default="{ row }">
              <div>文章 {{ formatWordCount(row.word_count) }}</div>
              <div v-if="row.publication" class="blog-manage-muted">
                发布 {{ formatWordCount(row.publication.word_count) }}
              </div>
            </template>
          </ElTableColumn>
          <ElTableColumn v-if="!isMobileViewport" label="版本" width="90">
            <template #default="{ row }">{{
              row.publication ? `第 ${row.publication.version} 版` : '-'
            }}</template>
          </ElTableColumn>
          <ElTableColumn v-if="!isMobileViewport" label="更新发布" width="175">
            <template #default="{ row }">{{ formatTime(row.publication?.updated_at) }}</template>
          </ElTableColumn>
          <ElTableColumn v-if="!isMobileViewport" label="阅读／点赞" width="115">
            <template #default="{ row }"
              >{{ row.publication?.view_count ?? 0 }} ／
              {{ row.publication?.like_count ?? 0 }}</template
            >
          </ElTableColumn>
          <ElTableColumn label="操作" :width="isMobileViewport ? 144 : 260" fixed="right">
            <template #default="{ row }">
              <div class="blog-manage-actions">
                <ElButton
                  size="small"
                  :icon="View"
                  :disabled="!!pendingId"
                  @click="
                    openPreview(row as BlogManageItem, row.publication ? 'snapshot' : 'draft')
                  "
                  >预览</ElButton
                >
                <ElTooltip content="编辑文章" placement="top">
                  <ElButton
                    size="small"
                    :icon="Edit"
                    aria-label="编辑文章"
                    :disabled="!!pendingId"
                    @click="router.push(`${prefix}/articles/edit/${row.id}`)"
                  />
                </ElTooltip>
                <ElPopconfirm
                  :title="`确定${publishLabel(row as BlogManageItem)}《${row.title || '未命名文章'}》？`"
                  :confirm-button-text="publishLabel(row as BlogManageItem)"
                  cancel-button-text="取消"
                  :width="260"
                  @confirm="publish(row as BlogManageItem)"
                >
                  <template #reference>
                    <ElButton
                      size="small"
                      type="primary"
                      :icon="Upload"
                      :loading="pendingId === row.id"
                      :disabled="!!pendingId || !canPublish(row as BlogManageItem)"
                      >{{ publishLabel(row as BlogManageItem) }}</ElButton
                    >
                  </template>
                </ElPopconfirm>
                <ElDropdown
                  trigger="click"
                  :disabled="!!pendingId || !row.publication?.is_published"
                  @command="withdraw(row as BlogManageItem)"
                >
                  <ElButton
                    size="small"
                    :icon="MoreFilled"
                    title="更多操作"
                    aria-label="更多操作"
                    :disabled="!!pendingId || !row.publication?.is_published"
                  />
                  <template #dropdown>
                    <ElDropdownMenu>
                      <ElDropdownItem
                        command="withdraw"
                        :icon="Download"
                        class="blog-withdraw-action"
                        >撤下博客</ElDropdownItem
                      >
                    </ElDropdownMenu>
                  </template>
                </ElDropdown>
              </div>
            </template>
          </ElTableColumn>
          <template #empty><ElEmpty description="暂无文章" /></template>
        </ElTable>
      </ElSkeleton>
      <ElPagination
        v-if="total > 10"
        v-model:current-page="page"
        :total="total"
        :page-size="10"
        layout="prev, pager, next"
        class="blog-manage-pagination"
      />
    </PageSectionShell>
    <ElDialog
      v-model="dialogVisible"
      :title="selectedItem?.title || '文章预览'"
      width="min(900px, calc(100vw - 32px))"
      class="blog-publication-dialog"
    >
      <div class="blog-preview-controls">
        <SegmentedSwitch
          v-if="selectedItem?.publication"
          v-model="previewMode"
          :options="previewOptions"
          aria-label="预览版本"
        />
        <span v-if="preview" class="blog-manage-muted">{{
          formatWordCount(preview.word_count)
        }}</span>
      </div>
      <ElSkeleton :loading="previewLoading" animated :rows="8">
        <article v-if="preview" class="blog-publication-preview">
          <h2>{{ preview.title }}</h2>
          <img v-if="preview.cover_url" :src="preview.cover_url" :alt="preview.title" />
          <p v-if="preview.excerpt" class="blog-manage-muted">{{ preview.excerpt }}</p>
          <div class="blog-preview-taxonomy">
            <ElTag v-if="preview.category" type="info">{{ preview.category.name }}</ElTag>
            <ElTag v-for="tag in preview.tags" :key="tag.id">{{ tag.name }}</ElTag>
          </div>
          <MarkdownRenderer :content="preview.content" />
        </article>
      </ElSkeleton>
      <template #footer>
        <div class="blog-preview-footer">
          <ElButton @click="dialogVisible = false">关闭</ElButton>
        </div>
      </template>
    </ElDialog>
  </div>
</template>

<style scoped>
.blog-manage-page {
  height: 100%;
  overflow-y: auto;
  padding: 24px;
  box-sizing: border-box;
}
.blog-manage-filters {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  align-items: center;
}
.blog-manage-filters .el-select {
  width: 180px;
  flex-shrink: 0;
}
.blog-manage-filters .el-input {
  max-width: 360px;
}
.blog-manage-title {
  overflow-wrap: anywhere;
  font-weight: 500;
}
.blog-manage-muted {
  color: var(--el-text-color-secondary);
  font-size: 13px;
  overflow-wrap: anywhere;
}
.blog-manage-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  min-height: 32px;
}
.blog-manage-actions .el-button {
  margin-left: 0;
}
.blog-withdraw-action {
  color: var(--el-color-danger);
}
.blog-manage-pagination {
  margin-top: 20px;
  justify-content: flex-end;
}
.blog-manage-error {
  color: var(--el-color-danger);
  padding: 12px 0;
}
.blog-preview-controls {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
  margin-bottom: 20px;
}
.blog-publication-preview {
  max-height: 60vh;
  overflow-y: auto;
  overflow-wrap: anywhere;
}
.blog-publication-preview h2 {
  font-size: 22px;
  margin: 0 0 16px;
}
.blog-publication-preview > img {
  max-width: 100%;
  max-height: 260px;
  object-fit: contain;
}
.blog-preview-taxonomy {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 12px 0;
}
.blog-preview-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  flex-wrap: wrap;
}
.blog-preview-footer .el-button {
  margin-left: 0;
}
@media (max-width: 640px) {
  .blog-manage-page {
    padding: 16px;
  }
  .blog-manage-filters {
    flex-wrap: wrap;
    gap: 8px;
  }
  .blog-manage-filters .el-input {
    flex: 1;
    min-width: 120px;
  }
  .blog-manage-filters .el-select {
    width: 100%;
  }
}
@media (max-width: 768px) {
  .blog-manage-actions {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 24px;
    gap: 6px 4px;
  }
  .blog-manage-actions .el-button {
    width: 100%;
    padding: 0 4px;
  }
}
</style>
