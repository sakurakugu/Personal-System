<script setup lang="ts">
import { Icon } from '@iconify/vue'
import { ElMessage } from 'element-plus'
import { onMounted, ref } from 'vue'
import { fetchFeedList, type FeedArticleRecord, type FeedItemRecord } from '@personal-system/module-blog/feed'
import { 解析当前API基地址 } from '../../../shared/api/runtime'

const 默认线上接口基址 = 'https://api.sakurakugu.top/v1'

function isAbsoluteHttpUrl(value: string): boolean {
  return /^https?:\/\//i.test(value)
}

function normalizeBaseUrl(value: string): string {
  return value.trim().replace(/\/+$/, '')
}

function resolveRssUrl(): string {
  const configuredServerBase =
    import.meta.env.VITE_SERVER_API_BASE?.trim()
    || import.meta.env.VITE_PRODUCTION_API_BASE?.trim()
  const currentApiBase = normalizeBaseUrl(解析当前API基地址())

  if (configuredServerBase) {
    return `${normalizeBaseUrl(configuredServerBase)}/rss.xml`
  }

  if (isAbsoluteHttpUrl(currentApiBase)) {
    return `${currentApiBase}/rss.xml`
  }

  if (import.meta.env.DEV) {
    return new window.URL(`${currentApiBase}/rss.xml`, window.location.origin).toString()
  }

  return `${默认线上接口基址}/rss.xml`
}

const rssUrl = resolveRssUrl()
const recentPosts = ref<FeedArticleRecord[]>([])

async function loadRecentPosts() {
  try {
    const data = await fetchFeedList(1, {})
    recentPosts.value = data.items
      .filter((item: FeedItemRecord) => item.type === 'article' && item.article)
      .slice(0, 6)
      .map((item: FeedItemRecord) => item.article!)
  } catch {
    recentPosts.value = []
  }
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

async function copyRssUrl() {
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(rssUrl)
    } else {
      const textarea = document.createElement('textarea')
      textarea.value = rssUrl
      textarea.style.position = 'fixed'
      textarea.style.left = '-9999px'
      document.body.appendChild(textarea)
      textarea.focus()
      textarea.select()
      const successful = document.execCommand('copy')
      document.body.removeChild(textarea)
      if (!successful) throw new Error('execCommand copy failed')
    }
    ElMessage.success('RSS 链接已复制到剪贴板！')
  } catch {
    ElMessage.error('复制失败，请手动复制链接')
  }
}

onMounted(() => {
  void loadRecentPosts()
})
</script>

<template>
  <div class="rss-view">
    <!-- RSS 标题和介绍 -->
    <div class="rss-card rss-header">
      <div class="rss-header-inner">
        <div class="rss-icon-wrap">
          <Icon icon="material-symbols:rss-feed" class="rss-icon" />
        </div>
        <div class="rss-title">RSS 订阅</div>
        <p class="rss-subtitle">
          通过 RSS 订阅，第一时间获取最新文章和动态
        </p>
      </div>
    </div>

    <!-- RSS 链接复制区域 -->
    <div class="rss-card rss-link-card">
      <div class="rss-link-row">
        <div class="rss-link-info">
          <div class="rss-link-icon-wrap">
            <Icon icon="material-symbols:link" class="rss-link-icon" />
          </div>
          <div class="rss-link-text">
            <h3 class="rss-link-title">RSS 链接</h3>
            <p class="rss-link-desc">复制链接到你的 RSS 阅读器</p>
          </div>
        </div>
        <div class="rss-link-actions">
          <code class="rss-url-code">{{ rssUrl }}</code>
          <button
            class="rss-copy-btn"
            @click="copyRssUrl"
          >
            复制链接
          </button>
        </div>
      </div>
    </div>

    <!-- 最新文章预览 -->
    <div class="rss-card rss-posts-card">
      <h2 class="rss-section-title">
        <Icon icon="material-symbols:article" class="rss-section-icon" />
        最新文章
      </h2>
      <div class="rss-posts-list">
        <article
          v-for="post in recentPosts"
          :key="post.id"
          class="rss-post-item"
        >
          <h3 class="rss-post-title">
            <router-link :to="`/blog/${post.slug}`" class="rss-post-link">
              {{ post.title }}
            </router-link>
          </h3>
          <p v-if="post.excerpt" class="rss-post-excerpt">
            {{ post.excerpt }}
          </p>
          <div class="rss-post-meta">
            <time :datetime="post.published_at || post.created_at">
              {{ formatDate(post.published_at) }}
            </time>
          </div>
        </article>
      </div>
    </div>

    <!-- RSS 说明 -->
    <div class="rss-card rss-about-card">
      <h2 class="rss-section-title">
        <Icon icon="material-symbols:help-outline" class="rss-section-icon" />
        什么是 RSS？
      </h2>
      <div class="rss-about-body">
        <p>
          RSS（Really Simple Syndication）是一种用于发布经常更新内容的标准格式。通过 RSS，你可以：
        </p>
        <ul class="rss-benefit-list">
          <li>及时获取网站最新内容，无需手动访问</li>
          <li>在一个地方管理多个网站的订阅</li>
          <li>避免错过重要更新和文章</li>
          <li>享受无广告的纯净阅读体验</li>
        </ul>
        <p class="rss-about-tip">
          推荐使用 Feedly、Inoreader 或其他 RSS 阅读器来订阅本站。
        </p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.rss-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.rss-card {
  background: var(--card-bg-transparent);
  border-radius: var(--radius-large);
  border: 1px solid rgba(255, 255, 255, 0.45);
  backdrop-filter: blur(18px);
  box-shadow: 0 10px 30px rgba(148, 163, 184, 0.14);
  padding: 24px 28px;
  transition: transform 0.2s, box-shadow 0.2s, background-color 0.2s, border-color 0.2s;
}

