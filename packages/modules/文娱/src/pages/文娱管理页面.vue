<script setup lang="ts">
import { Delete, Edit, Plus, Search } from '@element-plus/icons-vue'
import { 获取API错误消息 } from '@personal-system/api'
import type { FileItem } from '@personal-system/module-files'
import { 搜索文件 } from '@personal-system/module-files'
import {
  ElButton,
  ElCard,
  ElDialog,
  ElEmpty,
  ElForm,
  ElFormItem,
  ElInput,
  ElMessage,
  ElOption,
  ElPopconfirm,
  ElSelect,
  ElSpace,
  ElSwitch,
  ElTable,
  ElTableColumn,
  ElTag,
} from 'element-plus'
import { computed, onMounted, ref, watch } from 'vue'
import {
  创建文娱,
  删除文娱,
  更新文娱,
  获取文娱列表,
  获取文娱子分类统计,
  获取文娱标签统计,
} from '../api'
import MediaRating from '../components/评分展示.vue'
import { 获取文娱状态标签, 获取文娱状态选项 } from '../display'
import { 获取评分展示, 获取评分选项标签 } from '../rating'
import type { MediaListQuery, MediaPayload, MediaRecord, MediaStatus, MediaType } from '../types'

interface MediaFormState {
  title: string
  original_title: string
  media_type: MediaType
  status: MediaStatus
  rating: number | null
  creator: string
  genres_text: string
  tags_text: string
  summary: string
  description: string
  cover_file_id: string | null
  cover_file_name: string
  is_visible: boolean
}

