<script setup lang="ts">
import { ElButton, ElCheckbox, ElEmpty, ElTag } from 'element-plus'
import type { ArticleImageRecord } from '../../types'

type 文章图片列表项 = ArticleImageRecord & {
  isUsed: boolean
}

const props = defineProps<{
  expanded: boolean
  currentArticleId: string
  loading: boolean
  deleting: boolean
  items: 文章图片列表项[]
  desktopSummary: string
  mobileSummary: string
  selectedIds: string[]
  unusedCount: number
  resolvePreviewUrl: (image: 文章图片列表项) => string
  formatSize: (bytes: number) => string
  formatTime: (value: string) => string
}>()

const emit = defineEmits<{
  toggle: []
  refresh: []
  'select-all-unused': []
  'clear-selection': []
  'delete-selected': []
  'selection-change': [imageId: string, checked: boolean]
}>()
</script>

<template>
  <section class="article-image-panel">
    <div class="article-image-panel__header">
      <div
        class="article-image-panel__header-main"
        :class="{ 'is-expanded': expanded }"
      >
        <div class="article-image-panel__header-info">
          <div class="article-image-panel__title">文章图片</div>
          <div class="article-image-panel__header-summary article-image-panel__header-summary--desktop">
            {{ desktopSummary }}
          </div>
          <div class="article-image-panel__header-summary article-image-panel__header-summary--mobile">
            {{ mobileSummary }}
          </div>
        </div>
        <div v-if="expanded" class="article-image-panel__actions">
          <ElButton size="small" :disabled="!currentArticleId || loading" @click="emit('refresh')">
            刷新
          </ElButton>
          <ElButton
            size="small"
            :disabled="unusedCount === 0 || deleting"
            @click="emit('select-all-unused')"
          >
            选中未使用
          </ElButton>
          <ElButton
            size="small"
            :disabled="selectedIds.length === 0"
            @click="emit('clear-selection')"
          >
            清空选择
          </ElButton>
          <ElButton
            size="small"
            type="danger"
            :loading="deleting"
            :disabled="selectedIds.length === 0"
            @click="emit('delete-selected')"
          >
            删除选中未使用图片
          </ElButton>
        </div>
        <ElButton class="article-image-panel__toggle" size="small" @click="emit('toggle')">
          {{ expanded ? '收起' : '展开' }}
        </ElButton>
      </div>
    </div>

    <div v-if="expanded && !currentArticleId" class="article-image-panel__placeholder">
      首次上传正文图片时会自动创建草稿，随后这里会显示该文章的全部图片，并标记哪些图片当前未被正文或封面引用。
    </div>

    <div v-else-if="expanded && loading && items.length === 0" class="article-image-panel__placeholder">
      正在加载文章图片...
    </div>

    <ElEmpty v-else-if="expanded && items.length === 0" description="当前文章还没有上传图片" />

    <div v-else-if="expanded" class="article-image-grid">
      <article
        v-for="image in items"
        :key="image.id"
        class="article-image-card"
        :class="{
          'is-used': image.isUsed,
          'is-selected': selectedIds.includes(image.id),
        }"
      >
        <div class="article-image-card__toolbar">
          <ElCheckbox
            v-if="!image.isUsed"
            :model-value="selectedIds.includes(image.id)"
            @change="emit('selection-change', image.id, Boolean($event))"
          >
            选择删除
          </ElCheckbox>
          <span v-else class="article-image-card__locked-tip">当前已被正文或封面引用</span>
          <ElTag :type="image.isUsed ? 'success' : 'warning'" size="small">
            {{ image.isUsed ? '已使用' : '未使用' }}
          </ElTag>
        </div>

        <div class="article-image-card__preview">
          <img :src="resolvePreviewUrl(image)" :alt="image.original_name">
        </div>

        <div class="article-image-card__body">
          <div class="article-image-card__name" :title="image.original_name">{{ image.original_name }}</div>
          <div class="article-image-card__meta">
            <span>{{ formatSize(image.size) }}</span>
            <span>{{ formatTime(image.created_at) }}</span>
          </div>
          <div class="article-image-card__hint">
            {{ image.isUsed ? '保留中：当前正文或封面仍在引用这张图片' : '可清理：当前正文和封面都没引用这张图片' }}
          </div>
        </div>
      </article>
    </div>
  </section>
