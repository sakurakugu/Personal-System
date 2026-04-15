<script setup lang="ts">
/* global fetch */
import { Icon } from '@iconify/vue'
import { ElEmpty, ElSkeleton } from 'element-plus'
import { computed, onMounted, reactive, ref } from 'vue'
import { bangumiConfig, type BangumiCategoryConfig, type BangumiCategoryId } from '../../../constants/bangumiConfig'

interface BangumiSubject {
  id: number
  name: string
  name_cn?: string
  date?: string
  eps?: number
  images?: {
    small?: string
    grid?: string
    large?: string
    common?: string
  }
}

interface BangumiCollectionItem {
  subject_id: number
  type: number
  rate?: number
  comment?: string
  updated_at?: string
  subject: BangumiSubject
}

interface BangumiCollectionResponse {
  data?: BangumiCollectionItem[]
}

const enabledCategories = computed(() => bangumiConfig.categories.filter(category => category.enabled))
const activeTab = ref<BangumiCategoryId | ''>('')
const loading = ref(false)
const errorMessage = ref('')
const dataMap = reactive<Record<BangumiCategoryId, BangumiCollectionItem[]>>({
  anime: [],
  book: [],
  music: [],
  game: [],
  real: [],
})

const isUserConfigured = computed(() => bangumiConfig.userId.trim().length > 0)

const activeCategory = computed<BangumiCategoryConfig | undefined>(() => {
  return enabledCategories.value.find(category => category.id === activeTab.value)
})

const activeItems = computed(() => {
  if (!activeTab.value) return []
  return dataMap[activeTab.value]
})

function getCoverUrl(item: BangumiCollectionItem) {
  return item.subject.images?.common
    || item.subject.images?.large
    || item.subject.images?.grid
    || item.subject.images?.small
    || ''
}

function getCollectionStatus(type: number) {
  if (type === 1) return '想看'
  if (type === 2) return '看过'
  if (type === 3) return '在看'
  if (type === 4) return '搁置'
  if (type === 5) return '抛弃'
  return '未知'
}

function formatDate(date?: string) {
  if (!date) return '未知时间'
  const parsed = new Date(date)
  if (Number.isNaN(parsed.getTime())) return date
  return parsed.toLocaleDateString('zh-CN')
}

function formatUpdatedAt(updatedAt?: string) {
  if (!updatedAt) return ''
  const parsed = new Date(updatedAt)
  if (Number.isNaN(parsed.getTime())) return ''
  return parsed.toLocaleDateString('zh-CN')
}

async function fetchCategoryData(category: BangumiCategoryConfig) {
  const url = `${bangumiConfig.apiBaseUrl}/v0/users/${encodeURIComponent(bangumiConfig.userId)}/collections?subject_type=${category.subjectType}&limit=${bangumiConfig.requestLimit}`
  const response = await fetch(url, {
    headers: {
      Accept: 'application/json',
    },
  })
  if (!response.ok) {
    throw new Error(`请求失败(${response.status})`)
  }
  const payload = await response.json() as BangumiCollectionResponse
  dataMap[category.id] = Array.isArray(payload.data) ? payload.data : []
}

async function loadBangumiData() {
  if (!isUserConfigured.value) return
  loading.value = true
  errorMessage.value = ''
  try {
    const categories = enabledCategories.value
    await Promise.all(categories.map(category => fetchCategoryData(category)))
  } catch {
    errorMessage.value = 'Bangumi 数据加载失败，请稍后重试。'
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  activeTab.value = enabledCategories.value[0]?.id || ''
  await loadBangumiData()
})
</script>

