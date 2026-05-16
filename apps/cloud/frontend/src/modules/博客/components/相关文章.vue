<script setup lang="ts">
import { Icon } from '@iconify/vue'
import type { ArticleMetaRecord } from '@personal-system/module-articles'

const props = defineProps<{
  relatedArticles: ArticleMetaRecord[]
  randomArticles: ArticleMetaRecord[]
}>()

const emit = defineEmits<{
  articleClick: [slug: string]
}>()

// function getAuthorName(post: ArticleMetaRecord): string {
//   return post.author.nickname || post.author.username
// }
</script>

<template>
  <div class="article-related">
    <!-- 相关文章 -->
    <div v-if="props.relatedArticles.length" class="related-card">
      <div class="related-header">
        <div class="related-title">
          <Icon icon="material-symbols:signpost" class="related-icon" />
          <span>相关文章</span>
        </div>
        <span class="related-badge">智能推荐</span>
      </div>
      <div
        v-for="(post, idx) in props.relatedArticles"
        :key="post.id"
        class="related-item"
        :class="{ bordered: idx < props.relatedArticles.length - 1 }"
        @click="emit('articleClick', post.slug)"
      >
        <div class="related-num">{{ idx + 1 }}</div>
        <div class="related-body">
          <div class="related-item-title">{{ post.title }}</div>
          <div class="related-item-meta">
            <span v-if="post.category" class="related-cat">{{ post.category.name }}</span>
            <!-- <span class="related-inline-meta">
              <Icon icon="material-symbols:person-outline-rounded" />
              <span>{{ getAuthorName(post) }}</span>
            </span> -->
            <span class="related-inline-meta">
              <Icon icon="material-symbols:favorite-outline-rounded" />
              <span>{{ post.like_count }}</span>
            </span>
            <span class="related-date">{{ post.published_at?.slice(0, 10) || '' }}</span>
          </div>
        </div>
        <Icon icon="material-symbols:chevron-right-rounded" class="related-arrow" />
      </div>
    </div>

    <!-- 随机文章 -->
    <div v-if="props.randomArticles.length" class="related-card">
      <div class="related-header">
        <div class="related-title">
          <Icon icon="material-symbols:recommend" class="related-icon" />
          <span>随机推荐</span>
        </div>
        <span class="related-badge">猜你喜欢</span>
      </div>
      <div
        v-for="(post, idx) in props.randomArticles"
        :key="post.id"
        class="related-item"
        :class="{ bordered: idx < props.randomArticles.length - 1 }"
        @click="emit('articleClick', post.slug)"
      >
        <div class="related-num">{{ idx + 1 }}</div>
        <div class="related-body">
          <div class="related-item-title">{{ post.title }}</div>
          <div class="related-item-meta">
            <span v-if="post.category" class="related-cat">{{ post.category.name }}</span>
            <!-- <span class="related-inline-meta">
              <Icon icon="material-symbols:person-outline-rounded" />
              <span>{{ getAuthorName(post) }}</span>
            </span> -->
            <span class="related-inline-meta">
              <Icon icon="material-symbols:favorite-outline-rounded" />
              <span>{{ post.like_count }}</span>
            </span>
            <span class="related-date">{{ post.published_at?.slice(0, 10) || '' }}</span>
          </div>
        </div>
        <Icon icon="material-symbols:chevron-right-rounded" class="related-arrow" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.article-related {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1rem;
  margin: 0;
}

.related-card {
  background: var(--card-bg-transparent);
  border: 1px solid rgba(255, 255, 255, 0.45);
  border-radius: 0.75rem;
  backdrop-filter: blur(18px);
  background-color: rgba(255, 255, 255, var(--overlay-card-opacity)) !important;
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  transition: transform var(--transition-base), box-shadow var(--transition-base), background-color var(--transition-base), border-color var(--transition-base);
}

.dark .related-card {
  border-color: rgba(148, 163, 184, 0.16);
  background-color: rgba(15, 23, 42, var(--overlay-card-opacity)) !important;
}

.related-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding-bottom: 0.75rem;
  margin-bottom: 0.25rem;
  border-bottom: 1px dashed var(--border-color);
}

.related-title {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  font-weight: 700;
  color: var(--text-primary);
}

.related-icon {
  font-size: 1.25rem;
  color: var(--el-color-primary);
}

.related-badge {
  margin-left: auto;
  font-size: 0.75rem;
  padding: 0.125rem 0.5rem;
  border-radius: 999px;
  background: var(--bg-hover);
  color: var(--text-secondary);
}

.related-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.625rem 0.5rem;
  margin: 0 -0.5rem;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: background var(--transition-base) ease;
}

.related-item:hover {
  background: rgba(255, 255, 255, 0.35);
}

.dark .related-item:hover {
  background: rgba(255, 255, 255, 0.06);
}

.related-item.bordered {
  border-bottom: 1px dashed var(--border-color);
}

.related-num {
  flex-shrink: 0;
  width: 1.5rem;
  height: 1.5rem;
  border-radius: 0.375rem;
  background: var(--bg-hover);
  color: var(--el-color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 700;
}

.related-body {
  min-width: 0;
  flex: 1;
}

.related-item-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: color var(--transition-base) ease;
}

.related-item:hover .related-item-title {
  color: var(--el-color-primary);
}

.related-item-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.375rem;
  margin-top: 0.125rem;
  font-size: 0.75rem;
  color: var(--text-tertiary);
}

.related-inline-meta {
  display: inline-flex;
  align-items: center;
  gap: 0.1875rem;
}

.related-inline-meta :deep(svg) {
  font-size: 0.875rem;
}

.related-cat {
  flex-shrink: 0;
  padding: 0.0625rem 0.375rem;
  border-radius: 0.25rem;
  background: rgba(0, 0, 0, 0.05);
  color: var(--text-secondary);
}

.dark .related-cat {
  background: rgba(255, 255, 255, 0.08);
}

.related-arrow {
  flex-shrink: 0;
  font-size: 1.25rem;
  color: var(--text-tertiary);
  transition: all var(--transition-base) ease;
}

.related-item:hover .related-arrow {
  color: var(--el-color-primary);
  transform: translateX(2px);
}
</style>
