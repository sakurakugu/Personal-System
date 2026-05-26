<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { ElButton, ElCard, ElDrawer, ElEmpty, ElInput, ElOption, ElRate, ElSelect, ElSpace, ElTag } from 'element-plus'
import { RefreshRight, Search } from '@element-plus/icons-vue'
import { 获取公开文娱列表, type MediaRecord, type MediaStatus, type MediaType } from '@personal-system/module-media'

const loading = ref(false)
const keyword = ref('')
const activeType = ref<MediaType | ''>('')
const activeStatus = ref<MediaStatus | ''>('')
const items = ref<MediaRecord[]>([])
const selectedItem = ref<MediaRecord | null>(null)
const drawerVisible = ref(false)

const 主分类选项: Array<{ label: string, value: MediaType | '' }> = [
  { label: '全部', value: '' },
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

const 状态选项: Array<{ label: string, value: MediaStatus | '' }> = [
  { label: '全部状态', value: '' },
  { label: '想看 / 想玩 / 想读', value: 'planned' },
  { label: '在看 / 在玩 / 在读', value: 'doing' },
  { label: '已看 / 已玩 / 已读', value: 'done' },
  { label: '搁置', value: 'paused' },
  { label: '弃坑', value: 'dropped' },
]

const 状态标签映射 = computed<Record<string, string>>(() => Object.fromEntries(状态选项.map((item) => [item.value, item.label])))
const 主分类标签映射 = computed<Record<string, string>>(() => Object.fromEntries(主分类选项.map((item) => [item.value, item.label])))

async function 加载列表() {
  loading.value = true
  try {
    const response = await 获取公开文娱列表({
      page: 1,
      page_size: 48,
      media_type: activeType.value,
      status: activeStatus.value,
      keyword: keyword.value.trim(),
    })
    items.value = response.items
  } catch (error) {
    console.error('[media-view] 加载公开文娱失败', error)
  } finally {
    loading.value = false
  }
}

function 打开详情(item: MediaRecord) {
  selectedItem.value = item
  drawerVisible.value = true
}

function 获取摘要(item: MediaRecord) {
  return item.description || item.summary || '暂未填写简介。'
}

watch([activeType, activeStatus], () => {
  void 加载列表()
})

onMounted(() => {
  void 加载列表()
})
</script>

<template>
  <div class="media-view">
    <ElCard shadow="never" class="media-shell">
      <div class="media-header">
        <div>
          <h1 class="media-title">文娱推荐</h1>
          <p class="media-subtitle">推荐文娱列表，集中展示看过、玩过、读过且愿意留下记录的作品。</p>
        </div>
        <ElButton :icon="RefreshRight" @click="加载列表">刷新</ElButton>
      </div>

      <div class="media-filters">
        <ElInput v-model="keyword" placeholder="搜索名称、原名、创作者或简介" clearable @keyup.enter="加载列表">
          <template #prefix>
            <Search />
          </template>
        </ElInput>
        <ElSelect v-model="activeType" placeholder="主分类">
          <ElOption v-for="item in 主分类选项" :key="item.value || 'all'" :label="item.label" :value="item.value" />
        </ElSelect>
        <ElSelect v-model="activeStatus" placeholder="状态">
          <ElOption v-for="item in 状态选项" :key="item.value || 'all'" :label="item.label" :value="item.value" />
        </ElSelect>
        <ElButton type="primary" @click="加载列表">筛选</ElButton>
      </div>

      <div v-if="items.length > 0" class="media-grid">
        <button
          v-for="item in items"
          :key="item.id"
          type="button"
          class="media-item"
          @click="打开详情(item)"
        >
          <div class="media-item__cover-wrap">
            <img v-if="item.cover_file?.thumbnail_url || item.cover_file?.url" :src="item.cover_file?.thumbnail_url || item.cover_file?.url || ''" :alt="item.title" class="media-item__cover" >
            <div v-else class="media-item__cover media-item__cover--empty">{{ item.title.slice(0, 1) }}</div>
          </div>
          <div class="media-item__body">
            <div class="media-item__meta">
              <ElTag size="small">{{ 主分类标签映射[item.media_type] || item.media_type }}</ElTag>
              <ElTag size="small" type="info">{{ 状态标签映射[item.status] || item.status }}</ElTag>
            </div>
            <h2 class="media-item__title">{{ item.title }}</h2>
            <div v-if="item.original_title" class="media-item__original">{{ item.original_title }}</div>
            <div v-if="item.creator" class="media-item__creator">{{ item.creator }}</div>
            <ElRate v-if="item.rating" :model-value="item.rating / 2" disabled allow-half />
            <p class="media-item__summary">{{ 获取摘要(item) }}</p>
            <ElSpace wrap>
              <ElTag v-for="genre in item.genres.slice(0, 3)" :key="genre" size="small" effect="plain">{{ genre }}</ElTag>
              <ElTag v-for="tag in item.tags.slice(0, 3)" :key="tag" size="small" type="success" effect="plain">{{ tag }}</ElTag>
            </ElSpace>
          </div>
        </button>
      </div>

      <div v-else-if="!loading" class="media-empty">
        <ElEmpty description="暂无公开文娱记录" />
      </div>
    </ElCard>

    <ElDrawer v-model="drawerVisible" :title="selectedItem?.title || '文娱详情'" size="560px">
      <template v-if="selectedItem">
        <div class="media-detail">
          <img v-if="selectedItem.cover_file?.url" :src="selectedItem.cover_file.url" :alt="selectedItem.title" class="media-detail__cover" >
          <ElSpace wrap>
            <ElTag>{{ 主分类标签映射[selectedItem.media_type] || selectedItem.media_type }}</ElTag>
            <ElTag type="info">{{ 状态标签映射[selectedItem.status] || selectedItem.status }}</ElTag>
            <ElTag v-if="selectedItem.rating" type="warning">{{ selectedItem.rating }} 分</ElTag>
          </ElSpace>
          <div v-if="selectedItem.original_title" class="media-detail__original">{{ selectedItem.original_title }}</div>
          <div v-if="selectedItem.creator" class="media-detail__section">
            <h3>创作者</h3>
            <p>{{ selectedItem.creator }}</p>
          </div>
          <div v-if="selectedItem.genres.length > 0" class="media-detail__section">
            <h3>子分类</h3>
            <ElSpace wrap>
              <ElTag v-for="genre in selectedItem.genres" :key="genre" effect="plain">{{ genre }}</ElTag>
            </ElSpace>
          </div>
          <div v-if="selectedItem.tags.length > 0" class="media-detail__section">
            <h3>标签</h3>
            <ElSpace wrap>
              <ElTag v-for="tag in selectedItem.tags" :key="tag" type="success" effect="plain">{{ tag }}</ElTag>
            </ElSpace>
          </div>
          <div v-if="selectedItem.summary" class="media-detail__section">
            <h3>简介</h3>
            <p>{{ selectedItem.summary }}</p>
          </div>
          <div v-if="selectedItem.description" class="media-detail__section">
            <h3>推荐语</h3>
            <p>{{ selectedItem.description }}</p>
          </div>
        </div>
      </template>
    </ElDrawer>
  </div>
</template>

<style scoped>
.media-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.media-shell {
  border-radius: 24px;
  border: 1px solid rgba(255, 255, 255, 0.45);
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(18px);
}

.dark .media-shell {
  border-color: rgba(148, 163, 184, 0.16);
  background: rgba(15, 23, 42, 0.72);
}

.media-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  margin-bottom: 16px;
}