<template>
  <div class="bangumi-view">
    <div class="bangumi-card">
      <div class="bangumi-header">
        <div class="bangumi-title-wrap">
          <div class="bangumi-title-icon">
            <Icon icon="material-symbols:movie-outline" />
          </div>
          <div>
            <h1 class="bangumi-title">追番记录</h1>
            <p class="bangumi-subtitle">同步 Bangumi 个人收藏，集中展示动画、书籍、音乐与游戏记录。</p>
          </div>
        </div>
      </div>

      <div v-if="!isUserConfigured" class="bangumi-empty-wrap">
        <ElEmpty description="尚未配置 Bangumi 用户名">
          <template #description>
            <p class="bangumi-empty-text">请在 src/constants/bangumiConfig.ts 中填写 userId 后刷新页面。</p>
          </template>
        </ElEmpty>
      </div>

      <template v-else>
        <div class="bangumi-tabs" role="tablist" aria-label="Bangumi 分类">
          <button
            v-for="tab in enabledCategories"
            :key="tab.id"
            type="button"
            class="bangumi-tab"
            :class="{ active: activeTab === tab.id }"
            role="tab"
            :aria-selected="activeTab === tab.id"
            @click="activeTab = tab.id"
          >
            <span>{{ tab.name }}</span>
            <span class="tab-count">{{ dataMap[tab.id].length }}</span>
          </button>
        </div>

        <p v-if="activeCategory" class="bangumi-section-hint">
          当前分类：{{ activeCategory.name }}，共 {{ activeItems.length }} 条记录
        </p>

        <div v-if="loading" class="bangumi-loading">
          <ElSkeleton :rows="8" animated />
        </div>

        <div v-else-if="errorMessage" class="bangumi-empty-wrap">
          <ElEmpty :description="errorMessage" />
        </div>

        <div v-else-if="activeItems.length === 0" class="bangumi-empty-wrap">
          <ElEmpty description="当前分类暂无数据" />
        </div>

        <div v-else class="bangumi-grid">
          <article v-for="item in activeItems" :key="item.subject_id" class="bangumi-item">
            <img
              v-if="getCoverUrl(item)"
              :src="getCoverUrl(item)"
              :alt="item.subject.name_cn || item.subject.name"
              class="item-cover"
              loading="lazy"
            >
            <div v-else class="item-cover item-cover--placeholder">
              <Icon icon="material-symbols:hide-image-outline" />
            </div>

            <div class="item-content">
              <h3 class="item-title" :title="item.subject.name_cn || item.subject.name">
                {{ item.subject.name_cn || item.subject.name }}
              </h3>
              <p v-if="item.subject.name_cn && item.subject.name_cn !== item.subject.name" class="item-subtitle" :title="item.subject.name">
                {{ item.subject.name }}
              </p>

              <div class="item-meta-list">
                <span class="meta-chip">状态：{{ getCollectionStatus(item.type) }}</span>
                <span v-if="item.rate" class="meta-chip">评分：{{ item.rate }}/10</span>
                <span v-if="item.subject.eps" class="meta-chip">集数：{{ item.subject.eps }}</span>
                <span class="meta-chip">首发：{{ formatDate(item.subject.date) }}</span>
                <span v-if="formatUpdatedAt(item.updated_at)" class="meta-chip">更新：{{ formatUpdatedAt(item.updated_at) }}</span>
              </div>

              <p v-if="item.comment" class="item-comment">{{ item.comment }}</p>
            </div>
          </article>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.bangumi-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.bangumi-card {
  background: var(--card-bg-transparent);
  border-radius: var(--radius-large);
  border: 1px solid rgba(255, 255, 255, 0.45);
  backdrop-filter: blur(18px);
  box-shadow: 0 10px 30px rgba(148, 163, 184, 0.14);
  padding: 24px 28px;
}

.dark .bangumi-card {
  border-color: rgba(148, 163, 184, 0.16);
  box-shadow: 0 12px 28px rgba(2, 6, 23, 0.28);
}

.is-overlay-mode .bangumi-card {
  background: rgba(255, 255, 255, var(--overlay-card-opacity));
}

.dark .blog-home.is-overlay-mode .bangumi-card {
  background: rgba(15, 23, 42, var(--overlay-card-opacity));
}

.bangumi-header {
  margin-bottom: 16px;
}

.bangumi-title-wrap {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.bangumi-title-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: var(--primary);
  color: #ffffff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 1.3rem;
  flex-shrink: 0;
}

.dark .bangumi-title-icon {
  color: rgba(0, 0, 0, 0.75);
}

.bangumi-title {
  margin: 0;
  color: var(--text-primary);
  font-size: 1.6rem;
  line-height: 1.3;
}

.bangumi-subtitle {
  margin: 6px 0 0;
  color: var(--text-secondary);
  line-height: 1.6;
  font-size: 0.95rem;
}

.bangumi-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 10px;
}

.bangumi-tab {
  border: 1px solid var(--line-divider);
  background: transparent;
  color: var(--btn-content);
  border-radius: 999px;
  padding: 6px 12px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.bangumi-tab:hover {
  border-color: var(--primary);
  color: var(--primary);
}

.bangumi-tab.active {
  border-color: var(--primary);
  background: var(--primary);
  color: #ffffff;
}

.tab-count {
  font-size: 0.75rem;
  opacity: 0.8;
}

.bangumi-section-hint {
  margin: 0 0 14px;
  font-size: 0.86rem;
  color: var(--text-tertiary);
}

.bangumi-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.bangumi-item {
  border-radius: 14px;
  border: 1px solid var(--line-divider);
  background: rgba(255, 255, 255, 0.5);
  display: grid;
  grid-template-columns: 98px 1fr;
  overflow: hidden;
}

.dark .bangumi-item {
  background: rgba(15, 23, 42, 0.42);
}

.item-cover {
  width: 100%;
  height: 100%;
  min-height: 146px;
  object-fit: cover;
  background: rgba(148, 163, 184, 0.15);
}

.item-cover--placeholder {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--text-tertiary);
  font-size: 1.5rem;
}

.item-content {
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.item-title {
  margin: 0;
  color: var(--text-primary);
  font-size: 1rem;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.item-subtitle {
  margin: 4px 0 0;
  color: var(--text-tertiary);
  font-size: 0.8rem;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.item-meta-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 10px;
}

.meta-chip {
  border-radius: 8px;
  padding: 3px 8px;
  font-size: 0.74rem;
  line-height: 1.2;
  background: var(--btn-regular-bg);
  color: var(--btn-content);
}

.item-comment {
  margin: 8px 0 0;
  color: var(--text-secondary);
  font-size: 0.82rem;
  line-height: 1.45;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.bangumi-empty-wrap {
  padding: 14px 0 4px;
}

.bangumi-empty-text {
  color: var(--text-secondary);
}

.bangumi-loading {
  margin-top: 8px;
}

@media (max-width: 960px) {
  .bangumi-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 576px) {
  .bangumi-card {
    padding: 16px;
  }

  .bangumi-item {
    grid-template-columns: 88px 1fr;
  }

  .item-cover {
    min-height: 132px;
  }
}
</style>