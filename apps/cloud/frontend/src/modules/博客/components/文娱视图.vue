<script setup lang="ts">
import {
  MediaRating,
  最大评分等级,
  获取公开文娱列表,
  获取评分展示,
  type MediaRecord,
  type MediaStatus,
  type MediaType,
} from '@personal-system/module-media'
import { ElCard, ElEmpty, ElSpace, ElTag } from 'element-plus'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import BaseDrawer from '../../../shared/components/BaseDrawer.vue'

const loading = ref(false)
const activeType = ref<MediaType | ''>('anime')
const activeStatus = ref<MediaStatus | ''>('')
const items = ref<MediaRecord[]>([])
const 全量条目 = ref<MediaRecord[]>([])
const 全部数据最后更新时间 = ref('')
const selectedItem = ref<MediaRecord | null>(null)
const drawerVisible = ref(false)
const 分类栏滚动容器 = ref<globalThis.HTMLElement | null>(null)
const 分类栏正在拖动 = ref(false)
const 分类栏阻止点击 = ref(false)
const 分类栏起始横坐标 = ref(0)
const 分类栏起始滚动位置 = ref(0)
const route = useRoute()
const 搜索关键词 = computed(() => {
  return typeof route.query.search === 'string' ? route.query.search.trim() : ''
})

const 主分类选项: Array<{ label: string, value: MediaType }> = [
  { label: '动画', value: 'anime' },
  { label: '游戏', value: 'game' },
  { label: '小说', value: 'novel' },
  { label: '书籍', value: 'book' },
  { label: '漫画', value: 'comic' },
  { label: '电影', value: 'movie' },
  { label: '剧集', value: 'tv' },
  { label: '音乐', value: 'music' },
  { label: '其他', value: 'other' },
]

const 状态选项: Array<{ label: string, value: MediaStatus | '' }> = [
  { label: '全部', value: '' },
  { label: '已完成', value: 'done' },
  { label: '进行中', value: 'doing' },
  { label: '想看 / 想玩 / 想读', value: 'planned' },
  { label: '搁置', value: 'paused' },
  { label: '弃坑', value: 'dropped' },
]

const 状态标签映射 = computed<Record<string, string>>(() => Object.fromEntries(状态选项.map((item) => [item.value, item.label])))
const 主分类标签映射 = computed<Record<string, string>>(() => Object.fromEntries(主分类选项.map((item) => [item.value, item.label])))

const 当前分类列表 = computed(() => items.value)
const 分类数量映射 = computed<Record<string, number>>(() => {
  const counts: Record<string, number> = {}
  for (const item of 全量条目.value) {
    counts[item.media_type] = (counts[item.media_type] || 0) + 1
  }
  return counts
})
const 当前分类全量条目 = computed(() => 全量条目.value.filter((item) => item.media_type === activeType.value))
const 状态数量映射 = computed<Record<string, number>>(() => {
  const counts: Record<string, number> = {}
  for (const item of 当前分类全量条目.value) {
    counts[item.status] = (counts[item.status] || 0) + 1
  }
  return counts
})
const 状态筛选项 = computed(() => 状态选项.filter((item) => item.value === '' || (状态数量映射.value[item.value] || 0) > 0))

function 格式化日期时间(value: string) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return ''
  }
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1)
  const day = String(date.getDate())
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const seconds = String(date.getSeconds()).padStart(2, '0')
  return `${year}年${month}月${day}日 ${hours}:${minutes}:${seconds}`
}

