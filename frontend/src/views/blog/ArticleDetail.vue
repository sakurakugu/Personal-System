<script setup lang="ts">
import { View } from '@element-plus/icons-vue'
import { ElButton, ElCard, ElDivider, ElEmpty, ElIcon, ElInput, ElMessage, ElSkeleton, ElSpace, ElTag, ElText } from 'element-plus'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'
import MarkdownIt from 'markdown-it'
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useArticleStore } from '../../stores/article'
import { useAuthStore } from '../../stores/auth'
import api from '../../utils/api'

const route = useRoute()
const articleStore = useArticleStore()
const auth = useAuthStore()

const md = new MarkdownIt({
  html: true,
  linkify: true,
  highlight(str: string, lang: string) {
    if (lang && hljs.getLanguage(lang)) {
      try { return hljs.highlight(str, { language: lang }).value } catch {}
    }
    return ''
  },
})

interface Comment {
  id: string
  content: string
  user: { username: string; nickname: string | null } | null
  guest_name: string | null
  created_at: string
  replies: Comment[]
}

interface TocItem {
  id: string
  text: string
  level: number
}

const comments = ref<Comment[]>([])
const newComment = ref('')
const guestName = ref('')
const loadingComment = ref(false)
const loadingCommentsConfig = ref(true)
const commentsEnabled = ref(true)
const commentsStealth = ref(false)
const toc = ref<TocItem[]>([])

const renderedContent = computed(() => {
  if (!articleStore.current) return ''
  return md.render(articleStore.current.content)
})