const loading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)
const dialogMode = ref<'create' | 'edit'>('create')
const keyword = ref('')
const records = ref<MediaRecord[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(12)
const selectedGenre = ref('')
const selectedTag = ref('')
const selectedType = ref<MediaType | ''>('')
const selectedStatus = ref<MediaStatus | ''>('')
const availableGenres = ref<string[]>([])
const availableTags = ref<string[]>([])
const coverSearchKeyword = ref('')
const coverSearchLoading = ref(false)
const coverSearchResults = ref<FileItem[]>([])
const currentId = ref('')

const 主分类选项: Array<{ label: string, value: MediaType }> = [
  { label: '游戏', value: 'game' },
  { label: '小说', value: 'novel' },
  { label: '书籍', value: 'book' },
  { label: '动画', value: 'anime' },
  { label: '漫画', value: 'comic' },
  { label: '电影', value: 'movie' },
  { label: '剧集', value: 'tv' },
  { label: '音乐', value: 'music' },
  { label: '其他', value: 'other' },
]

const 状态选项 = computed(() => 获取文娱状态选项(selectedType.value))
const 表单状态选项 = computed(() => 获取文娱状态选项(form.value.media_type))
const 评分等级选项 = Array.from({ length: 15 }, (_, index) => index + 1)
const 评分列宽度 = 180

function 创建空表单(): MediaFormState {
  return {
    title: '',
    original_title: '',
    media_type: 'anime',
    status: 'done',
    rating: null,
    creator: '',
    genres_text: '',
    tags_text: '',
    summary: '',
    description: '',
    cover_file_id: null,
    cover_file_name: '',
    is_visible: true,
  }
}

const form = ref<MediaFormState>(创建空表单())

const 对话框标题 = computed(() => dialogMode.value === 'create' ? '新增文娱条目' : '编辑文娱条目')

function 解析标签文本(text: string): string[] {
  return text
    .replaceAll('，', ',')
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
}

function 构建请求体(): MediaPayload {
  return {
    title: form.value.title.trim(),
    original_title: form.value.original_title.trim() || null,
    media_type: form.value.media_type,
    status: form.value.status,
    rating: form.value.rating,
    creator: form.value.creator.trim() || null,
    genres: 解析标签文本(form.value.genres_text),
    tags: 解析标签文本(form.value.tags_text),
    summary: form.value.summary.trim() || null,
    description: form.value.description.trim() || null,
    cover_file_id: form.value.cover_file_id,
    is_visible: form.value.is_visible,
  }
}

function 重置表单() {
  form.value = 创建空表单()
  currentId.value = ''
  coverSearchKeyword.value = ''
  coverSearchResults.value = []
}

function 获取评分摘要(rating: number) {
  return 获取评分展示(rating).summaryText
}

function 从记录填充表单(record: MediaRecord) {
  form.value = {
    title: record.title,
    original_title: record.original_title ?? '',
    media_type: record.media_type,
    status: record.status,
    rating: record.rating,
    creator: record.creator ?? '',
    genres_text: record.genres.join(', '),
    tags_text: record.tags.join(', '),
    summary: record.summary ?? '',
    description: record.description ?? '',
    cover_file_id: record.cover_file_id,
    cover_file_name: record.cover_file?.original_name ?? '',
    is_visible: record.is_visible,
  }
  currentId.value = record.id
}

async function 加载筛选项() {
  const [genres, tags] = await Promise.all([
    获取文娱子分类统计(),
    获取文娱标签统计(),
  ])
  availableGenres.value = genres.map((item) => item.name)
  availableTags.value = tags.map((item) => item.name)
}

async function 加载列表() {
  loading.value = true
  try {
    const query: MediaListQuery = {
      page: page.value,
      page_size: pageSize.value,
      keyword: keyword.value.trim(),
      media_type: selectedType.value,
      status: selectedStatus.value,
      genre: selectedGenre.value || undefined,
      tag: selectedTag.value || undefined,
    }
    const response = await 获取文娱列表(query)
    records.value = response.items
    total.value = response.total
  } catch (error) {
    ElMessage.error(获取API错误消息(error, '加载文娱列表失败'))
  } finally {
    loading.value = false
  }
}

async function 搜索封面文件() {
  const search = coverSearchKeyword.value.trim()
  if (!search) {
    coverSearchResults.value = []
    return
  }
  coverSearchLoading.value = true
  try {
    const data = await 搜索文件(search)
    coverSearchResults.value = data.files
  } catch (error) {
    ElMessage.error(获取API错误消息(error, '搜索封面文件失败'))
  } finally {
    coverSearchLoading.value = false
  }
}

function 选择封面文件(file: FileItem) {
  form.value.cover_file_id = file.id
  form.value.cover_file_name = file.original_name
}

function 清除封面文件() {
  form.value.cover_file_id = null
  form.value.cover_file_name = ''
}

function 打开新增() {
  dialogMode.value = 'create'
  重置表单()
  dialogVisible.value = true
}

function 打开编辑(record: MediaRecord) {
  dialogMode.value = 'edit'
  从记录填充表单(record)
  dialogVisible.value = true
}

async function 提交表单() {
  if (!form.value.title.trim()) {
    ElMessage.warning('名称不能为空')
    return
  }
  saving.value = true
  try {
    const payload = 构建请求体()
    if (dialogMode.value === 'create') {
      await 创建文娱(payload)
      ElMessage.success('文娱条目已创建')
    } else {
      await 更新文娱(currentId.value, payload)
      ElMessage.success('文娱条目已更新')
    }
    dialogVisible.value = false
    await Promise.all([加载列表(), 加载筛选项()])
  } catch (error) {
    ElMessage.error(获取API错误消息(error, '保存文娱条目失败'))
  } finally {
    saving.value = false
  }
}

async function 执行删除(id: string) {
  try {
    await 删除文娱(id)
    ElMessage.success('文娱条目已删除')
    await Promise.all([加载列表(), 加载筛选项()])
  } catch (error) {
    ElMessage.error(获取API错误消息(error, '删除文娱条目失败'))
  }
}

watch([selectedType, selectedStatus, selectedGenre, selectedTag], () => {
  page.value = 1
  void 加载列表()
})

onMounted(async () => {
  await Promise.all([加载列表(), 加载筛选项()])
})
</script>

<template>
  <div class="media-page">
    <ElCard shadow="never" class="media-panel">
      <template #header>
        <div class="media-panel__header">
          <div>
            <h2 class="media-panel__title">作品推荐</h2>
            <p class="media-panel__subtitle">记录、筛选和维护自己的文娱作品清单。</p>
          </div>
          <ElSpace>
            <ElButton type="primary" :icon="Plus" @click="打开新增">新增条目</ElButton>
          </ElSpace>
        </div>
      </template>

      <div class="media-toolbar">
        <ElInput v-model="keyword" placeholder="搜索名称、原名、作者或简介" clearable @keyup.enter="加载列表">
          <template #prefix>
            <Search />
          </template>
        </ElInput>
        <ElSelect v-model="selectedType" clearable placeholder="主分类">
          <ElOption v-for="item in 主分类选项" :key="item.value" :label="item.label" :value="item.value" />
        </ElSelect>
        <ElSelect v-model="selectedStatus" clearable placeholder="状态">
          <ElOption v-for="item in 状态选项" :key="item.value" :label="item.label" :value="item.value" />
        </ElSelect>
        <ElSelect v-model="selectedGenre" clearable filterable placeholder="子分类">
          <ElOption v-for="item in availableGenres" :key="item" :label="item" :value="item" />
        </ElSelect>
        <ElSelect v-model="selectedTag" clearable filterable placeholder="标签">
          <ElOption v-for="item in availableTags" :key="item" :label="item" :value="item" />
        </ElSelect>
        <ElButton type="primary" @click="加载列表">搜索</ElButton>
      </div>

      <ElTable v-loading="loading" :data="records" class="media-table" empty-text="暂无文娱条目">
        <ElTableColumn label="名称" min-width="280">
          <template #default="{ row }: { row: MediaRecord }">
            <div class="media-title-cell">
              <img v-if="row.cover_file?.thumbnail_url || row.cover_file?.url" :src="row.cover_file?.thumbnail_url || row.cover_file?.url || ''" :alt="row.title" class="media-cover" >
              <div class="media-title-meta">
                <div class="media-title">{{ row.title }}</div>
                <div v-if="row.original_title" class="media-original-title">{{ row.original_title }}</div>
              </div>
            </div>
          </template>
        </ElTableColumn>
        <ElTableColumn label="主分类" width="100">
          <template #default="{ row }: { row: MediaRecord }">
            <ElTag>{{ 主分类选项.find((item) => item.value === row.media_type)?.label || row.media_type }}</ElTag>
          </template>
        </ElTableColumn>
        <ElTableColumn label="状态" width="140">
          <template #default="{ row }: { row: MediaRecord }">
            {{ 获取文娱状态标签(row.media_type, row.status) }}
          </template>
        </ElTableColumn>
        <ElTableColumn label="评分" :width="评分列宽度">
          <template #default="{ row }: { row: MediaRecord }">
            <span v-if="row.rating" class="media-rating-cell">
              <span>{{ row.rating }}</span>
              <span class="media-rating-cell__divider">·</span>
              <MediaRating :rating="row.rating" compact />
              <span class="media-rating-cell__text">{{ 获取评分摘要(row.rating) }}</span>
            </span>
            <span v-else>-</span>
          </template>
        </ElTableColumn>
        <ElTableColumn label="创作者" min-width="160" prop="creator" />
        <ElTableColumn label="标签" min-width="220">
          <template #default="{ row }: { row: MediaRecord }">
            <ElSpace wrap>
              <ElTag v-for="tag in row.tags.slice(0, 4)" :key="tag" size="small" type="info">{{ tag }}</ElTag>
            </ElSpace>
          </template>
        </ElTableColumn>
        <ElTableColumn label="公开" width="90">
          <template #default="{ row }: { row: MediaRecord }">
            <ElTag :type="row.is_visible ? 'success' : 'info'">{{ row.is_visible ? '是' : '否' }}</ElTag>
          </template>
        </ElTableColumn>
        <ElTableColumn label="操作" width="140" fixed="right">
          <template #default="{ row }: { row: MediaRecord }">
            <ElSpace>
              <ElButton link type="primary" :icon="Edit" @click="打开编辑(row)">编辑</ElButton>
              <ElPopconfirm title="确认删除这条文娱记录？" @confirm="执行删除(row.id)">
                <template #reference>
                  <ElButton link type="danger" :icon="Delete">删除</ElButton>
                </template>
              </ElPopconfirm>
            </ElSpace>
          </template>
        </ElTableColumn>
      </ElTable>

      <div v-if="!loading && records.length === 0" class="media-empty">
        <ElEmpty description="还没有文娱条目" />
      </div>

      <div class="media-pagination">
        <span>共 {{ total }} 条</span>
        <ElSpace>
          <ElButton :disabled="page <= 1" @click="page -= 1; 加载列表()">上一页</ElButton>
          <span>第 {{ page }} 页</span>
          <ElButton :disabled="records.length < pageSize" @click="page += 1; 加载列表()">下一页</ElButton>
        </ElSpace>
      </div>
    </ElCard>

    <ElDialog v-model="dialogVisible" :title="对话框标题" width="900px" destroy-on-close>
      <ElForm label-width="96px" class="media-form">
        <div class="media-form__grid">
          <ElFormItem label="名称" required>
            <ElInput v-model="form.title" maxlength="300" />
          </ElFormItem>
          <ElFormItem label="原名">
            <ElInput v-model="form.original_title" maxlength="300" />
          </ElFormItem>
          <ElFormItem label="主分类">
            <ElSelect v-model="form.media_type">
              <ElOption v-for="item in 主分类选项" :key="item.value" :label="item.label" :value="item.value" />
            </ElSelect>
          </ElFormItem>
          <ElFormItem label="状态">
            <ElSelect v-model="form.status">
              <ElOption v-for="item in 表单状态选项" :key="item.value" :label="item.label" :value="item.value" />
            </ElSelect>
          </ElFormItem>
          <ElFormItem label="评分">
            <ElSelect v-model="form.rating" clearable placeholder="可空">
              <ElOption v-for="item in 评分等级选项" :key="item" :label="获取评分选项标签(item)" :value="item" />
            </ElSelect>
          </ElFormItem>
          <ElFormItem label="创作者">
            <ElInput v-model="form.creator" maxlength="200" placeholder="作者 / 导演 / 工作室 / 开发商" />
          </ElFormItem>
          <ElFormItem label="子分类" class="media-form__full">
            <ElInput v-model="form.genres_text" placeholder="多个值用逗号分隔" />
          </ElFormItem>
          <ElFormItem label="标签" class="media-form__full">
            <ElInput v-model="form.tags_text" placeholder="多个值用逗号分隔" />
          </ElFormItem>
          <ElFormItem label="简介" class="media-form__full">
            <ElInput v-model="form.summary" type="textarea" :rows="3" />
          </ElFormItem>
          <ElFormItem label="描述" class="media-form__full">
            <ElInput v-model="form.description" type="textarea" :rows="5" />
          </ElFormItem>
          <ElFormItem label="公开展示">
            <ElSwitch v-model="form.is_visible" />
          </ElFormItem>
          <ElFormItem label="封面" class="media-form__full">
            <div class="cover-picker">
              <div class="cover-picker__toolbar">
                <ElInput v-model="coverSearchKeyword" placeholder="搜索已有文件作为封面" clearable @keyup.enter="搜索封面文件" />
                <ElButton :loading="coverSearchLoading" @click="搜索封面文件">搜索</ElButton>
                <ElButton v-if="form.cover_file_id" @click="清除封面文件">清除封面</ElButton>
              </div>
              <div v-if="form.cover_file_name" class="cover-picker__selected">当前封面：{{ form.cover_file_name }}</div>
              <div v-if="coverSearchResults.length > 0" class="cover-picker__results">
                <button
                  v-for="file in coverSearchResults"
                  :key="file.id"
                  type="button"
                  class="cover-picker__item"
                  @click="选择封面文件(file)"
                >
                  <img v-if="file.thumbnail_url || file.url" :src="file.thumbnail_url || file.url" :alt="file.original_name" class="cover-picker__thumb" >
                  <span>{{ file.original_name }}</span>
                </button>
              </div>
            </div>
          </ElFormItem>
        </div>
      </ElForm>
      <template #footer>
        <ElSpace>
          <ElButton @click="dialogVisible = false">取消</ElButton>
          <ElButton type="primary" :loading="saving" @click="提交表单">保存</ElButton>
        </ElSpace>
      </template>
    </ElDialog>
  </div>
</template>

<style scoped>
.media-page {
  padding: 20px;
}

.media-panel {
  border-radius: 20px;
}

.media-panel__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.media-panel__title {
  margin: 0;
  font-size: 24px;
}

.media-panel__subtitle {
  margin: 6px 0 0;
  color: var(--el-text-color-secondary);
}

.media-toolbar {
  display: grid;
  grid-template-columns: minmax(240px, 1.4fr) repeat(4, minmax(120px, 1fr)) auto;
  gap: 12px;
  margin-bottom: 20px;
}

.media-table {
  width: 100%;
}

.media-title-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.media-cover {
  width: 52px;
  height: 72px;
  border-radius: 10px;
  object-fit: cover;
  background: #f5f5f5;
}

.media-title {
  font-weight: 600;
}

.media-original-title {
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.media-rating-cell {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  white-space: nowrap;
}

.media-rating-cell__divider,
.media-rating-cell__text {
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.media-empty {
  padding: 24px 0;
}

.media-pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 16px;
}

.media-form__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0 16px;
}

.media-form__full {
  grid-column: 1 / -1;
}

.cover-picker {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.cover-picker__toolbar {
  display: flex;
  gap: 12px;
}

.cover-picker__selected {
  color: var(--el-text-color-secondary);
}

.cover-picker__results {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 12px;
  max-height: 260px;
  overflow: auto;
}

.cover-picker__item {
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: flex-start;
  padding: 10px;
  border: 1px solid var(--el-border-color);
  border-radius: 12px;
  background: transparent;
  cursor: pointer;
  text-align: left;
}

.cover-picker__thumb {
  width: 100%;
  aspect-ratio: 3 / 4;
  object-fit: cover;
  border-radius: 8px;
  background: #f5f5f5;
}

@media (max-width: 960px) {
  .media-toolbar {
    grid-template-columns: 1fr 1fr;
  }

  .media-form__grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .media-page {
    padding: 12px;
  }

  .media-panel__header,
  .media-pagination,
  .cover-picker__toolbar {
    flex-direction: column;
    align-items: stretch;
  }

  .media-toolbar {
    grid-template-columns: 1fr;
  }
}
</style>