async function 加载列表() {
  loading.value = true
  try {
    const [summaryResponse, listResponse] = await Promise.all([
      获取公开文娱列表({
        page: 1,
        page_size: 100,
        keyword: 搜索关键词.value,
      }),
      获取公开文娱列表({
        page: 1,
        page_size: 48,
        media_type: activeType.value,
        status: activeStatus.value,
        keyword: 搜索关键词.value,
      }),
    ])
    全量条目.value = summaryResponse.items
    items.value = listResponse.items
    全部数据最后更新时间.value = summaryResponse.all_data_updated_at ? 格式化日期时间(summaryResponse.all_data_updated_at) : ''
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

function 详情抽屉离场后处理() {
  selectedItem.value = null
}

function 获取评分摘要(rating: number) {
  return 获取评分展示(rating).summaryText
}

function 获取摘要(item: MediaRecord) {
  return item.description || item.summary || '暂未填写简介。'
}

function 获取状态徽标颜色(status: MediaStatus) {
  switch (status) {
    case 'planned':
      return '#3b82f6'
    case 'doing':
      return '#22c55e'
    case 'done':
      return '#f59e0b'
    case 'paused':
      return '#64748b'
    case 'dropped':
      return '#ef4444'
    default:
      return '#6b7280'
  }
}

function 选择分类(type: MediaType, event?: globalThis.MouseEvent) {
  if (分类栏阻止点击.value) {
    event?.preventDefault()
    event?.stopPropagation()
    分类栏阻止点击.value = false
    return
  }
  activeType.value = type
}

function 选择状态(status: MediaStatus | '') {
  activeStatus.value = status
}

function 开始拖动分类栏(event: globalThis.MouseEvent) {
  if (event.button !== 0 && event.button !== 1) {
    return
  }
  const container = 分类栏滚动容器.value
  if (!container) {
    return
  }
  分类栏正在拖动.value = false
  分类栏起始横坐标.value = event.clientX
  分类栏起始滚动位置.value = container.scrollLeft
  container.classList.add('media-tabs-scroll--dragging')
  window.addEventListener('mousemove', 拖动分类栏)
  window.addEventListener('mouseup', 结束拖动分类栏)
  if (event.button === 1) {
    event.preventDefault()
  }
}

function 拖动分类栏(event: globalThis.MouseEvent) {
  const container = 分类栏滚动容器.value
  if (!container) {
    return
  }
  const 位移 = event.clientX - 分类栏起始横坐标.value
  if (Math.abs(位移) > 4) {
    分类栏正在拖动.value = true
  }
  container.scrollLeft = 分类栏起始滚动位置.value - 位移
  if (分类栏正在拖动.value) {
    event.preventDefault()
  }
}

function 结束拖动分类栏() {
  const container = 分类栏滚动容器.value
  if (container) {
    container.classList.remove('media-tabs-scroll--dragging')
  }
  window.removeEventListener('mousemove', 拖动分类栏)
  window.removeEventListener('mouseup', 结束拖动分类栏)
  if (分类栏正在拖动.value) {
    分类栏阻止点击.value = true
    window.setTimeout(() => {
      分类栏阻止点击.value = false
    }, 0)
  }
}

function 处理分类栏滚轮(event: globalThis.WheelEvent) {
  const container = 分类栏滚动容器.value
  if (!container) {
    return
  }
  const 横向位移 = Math.abs(event.deltaX) > Math.abs(event.deltaY) ? event.deltaX : event.deltaY
  if (横向位移 === 0) {
    return
  }
  const 已滚到最左侧 = container.scrollLeft <= 0
  const 已滚到最右侧 = container.scrollLeft + container.clientWidth >= container.scrollWidth - 1
  if ((横向位移 < 0 && 已滚到最左侧) || (横向位移 > 0 && 已滚到最右侧)) {
    return
  }
  event.preventDefault()
  container.scrollLeft += 横向位移
}

watch([activeType, activeStatus], () => {
  void 加载列表()
})

watch(搜索关键词, () => {
  void 加载列表()
})

onMounted(() => {
  void 加载列表()
})

onBeforeUnmount(() => {
  window.removeEventListener('mousemove', 拖动分类栏)
  window.removeEventListener('mouseup', 结束拖动分类栏)
})
</script>

<template>
  <div class="media-view">
    <ElCard shadow="never" class="media-shell">
      <div class="media-shell__inner">
        <div class="header-wrap">
          <div class="header-title-row">
            <span class="header-title-bar" aria-hidden="true" />
            <h1 class="header-title">文娱推荐</h1>
          </div>
          <p class="header-desc">推荐文娱列表，集中展示看过、玩过、读过或者被推荐的作品</p>
          <p v-if="全部数据最后更新时间" class="header-updated-at">数据更新于 {{ 全部数据最后更新时间 }}</p>
        </div>

        <div
          ref="分类栏滚动容器"
          class="media-tabs-scroll"
          @mousedown="开始拖动分类栏"
          @wheel="处理分类栏滚轮"
        >
          <div class="media-tabs">
            <button
              v-for="item in 主分类选项"
              :key="item.value"
              type="button"
              class="media-tab"
              :class="{ 'media-tab--active': activeType === item.value }"
              @click="选择分类(item.value, $event)"
            >
              {{ item.label }}
              <span class="media-tab__count">{{ 分类数量映射[item.value] || 0 }}</span>
            </button>
          </div>
        </div>

        <div class="media-filters">
          <button
            v-for="item in 状态筛选项"
            :key="item.value || 'all'"
            type="button"
            class="media-filter"
            :class="{ 'media-filter--active': activeStatus === item.value }"
            @click="选择状态(item.value)"
          >
            {{ item.label }}
            <span v-if="item.value" class="media-filter__count">({{ 状态数量映射[item.value] || 0 }})</span>
            <span v-else class="media-filter__count">({{ 当前分类全量条目.length }})</span>
          </button>
        </div>

        <div v-if="loading" class="media-empty">
          <div class="media-empty__text">正在加载公开文娱记录…</div>
        </div>

        <div v-else-if="当前分类列表.length > 0" class="media-grid">
          <button
            v-for="item in 当前分类列表"
            :key="item.id"
            type="button"
            class="media-card"
            @click="打开详情(item)"
          >
            <div class="media-card__cover">
              <img
                v-if="item.cover_file?.thumbnail_url || item.cover_file?.url"
                :src="item.cover_file?.thumbnail_url || item.cover_file?.url || ''"
                :alt="item.title"
                class="media-card__image"
              >
              <div v-else class="media-card__image media-card__image--empty">📖</div>

              <div class="media-card__status" :style="{ backgroundColor: 获取状态徽标颜色(item.status) }">
                {{ 状态标签映射[item.status] || item.status }}
              </div>

              <div v-if="item.rating" class="media-card__score">
                <MediaRating :rating="item.rating" compact />
              </div>

              <div class="media-card__overlay" />

              <div class="media-card__content">
                <h2 class="media-card__title">{{ item.title }}</h2>
                <p v-if="item.creator" class="media-card__meta">{{ item.creator }}</p>
                <p v-if="item.original_title" class="media-card__meta">{{ item.original_title }}</p>
                <p class="media-card__comment" :title="获取摘要(item)">{{ 获取摘要(item) }}</p>
                <div v-if="item.genres.length > 0 || item.tags.length > 0" class="media-card__tags">
                  <span v-for="genre in item.genres.slice(0, 3)" :key="genre" class="media-card__tag">{{ genre }}</span>
                  <span v-for="tag in item.tags.slice(0, 3)" :key="tag" class="media-card__tag">{{ tag }}</span>
                </div>
              </div>
            </div>
          </button>
        </div>

        <div v-else class="media-empty">
          <ElEmpty description="暂无公开文娱记录" />
        </div>
      </div>
    </ElCard>

    <BaseDrawer
      v-model="drawerVisible"
      :title="selectedItem?.title || '文娱详情'"
      :aria-label="selectedItem?.title || '文娱详情'"
      anchor-selector="#top-row"
      theme-source-selector=".blog-home"
      @after-leave="详情抽屉离场后处理"
    >
      <template #header>
        <h2 class="media-detail-drawer__title">{{ selectedItem?.title || '文娱详情' }}</h2>
        <button
          type="button"
          class="media-detail-drawer__close"
          aria-label="关闭详情"
          @click="drawerVisible = false"
        >
          ×
        </button>
      </template>

      <div v-if="selectedItem" class="media-detail">
        <img
          v-if="selectedItem.cover_file?.url || selectedItem.cover_file?.thumbnail_url"
          :src="selectedItem.cover_file?.url || selectedItem.cover_file?.thumbnail_url || ''"
          :alt="selectedItem.title"
          class="media-detail__cover"
        >
        <div v-else class="media-detail__cover media-detail__cover--empty">📖</div>

        <ElSpace wrap>
          <ElTag>{{ 主分类标签映射[selectedItem.media_type] || selectedItem.media_type }}</ElTag>
          <ElTag type="info">{{ 状态标签映射[selectedItem.status] || selectedItem.status }}</ElTag>
          <ElTag v-if="selectedItem.rating" type="warning">{{ 获取评分摘要(selectedItem.rating) }}</ElTag>
        </ElSpace>

        <div v-if="selectedItem.original_title" class="media-detail__text media-detail__text--muted">{{ selectedItem.original_title }}</div>
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
        <div v-if="selectedItem.rating" class="media-detail__section">
          <h3>评分</h3>
          <div class="media-detail__rating">
            <MediaRating :rating="selectedItem.rating" show-text />
            <span class="media-detail__rating-text">{{ selectedItem.rating }} / {{ 最大评分等级 }} 级</span>
          </div>
        </div>
      </div>
    </BaseDrawer>
  </div>
</template>

<style scoped>
.media-view {
  display: flex;
  flex-direction: column;
}

.media-shell {
  border: none;
  background: transparent;
}

.media-shell :deep(.el-card__body) {
  padding: 0;
}

.media-shell__inner {
  width: 100%;
  padding: 24px 36px;
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 16px;
  background: var(--card-bg, #ffffff);
  transition: background-color 0.15s ease, border-color 0.15s ease;
}

.dark .media-shell__inner {
  border-color: rgba(255, 255, 255, 0.08);
}

.header-wrap {
  margin-bottom: 1rem;
}

.header-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0;
  font-weight: 700;
  font-size: 1.125rem;
  color: var(--text-primary);
  border-bottom: none;
  margin-top: 16px;
  margin-bottom: 0.75rem;
}

.header-title-bar {
  flex: 0 0 auto;
  width: 4px;
  height: 16px;
  border-radius: 2px;
  background: var(--primary, var(--el-color-primary));
}

.header-title {
  margin: 0;
  font-size: 1.125rem;
  font-weight: 700;
  color: var(--text-primary);
}

.header-desc {
  margin: 0;
  font-size: 1rem;
  color: var(--text-secondary);
  line-height: 1.625;
}

.header-updated-at {
  margin: 0.3rem 0 0.35rem;
  font-size: 0.875rem;
  color: var(--el-text-color-secondary);
  line-height: 1.5;
}

.media-tabs-scroll {
  width: 100%;
  margin-bottom: 12px;
  overflow-x: auto;
  overflow-y: hidden;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
  cursor: grab;
}

.media-tabs-scroll::-webkit-scrollbar {
  display: none;
}

.media-tabs-scroll--dragging {
  cursor: grabbing;
  user-select: none;
}

.media-tabs {
  display: flex;
  width: max-content;
  min-width: 100%;
  gap: 28px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
}

.dark .media-tabs {
  border-bottom-color: rgba(255, 255, 255, 0.08);
}

.media-tab {
  display: inline-flex;
  align-items: center;
  padding: 10px 1px;
  border: none;
  border-bottom: 2px solid transparent;
  background: transparent;
  color: #6b7280;
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
  cursor: pointer;
  transition: color 0.2s ease, border-color 0.2s ease;
}

.dark .media-tab {
  color: #9ca3af;
}

.media-tab:hover {
  color: #374151;
}

.dark .media-tab:hover {
  color: #d1d5db;
}

.media-tab--active {
  border-bottom-color: var(--el-color-primary);
  color: var(--el-color-primary);
}

.media-tab__count {
  min-width: 22px;
  margin-left: 8px;
  padding: 1px 5px;
  border-radius: 6px;
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  font-size: 12px;
  line-height: 1.2;
  text-align: center;
}

.dark .media-tab__count {
  background: color-mix(in srgb, var(--el-color-primary) 18%, transparent);
  color: var(--el-color-primary-light-3);
}

.media-tab--active .media-tab__count {
  color: inherit;
}

.media-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 20px;
}

.media-filter {
  padding: 5px 10px;
  border: none;
  border-radius: 8px;
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s ease, color 0.2s ease;
}

.dark .media-filter {
  background: color-mix(in srgb, var(--el-color-primary) 18%, transparent);
  color: var(--el-color-primary-light-3);
}

.media-filter:hover {
  background: var(--el-color-primary-light-8);
}

.media-filter--active {
  background: var(--el-color-primary);
  color: #fff;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.22);
}

.media-filter__count {
  margin-left: 2px;
}

.media-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

@media (min-width: 640px) {
  .media-grid {
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  }
}

.media-card {
  display: block;
  overflow: hidden;
  padding: 0;
  border: none;
  border-radius: 12px;
  background: transparent;
  text-align: left;
  cursor: pointer;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.media-card:hover {
  transform: scale(1.02);
  box-shadow: 0 16px 32px rgba(0, 0, 0, 0.14);
}

.media-card__cover {
  position: relative;
  overflow: hidden;
  aspect-ratio: 2 / 3;
  border-radius: 12px;
}

.media-card__image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  pointer-events: none;
  transition: transform 0.5s ease;
}

.media-card:hover .media-card__image {
  transform: scale(1.05);
}

.media-card__image--empty {
  display: flex;
  align-items: center;
  justify-content: center;
  background: #e5e7eb;
  color: #9ca3af;
  font-size: 40px;
}

.dark .media-card__image--empty {
  background: #374151;
  color: #d1d5db;
}

.media-card__status {
  position: absolute;
  top: 8px;
  left: 8px;
  padding: 4px 8px;
  border-radius: 999px;
  color: #fff;
  font-size: 12px;
  font-weight: 500;
}

.media-card__score {
  position: absolute;
  top: 8px;
  right: 8px;
  display: flex;
  align-items: center;
  padding: 4px 8px;
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  color: #fff;
}

.media-card__overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0.2), transparent);
}