// 解析文章目录
function parseToc(content: string) {
  const items: TocItem[] = []
  const lines = content.split('\n')
  let idCounter = 0

  for (const line of lines) {
    const match = line.match(/^(#{2,3})\s+(.+)$/)
    if (match) {
      const level = match[1]?.length || 2
      const text = match[2]?.replace(/\*\*/g, '').replace(/\*/g, '').replace(/`/g, '') || ''
      items.push({
        id: `heading-${idCounter++}`,
        text,
        level,
      })
    }
  }
  return items
}

// 为渲染后的内容添加锚点
function addAnchorsToContent() {
  nextTick(() => {
    const container = window.document.querySelector('.markdown-body')
    if (!container) return

    const headings = container.querySelectorAll('h2, h3')
    toc.value.forEach((item, index) => {
      const heading = headings[index]
      if (heading) {
        heading.id = item.id
      }
    })
  })
}

function scrollToSection(id: string) {
  const element = window.document.getElementById(id)
  if (element) {
    element.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

onMounted(async () => {
  const slug = route.params.slug as string
  await loadCommentsConfig()
  await articleStore.fetchBySlug(slug)
  if (articleStore.current) {
    toc.value = parseToc(articleStore.current.content)
    addAnchorsToContent()
    await loadComments()
    try { await api.post('/stats/pageview', { path: `/blog/${slug}`, article_id: articleStore.current.id }) } catch {}
  }
})

// 当文章内容更新时重新生成目录
watch(() => articleStore.current?.content, (newContent) => {
  if (newContent) {
    toc.value = parseToc(newContent)
    addAnchorsToContent()
  }
})

async function loadComments() {
  if (!articleStore.current || !commentsEnabled.value) return
  try {
    const { data } = await api.get('/comments', { params: { article_id: articleStore.current.id } })
    comments.value = data
  } catch {}
}

async function submitComment() {
  if (!articleStore.current || !newComment.value.trim() || !commentsEnabled.value) return
  loadingComment.value = true
  try {
    await api.post('/comments', {
      article_id: articleStore.current.id,
      content: newComment.value,
      guest_name: auth.isAuthenticated ? undefined : (guestName.value || '匿名'),
    })
    newComment.value = ''
    ElMessage.success('评论已提交')
    await loadComments()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '评论失败')
  } finally {
    loadingComment.value = false
  }
}

async function loadCommentsConfig() {
  try {
    const { data } = await api.get('/admin/public-settings')
    commentsEnabled.value = data.comments_enabled
    commentsStealth.value = data.comments_stealth
  } catch {
    commentsEnabled.value = true
    commentsStealth.value = false
  } finally {
    loadingCommentsConfig.value = false
  }
}
</script>

<template>
  <div class="article-detail">
    <!-- 左侧栏 -->
    <aside class="sidebar-left">
      <ElCard class="sidebar-card">
        <div class="back-section">
          <router-link to="/blog" class="back-link">
            ← 返回文章列表
          </router-link>
        </div>
      </ElCard>

      <ElCard v-if="toc.length > 0" header="📑 文章目录" class="sidebar-card">
        <div class="toc-list">
          <a
            v-for="item in toc"
            :key="item.id"
            :href="`#${item.id}`"
            class="toc-item"
            :class="{ 'toc-h2': item.level === 2, 'toc-h3': item.level === 3 }"
            @click.prevent="scrollToSection(item.id)"
          >
            {{ item.text }}
          </a>
        </div>
      </ElCard>
    </aside>

    <!-- 中间主内容区 -->
    <main class="main-area">
      <ElSkeleton :loading="articleStore.loading" animated>
        <template v-if="articleStore.current">
          <ElCard>
            <h1 class="title">{{ articleStore.current.title }}</h1>
            <div class="meta">
              <ElSpace size="small" alignment="center">
                <ElText type="info">{{ articleStore.current.author.nickname || articleStore.current.author.username }}</ElText>
                <ElText type="info">·</ElText>
                <ElText type="info">{{ new Date(articleStore.current.published_at || articleStore.current.created_at).toLocaleDateString() }}</ElText>
                <ElText type="info" style="display: inline-flex; align-items: center; gap: 4px">
                  <span>·</span>
                  <ElIcon><View /></ElIcon>
                  <span>{{ articleStore.current.view_count }}</span>
                </ElText>
              </ElSpace>
              <ElSpace size="small" style="margin-top: 8px">
                <ElTag v-if="articleStore.current.category" type="info" size="small">{{ articleStore.current.category.name }}</ElTag>
                <ElTag v-for="tag in articleStore.current.tags" :key="tag.id" size="small">{{ tag.name }}</ElTag>
              </ElSpace>
            </div>

            <ElDivider />

            <div class="markdown-body" v-html="renderedContent" />
          </ElCard>

          <!-- 评论区 -->
          <ElCard v-if="!loadingCommentsConfig && commentsEnabled" header="评论" style="margin-top: 24px">
            <div v-if="comments.length" class="comment-list">
              <div v-for="c in comments" :key="c.id" class="comment-item">
                <div class="comment-header">
                  <ElText tag="b">{{ c.user?.nickname || c.user?.username || c.guest_name || '匿名' }}</ElText>
                  <ElText type="info" style="font-size: 12px; margin-left: 8px">{{ new Date(c.created_at).toLocaleString() }}</ElText>
                </div>
                <p class="comment-content">{{ c.content }}</p>
                <div v-if="c.replies?.length" class="replies">
                  <div v-for="r in c.replies" :key="r.id" class="comment-item reply">
                    <div class="comment-header">
                      <ElText tag="b">{{ r.user?.nickname || r.user?.username || r.guest_name || '匿名' }}</ElText>
                      <ElText type="info" style="font-size: 12px; margin-left: 8px">{{ new Date(r.created_at).toLocaleString() }}</ElText>
                    </div>
                    <p class="comment-content">{{ r.content }}</p>
                  </div>
                </div>
              </div>
            </div>
            <ElEmpty v-else description="暂无评论，来抢沙发吧！" />

            <ElDivider />

            <div class="comment-form">
              <ElInput
                v-if="!auth.isAuthenticated"
                v-model="guestName"
                placeholder="你的名字（可选）"
                style="margin-bottom: 8px"
              />
              <ElInput
                v-model="newComment"
                type="textarea"
                placeholder="写下你的评论..."
                :rows="3"
              />
              <ElButton
                type="primary"
                style="margin-top: 8px"
                :loading="loadingComment"
                @click="submitComment"
              >
                发表评论
              </ElButton>
            </div>
          </ElCard>
          <ElCard v-else-if="!loadingCommentsConfig && !commentsStealth" header="评论" style="margin-top: 24px">
            <ElEmpty description="评论功能已关闭" />
          </ElCard>
        </template>
        <ElEmpty v-else-if="!articleStore.loading" description="文章不存在" />
      </ElSkeleton>
    </main>

    <!-- 右侧栏 -->
    <aside class="sidebar-right">
      <ElCard class="sidebar-card">
        <div class="profile-section">
          <div class="avatar">
            <img src="https://free.picui.cn/free/2026/03/17/69b8f1dd8a75e.jpg" alt="头像.jpg" title="头像.jpg">
          </div>
          <h3 class="profile-name">Sakurakugu</h3>
          <p class="profile-desc">一个喜欢折腾代码的开发者</p>
        </div>
      </ElCard>

      <ElCard v-if="articleStore.current?.tags?.length" header="🏷️ 本文标签" class="sidebar-card">
        <div class="tag-list">
          <ElTag
            v-for="tag in articleStore.current.tags"
            :key="tag.id"
            size="small"
            class="tag-item"
          >
            {{ tag.name }}
          </ElTag>
        </div>
      </ElCard>
    </aside>
  </div>
</template>

<style scoped>
/* 三栏布局 */
.article-detail {
  display: grid;
  grid-template-columns: 240px 1fr 240px;
  gap: 24px;
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px 16px;
}

/* 左侧栏 */
.sidebar-left {
  position: sticky;
  top: 80px;
  height: fit-content;
}

/* 右侧栏 */
.sidebar-right {
  position: sticky;
  top: 80px;
  height: fit-content;
}

/* 侧边栏卡片通用样式 */
.sidebar-card {
  margin-bottom: 16px;
  border-radius: 12px;
}

.sidebar-card :deep(.el-card__header) {
  font-weight: 600;
  font-size: 14px;
  padding-bottom: 12px;
}

/* 返回链接 */
.back-section {
  padding: 8px 0;
}

.back-link {
  display: flex;
  align-items: center;
  color: #555;
  text-decoration: none;
  font-size: 14px;
  transition: color 0.2s;
}

.back-link:hover {
  color: #18a058;
}

/* 文章目录 */
.toc-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.toc-item {
  display: block;
  padding: 6px 10px;
  border-radius: 6px;
  color: #555;
  text-decoration: none;
  font-size: 13px;
  transition: all 0.2s;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.toc-item:hover {
  background: #f5f7fa;
  color: #18a058;
}

.toc-h2 {
  font-weight: 500;
}

.toc-h3 {
  padding-left: 20px;
  font-size: 12px;
  color: #777;
}

/* 个人信息区 */
.profile-section {
  text-align: center;
  padding: 8px 0;
}

.avatar {
  width: 60px;
  height: 60px;
  margin: 0 auto 10px;
  border-radius: 50%;
  overflow: hidden;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.profile-name {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 4px;
  color: #333;
}

.profile-desc {
  font-size: 12px;
  color: #888;
}

/* 标签列表 */
.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag-item {
  cursor: default;
}

/* 主内容区 */
.main-area {
  min-width: 0;
}

.title {
  font-size: 28px;
  margin-bottom: 12px;
  line-height: 1.4;
}

.meta {
  margin-bottom: 8px;
}

.markdown-body {
  line-height: 1.8;
  font-size: 15px;
}

.markdown-body :deep(pre) {
  background: #f6f8fa;
  padding: 16px;
  border-radius: 6px;
  overflow-x: auto;
}

.markdown-body :deep(code) {
  background: #f0f0f0;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 13px;
}

.markdown-body :deep(pre code) {
  background: none;
  padding: 0;
}

.markdown-body :deep(img) {
  max-width: 100%;
  border-radius: 4px;
}

.markdown-body :deep(h2),
.markdown-body :deep(h3) {
  scroll-margin-top: 80px;
}

.comment-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.comment-item {
  padding: 12px;
  background: #f9f9f9;
  border-radius: 8px;
}

.comment-header {
  margin-bottom: 4px;
}

.comment-content {
  font-size: 14px;
  color: #444;
  margin: 0;
}

.replies {
  margin-top: 12px;
  padding-left: 20px;
  border-left: 2px solid #e0e0e0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.reply {
  background: #f0f4f0;
}

/* 响应式布局 */
@media (max-width: 1200px) {
  .article-detail {
    grid-template-columns: 200px 1fr 200px;
    gap: 16px;
  }
}

@media (max-width: 992px) {
  .article-detail {
    grid-template-columns: 1fr;
    max-width: 800px;
  }

  .sidebar-left,
  .sidebar-right {
    position: static;
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 16px;
  }

  .sidebar-card {
    margin-bottom: 0;
  }
}

@media (max-width: 576px) {
  .article-detail {
    padding: 16px 12px;
  }

  .title {
    font-size: 22px;
  }

  .sidebar-left,
  .sidebar-right {
    grid-template-columns: 1fr;
  }
}
</style>