.media-title {
  margin: 0;
  font-size: 32px;
}

.media-subtitle {
  margin: 8px 0 0;
  color: var(--text-secondary);
}

.media-filters {
  display: grid;
  grid-template-columns: minmax(220px, 1.6fr) repeat(2, minmax(120px, 0.8fr)) auto;
  gap: 12px;
  margin-bottom: 20px;
}

.media-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px;
}

.media-item {
  display: flex;
  flex-direction: column;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 20px;
  overflow: hidden;
  padding: 0;
  background: rgba(255, 255, 255, 0.82);
  cursor: pointer;
  text-align: left;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.dark .media-item {
  border-color: rgba(148, 163, 184, 0.16);
  background: rgba(15, 23, 42, 0.78);
}

.media-item:hover {
  transform: translateY(-4px);
  box-shadow: 0 20px 40px rgba(15, 23, 42, 0.12);
}

.media-item__cover-wrap {
  aspect-ratio: 3 / 4;
  background: linear-gradient(135deg, #f59e0b 0%, #f97316 100%);
}

.media-item__cover {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.media-item__cover--empty {
  display: grid;
  place-items: center;
  color: #fff;
  font-size: 56px;
  font-weight: 700;
}

.media-item__body {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 16px;
}

.media-item__meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.media-item__title {
  margin: 0;
  font-size: 20px;
}

.media-item__original,
.media-item__creator {
  color: var(--text-secondary);
  font-size: 14px;
}

.media-item__summary {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.65;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.media-empty {
  padding: 32px 0 8px;
}

.media-detail {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.media-detail__cover {
  width: 220px;
  max-width: 100%;
  border-radius: 16px;
  object-fit: cover;
}

.media-detail__original {
  color: var(--el-text-color-secondary);
}

.media-detail__section h3 {
  margin: 0 0 8px;
  font-size: 16px;
}

.media-detail__section p {
  margin: 0;
  line-height: 1.75;
}

@media (max-width: 768px) {
  .media-filters {
    grid-template-columns: 1fr;
  }

  .media-header {
    flex-direction: column;
  }
}
</style>