.rss-card:hover {
  box-shadow: 0 18px 34px rgba(148, 163, 184, 0.18);
}

.dark .rss-card {
  border-color: rgba(148, 163, 184, 0.16);
  box-shadow: 0 12px 28px rgba(2, 6, 23, 0.28);
}

.dark .rss-card:hover {
  box-shadow: 0 18px 34px rgba(2, 6, 23, 0.35);
}

/* 标题区域 */
.rss-header {
  text-align: center;
  padding: 32px 28px;
}

.rss-icon-wrap {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 64px;
  height: 64px;
  background: var(--el-color-primary);
  border-radius: 16px;
  margin-bottom: 16px;
}

.rss-icon {
  width: 32px;
  height: 32px;
  color: #fff;
}

.rss-title {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.rss-subtitle {
  color: var(--text-secondary);
  max-width: 36rem;
  margin: 0 auto;
  line-height: 1.6;
}

/* 链接复制区域 */
.rss-link-row {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.rss-link-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.rss-link-icon-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  background: var(--el-color-primary);
  border-radius: 12px;
  flex-shrink: 0;
}

.rss-link-icon {
  width: 24px;
  height: 24px;
  color: #fff;
}

.rss-link-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 2px;
}

.rss-link-desc {
  font-size: 0.875rem;
  color: var(--text-secondary);
  margin: 0;
}

.rss-link-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.rss-url-code {
  display: block;
  background: var(--card-bg);
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 0.875rem;
  font-family: monospace;
  color: var(--text-secondary);
  border: 1px solid var(--line-divider);
  word-break: break-all;
}

.rss-copy-btn {
  padding: 8px 16px;
  color: #fff;
  background: var(--el-color-primary);
  border: none;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: opacity 0.2s;
  white-space: nowrap;
}

.rss-copy-btn:hover {
  opacity: 0.85;
}

/* 最新文章 */
.rss-section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 1.125rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 16px;
}

.rss-section-icon {
  width: 20px;
  height: 20px;
  color: var(--el-color-primary);
}

.rss-posts-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.rss-post-item {
  background: var(--card-bg);
  border-radius: 12px;
  padding: 16px;
  border: 1px solid var(--line-divider);
  transition: border-color 0.3s;
}

.rss-post-item:hover {
  border-color: var(--el-color-primary);
}

.rss-post-title {
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 6px;
}

.rss-post-link {
  color: var(--text-primary);
  text-decoration: none;
  transition: color 0.2s;
}

.rss-post-link:hover {
  color: var(--el-color-primary);
  text-decoration: underline;
}

.rss-post-excerpt {
  font-size: 0.875rem;
  color: var(--text-secondary);
  margin: 0 0 8px;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.rss-post-meta {
  font-size: 0.8rem;
  color: var(--text-tertiary);
}

/* 说明区域 */
.rss-about-body {
  color: var(--text-secondary);
  line-height: 1.7;
}

.rss-about-body p {
  margin: 0 0 10px;
}

.rss-benefit-list {
  list-style: disc;
  padding-left: 1.5rem;
  margin: 0 0 10px;
}

.rss-benefit-list li {
  margin-bottom: 4px;
}

.rss-about-tip {
  font-size: 0.8rem;
  color: var(--text-tertiary);
  margin: 0;
}

/* 桌面端布局 */
@media (min-width: 768px) {
  .rss-link-row {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
  }

  .rss-link-actions {
    flex-direction: row;
    align-items: center;
    min-width: 0;
  }

  .rss-url-code {
    flex: 1;
    min-width: 0;
  }
}

@media (max-width: 576px) {
  .rss-card {
    padding: 16px;
  }

  .rss-title {
    font-size: 1.5rem;
  }

  .rss-header {
    padding: 24px 16px;
  }
}
</style>