.media-card__content {
  position: absolute;
  right: 0;
  bottom: 0;
  left: 0;
  padding: 12px;
}

.media-card__title {
  display: -webkit-box;
  margin: 0;
  overflow: hidden;
  color: #fff;
  font-size: 13px;
  font-weight: 700;
  line-height: 1.4;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.media-card__meta {
  margin: 4px 0 0;
  color: rgba(255, 255, 255, 0.6);
  font-size: 12px;
}

.media-card__comment {
  display: -webkit-box;
  margin: 4px 0 0;
  overflow: hidden;
  color: rgba(255, 255, 255, 0.75);
  font-size: 12px;
  line-height: 1.5;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 1;
}

.media-card__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 6px;
}

.media-card__tag {
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.2);
  color: rgba(255, 255, 255, 0.9);
  font-size: 10px;
  backdrop-filter: blur(4px);
}

.media-empty {
  padding: 48px 0;
  text-align: center;
}

.media-empty__text {
  color: rgba(107, 114, 128, 0.9);
}

.dark .media-empty__text {
  color: rgba(156, 163, 175, 0.9);
}

.media-detail {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.media-detail__cover {
  width: 220px;
  max-width: 100%;
  border-radius: 12px;
  object-fit: cover;
}

.media-detail__cover--empty {
  display: flex;
  align-items: center;
  justify-content: center;
  aspect-ratio: 2 / 3;
  background: #e5e7eb;
  color: #9ca3af;
  font-size: 48px;
}

.dark .media-detail__cover--empty {
  background: #374151;
  color: #d1d5db;
}

.media-detail__text {
  font-size: 14px;
}

.media-detail__text--muted {
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

.media-detail__rating {
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--text-primary);
}

.media-detail__rating-text {
  color: var(--el-text-color-secondary);
  font-size: 14px;
}

.media-detail :deep(.el-tag) {
  border-radius: 4px;
}

.media-detail-drawer__title {
  margin: 0;
  color: var(--text-primary);
  font-size: 20px;
  font-weight: 700;
  line-height: 1.4;
}

.media-detail-drawer__close {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  padding: 0;
  border: none;
  border-radius: 999px;
  background: transparent;
  color: var(--text-secondary);
  font-size: 22px;
  line-height: 1;
  cursor: pointer;
  transition: background-color 0.2s ease, color 0.2s ease;
}

.media-detail-drawer__close:hover {
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
}

@media (max-width: 768px) {
  .media-shell__inner {
    padding: 18px;
  }

  .header-title-row {
    margin-bottom: 0.625rem;
  }

  .header-title {
    font-size: 1.125rem;
  }
}
</style>