</template>

<style scoped>
@import '@personal-system/ui/styles/media.css';

.article-image-panel {
  display: grid;
  gap: 16px;
  margin-bottom: 24px;
  padding: 18px;
  border: 1px solid var(--el-border-color-light);
  border-radius: 16px;
  background:
    linear-gradient(180deg, color-mix(in srgb, var(--el-color-success-light-9) 34%, transparent), transparent 42%),
    var(--el-bg-color-overlay);
}

.article-image-panel__header {
  display: grid;
  gap: 12px;
}

.article-image-panel__header-main {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: nowrap;
  min-width: 0;
}

.article-image-panel__header-info {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1 1 auto;
  min-width: 0;
}

.article-image-panel__title {
  flex: 0 0 auto;
  font-size: 16px;
  font-weight: 700;
  color: var(--el-text-color-primary);
}

.article-image-panel__header-summary {
  flex: 1 1 auto;
  min-width: 0;
}

.article-image-panel__header-summary--mobile {
  display: none;
}

.article-image-panel__header-summary,
.article-image-panel__placeholder {
  color: var(--el-text-color-secondary);
  font-size: 13px;
  line-height: 1.6;
}

.article-image-panel__actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: nowrap;
  flex: 0 0 auto;
}

.article-image-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px;
}

.article-image-card {
  display: grid;
  gap: 12px;
  padding: 12px;
  border: 1px solid var(--el-border-color-light);
  border-radius: 14px;
  background: var(--el-bg-color);
  transition:
    transform 0.18s ease,
    border-color 0.18s ease,
    box-shadow 0.18s ease;
}

.article-image-card.is-used {
  border-color: color-mix(in srgb, var(--el-color-success) 34%, var(--el-border-color-light));
}

.article-image-card.is-selected {
  border-color: var(--el-color-danger);
  box-shadow: 0 10px 24px rgba(245, 108, 108, 0.16);
}

.article-image-card:hover {
  transform: translateY(-2px);
}

.article-image-card__toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.article-image-card__locked-tip {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.article-image-card__preview {
  overflow: hidden;
  aspect-ratio: 16 / 10;
  border-radius: 10px;
  background:
    linear-gradient(135deg, var(--theme-accent-overlay-10), color-mix(in srgb, var(--el-color-primary-light-3) 12%, transparent)),
    var(--el-fill-color-light);
}

.article-image-card__preview img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.article-image-card__body {
  display: grid;
  gap: 8px;
}

.article-image-card__name {
  color: var(--el-text-color-primary);
  font-weight: 600;
  line-height: 1.5;
  word-break: break-all;
}

.article-image-card__meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

.article-image-card__hint {
  color: var(--el-text-color-regular);
  font-size: 12px;
  line-height: 1.6;
}

@media (--mobile-viewport) {
  .article-image-panel {
    padding: 14px;
  }

  .article-image-panel__actions {
    width: 100%;
    flex-wrap: wrap;
    order: 3;
  }

  .article-image-panel__header-main {
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
  }

  .article-image-panel__header-info {
    align-items: center;
    justify-content: space-between;
    flex: 1 1 auto;
    min-width: 0;
    gap: 12px;
  }

  .article-image-panel__header-main.is-expanded .article-image-panel__header-info {
    flex: 1 1 calc(100% - 96px);
  }

  .article-image-panel__header-summary--desktop {
    display: none;
  }

  .article-image-panel__header-summary--mobile {
    display: block;
    order: 2;
    width: 100%;
    text-align: center;
  }

  .article-image-panel__actions :deep(.el-button) {
    flex: 1 1 calc(50% - 8px);
    min-width: 0;
    margin-left: 0;
  }

  .article-image-grid {
    grid-template-columns: 1fr;
  }
}
</style>
