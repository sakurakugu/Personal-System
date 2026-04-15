<script setup lang="ts">
import { ElEmpty } from 'element-plus'
import { computed, onMounted, ref } from 'vue'
import { fetchAllArticleMeta } from '../../../features/articles/api'
import type { ArticleMetaRecord } from '../../../features/articles/types'

const emit = defineEmits<{
  (e: 'click', slug: string): void
}>()

const archiveArticles = ref<ArticleMetaRecord[]>([])
const archiveLoading = ref(false)

const archiveGroups = computed(() => {
  const map: Record<number, ArticleMetaRecord[]> = {}
  archiveArticles.value.forEach(post => {
    if (!post.published_at) return
    const year = new Date(post.published_at).getFullYear()
    if (!map[year]) map[year] = []
    map[year].push(post)
  })
  return Object.keys(map)
    .map(y => ({ year: Number(y), posts: map[Number(y)] }))
    .sort((a, b) => b.year - a.year)
})

function formatArchiveDate(dateStr: string) {
  const d = new Date(dateStr)
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${month}-${day}`
}

function formatArchiveTags(tags: ArticleMetaRecord['tags']) {
  return tags.map(t => `#${t.name}`).join(' ')
}

async function loadArchiveData() {
  if (archiveArticles.value.length > 0) return
  archiveLoading.value = true
  try {
    const list = await fetchAllArticleMeta()
    archiveArticles.value = list.sort((a, b) => {
      const ta = a.published_at ? new Date(a.published_at).getTime() : 0
      const tb = b.published_at ? new Date(b.published_at).getTime() : 0
      return tb - ta
    })
  } catch {
    archiveArticles.value = []
  } finally {
    archiveLoading.value = false
  }
}

onMounted(() => {
  void loadArchiveData()
})
</script>

<template>
  <div class="archive-view">
    <div v-loading="archiveLoading" class="archive-content">
      <div v-if="!archiveLoading && archiveGroups.length === 0" class="empty-state">
        <ElEmpty description="暂无文章" />
      </div>

      <div
        v-for="group in archiveGroups"
        :key="group.year"
        class="year-group"
      >
        <div class="year-header">
          <div class="year-number">{{ group.year }}</div>
          <div class="year-dot" />
          <div class="year-count">{{ group.posts.length }} 篇文章</div>
        </div>

        <div class="post-list">
          <div
            v-for="post in group.posts"
            :key="post.id"
            class="post-item"
            @click="emit('click', post.slug)"
          >
            <div class="post-date">{{ formatArchiveDate(post.published_at!) }}</div>
            <div class="post-line">
              <div class="post-dot" />
            </div>
            <div class="post-title">{{ post.title }}</div>
            <div class="post-tags">{{ formatArchiveTags(post.tags) }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.archive-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.archive-content {
  background: var(--card-bg-transparent);
  border: 1px solid rgba(255, 255, 255, 0.45);
  backdrop-filter: blur(18px);
  border-radius: var(--radius-large);
  padding: 20px 24px;
  box-shadow: 0 10px 30px rgba(148, 163, 184, 0.14);
  transition: transform 0.2s, box-shadow 0.2s, background-color 0.2s, border-color 0.2s;
}

.dark .archive-content {
  border-color: rgba(148, 163, 184, 0.16);
  box-shadow: 0 12px 28px rgba(2, 6, 23, 0.28);
}

.is-overlay-mode .archive-content {
  background: rgba(255, 255, 255, var(--overlay-card-opacity));
}

.dark .blog-home.is-overlay-mode .archive-content {
  background: rgba(15, 23, 42, var(--overlay-card-opacity));
}

.year-group + .year-group {
  margin-top: 20px;
}

.year-header {
  display: flex;
  flex-direction: row;
  align-items: center;
  height: 3rem;
}

.year-number {
  width: 15%;
  text-align: right;
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--text-secondary);
  transition: color 0.2s;
}

.year-dot {
  width: 15%;
  display: flex;
  justify-content: center;
}

.year-dot::before {
  content: '';
  width: 0.625rem;
  height: 0.625rem;
  border-radius: 9999px;
  background: transparent;
  outline: 3px solid var(--primary);
  outline-offset: -2px;
}

.year-count {
  width: 70%;
  text-align: left;
  color: var(--text-secondary);
  font-size: 14px;
  transition: color 0.2s;
}

.post-item {
  display: flex;
  flex-direction: row;
  align-items: center;
  height: 2.25rem;
  width: 100%;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: background-color 0.15s;
}

.post-item:hover {
  background: var(--btn-plain-bg-hover, rgba(0, 0, 0, 0.05));
}

.post-item:hover .post-title {
  color: var(--primary);
  transform: translateX(4px);
}

.post-item:hover .post-dot {
  height: 1rem;
  background: var(--primary);
}

.post-date {
  width: 15%;
  text-align: right;
  font-size: 0.875rem;
  color: var(--text-secondary);
  transition: color 0.2s;
}

.post-line {
  width: 15%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.post-line::before {
  content: '';
  position: absolute;
  top: 0;
  bottom: 0;
  left: 50%;
  width: 1px;
  background: repeating-linear-gradient(
    to bottom,
    var(--line-divider) 0,
    var(--line-divider) 4px,
    transparent 4px,
    transparent 8px
  );
  transform: translateX(-50%);
}

.year-group:first-of-type .post-list .post-item:first-child .post-line::before {
  top: 50%;
}

.year-group:last-of-type .post-list .post-item:last-child .post-line::before {
  bottom: 50%;
}

.post-dot {
  width: 0.25rem;
  height: 0.25rem;
  border-radius: 9999px;
  background: oklch(0.5 0.05 var(--hue));
  outline: 4px solid rgba(255, 255, 255, 0.68);
  z-index: 10;
  transition: all 0.2s;
}

.dark .post-dot {
  outline-color: rgba(15, 23, 42, 0.62);
}

.post-title {
  width: 70%;
  padding-right: 1rem;
  text-align: left;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: all 0.2s;
}

.post-tags {
  display: none;
}

.empty-state {
  min-height: 240px;
  display: flex;
  align-items: center;
  justify-content: center;
}

@media (min-width: 768px) {
  .year-number {
    width: 10%;
  }
  .year-dot {
    width: 10%;
  }
  .year-count {
    width: 80%;
  }
  .post-date {
    width: 10%;
  }
  .post-line {
    width: 10%;
  }
  .post-title {
    width: 65%;
    padding-right: 2rem;
  }
  .post-tags {
    display: block;
    width: 15%;
    text-align: left;
    font-size: 0.875rem;
    color: var(--text-tertiary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    transition: color 0.2s;
  }
  .post-item:hover .post-tags {
    color: var(--primary);
  }
}

@media (max-width: 640px) {
  .archive-content {
    padding: 16px 16px;
  }
}
</style>
