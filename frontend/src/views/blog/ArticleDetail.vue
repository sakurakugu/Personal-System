<script setup lang="ts">
import { View } from '@element-plus/icons-vue'
import { ElButton, ElCard, ElDivider, ElEmpty, ElIcon, ElInput, ElMessage, ElSkeleton, ElSpace, ElTag, ElText } from 'element-plus'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'
import MarkdownIt from 'markdown-it'
import axios from 'axios'
import { computed, nextTick, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  createComment,
  deleteComment as removeComment,
  fetchComments,
  likeComment,
  unlikeComment,
} from '../../features/comments/api'
import type { CommentRecord } from '../../features/comments/types'
import { fetchPublicSettings, trackPageView } from '../../features/system/api'
import { useArticleStore } from '../../stores/article'
import { useAuthStore } from '../../stores/auth'
import { getApiErrorMessage } from '../../utils/api'

const route = useRoute()
const router = useRouter()
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

interface TocItem {
  id: string
  text: string
  level: number
}

const comments = ref<CommentRecord[]>([])
const newComment = ref('')
const guestName = ref('')
const loadingComment = ref(false)
const loadingCommentsConfig = ref(true)
const commentsEnabled = ref(true)
const commentsStealth = ref(false)
const commentsMinRole = ref('guest')
const toc = ref<TocItem[]>([])
const articleAccessDenied = ref(false)

const replyingTo = ref<string | null>(null)
const replyContent = ref('')
const replyGuestName = ref('')
const loadingReply = ref(false)
const replyingToComment = ref<CommentRecord | null>(null)

const renderedContent = computed(() => {
  if (!articleStore.current) return ''
  return md.render(articleStore.current.content)
})

const roleHierarchy: Record<string, number> = {
  guest: 0,
  user: 1,
  admin: 2,
  super_admin: 3,
}

const canViewComments = computed(() => {
  const minLevel = roleHierarchy[commentsMinRole.value] ?? 0
  const userLevel = roleHierarchy[auth.userRole || 'guest'] ?? 0
  return userLevel >= minLevel
})

const permissionMessage = computed(() => {
  const roleLabels: Record<string, string> = {
    guest: '所有人',
    user: '登录用户',
    admin: '管理员',
    super_admin: '超级管理员',
  }
  return `仅${roleLabels[commentsMinRole.value] || '特定用户'}可查看评论`
})

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

async function loadCommentsConfig() {
  loadingCommentsConfig.value = true
  try {
    const data = await fetchPublicSettings()
    commentsEnabled.value = data.comments_enabled
    commentsStealth.value = data.comments_stealth
    commentsMinRole.value = data.comments_min_role || 'guest'
  } catch {
    commentsEnabled.value = true
    commentsStealth.value = false
    commentsMinRole.value = 'guest'
  } finally {
    loadingCommentsConfig.value = false
  }
}

async function loadComments() {
  if (!articleStore.current || !commentsEnabled.value) return
  try {
    comments.value = await fetchComments(articleStore.current.id)
  } catch {
    comments.value = []
  }
}

async function loadArticlePage(slug: string) {
  comments.value = []
  toc.value = []
  replyingTo.value = null
  replyingToComment.value = null
  articleAccessDenied.value = false
  void loadCommentsConfig()
  try {
    await articleStore.fetchBySlug(slug)
  } catch (error) {
    if (axios.isAxiosError(error) && articleStore.currentErrorStatus === 401) {
      articleAccessDenied.value = true
      return
    }
    return
  }
  if (articleStore.current) {
    toc.value = parseToc(articleStore.current.content)
    addAnchorsToContent()
    await loadComments()
    try {
      await trackPageView({
        path: `/blog/${slug}`,
        article_id: articleStore.current.id,
      })
    } catch {}
  }
}

watch(() => articleStore.current?.content, (newContent) => {
  if (newContent) {
    toc.value = parseToc(newContent)
    addAnchorsToContent()
  }
})

watch(() => route.params.slug, (slug) => {
  if (typeof slug === 'string') {
    void loadArticlePage(slug)
  }
}, { immediate: true })

function showLoginModal() {
  router.push({ query: { ...route.query, login: '1' } })
}

async function submitComment() {
  if (!articleStore.current || !newComment.value.trim() || !commentsEnabled.value) return
  loadingComment.value = true
  try {
    await createComment({
      article_id: articleStore.current.id,
      content: newComment.value,
      guest_name: auth.isAuthenticated ? undefined : (guestName.value || '匿名'),
    })
    newComment.value = ''
    ElMessage.success('评论已提交')
    await loadComments()
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '评论失败'))
  } finally {
    loadingComment.value = false
  }
}

function getCommentDisplayName(comment: CommentRecord | null): string {
  if (!comment) return '匿名'
  return comment.user?.nickname || comment.user?.username || comment.guest_name || '匿名'
}

function getCommentUserKey(comment: CommentRecord): string {
  if (comment.user) {
    return comment.user.username
  }
  return comment.guest_name || '匿名'
}

function parseMentions(content: string): { type: 'text' | 'mention'; value: string }[] {
  const result: { type: 'text' | 'mention'; value: string }[] = []
  const mentionRegex = /@([^\s@]+)/g
  let lastIndex = 0
  let match

  while ((match = mentionRegex.exec(content)) !== null) {
    if (match.index > lastIndex) {
      result.push({ type: 'text', value: content.slice(lastIndex, match.index) })
    }
    result.push({ type: 'mention', value: match[1] })
    lastIndex = mentionRegex.lastIndex
  }

  if (lastIndex < content.length) {
    result.push({ type: 'text', value: content.slice(lastIndex) })
  }

  return result
}

function handleMentionClick(targetName: string, currentCommentId: string) {
  const allComments: CommentRecord[] = []
  
  for (const c of comments.value) {
    allComments.push(c)
    for (const r of c.replies || []) {
      allComments.push(r)
    }
  }

  const currentIndex = allComments.findIndex((item) => item.id === currentCommentId)
  if (currentIndex === -1) return

  for (let i = currentIndex - 1; i >= 0; i--) {
    const item = allComments[i]
    const itemName = getCommentUserKey(item)
    if (itemName === targetName) {
      const targetId = `comment-${item.id}`
      const element = document.getElementById(targetId)
      if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'center' })
        element.classList.add('comment-highlight')
        setTimeout(() => {
          element.classList.remove('comment-highlight')
        }, 2000)
      }
      return
    }
  }
  
  ElMessage.info(`未找到用户 ${targetName} 的 earlier 评论`)
}

function startReply(commentId: string) {
  replyingTo.value = commentId
  replyingToComment.value = findCommentById(commentId)
  replyGuestName.value = guestName.value
  replyContent.value = ''
}

function findCommentById(commentId: string): CommentRecord | null {
  for (const c of comments.value) {
    if (c.id === commentId) return c
    for (const r of c.replies || []) {
      if (r.id === commentId) return r
    }
  }
  return null
}

function cancelReply() {
  replyingTo.value = null
  replyingToComment.value = null
  replyContent.value = ''
}

async function submitReply(parentId: string) {
  if (!articleStore.current || !replyContent.value.trim() || !commentsEnabled.value) return
  loadingReply.value = true
  try {
    let content = replyContent.value.trim()
    if (replyingToComment.value?.reply_to_user) {
      const targetName = getCommentDisplayName(replyingToComment.value)
      content = `回复 @${targetName} ：${content}`
    }
    
    await createComment({
      article_id: articleStore.current.id,
      content,
      parent_id: parentId,
      guest_name: auth.isAuthenticated ? undefined : (replyGuestName.value || '匿名'),
    })
    replyContent.value = ''
    replyingTo.value = null
    replyingToComment.value = null
    ElMessage.success('回复已提交')
    await loadComments()
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '回复失败'))
  } finally {
    loadingReply.value = false
  }
}

function canDeleteComment(comment: CommentRecord): boolean {
  if (!auth.isAuthenticated) return false
  if (auth.userRole === 'admin' || auth.userRole === 'super_admin') return true
  return comment.user?.id === auth.user?.id
}

async function deleteComment(comment: CommentRecord) {
  const isReply = comment.reply_to_user !== null
  const confirmText = isReply ? '确定要删除这条回复吗？' : '确定要删除这条评论吗？相关回复也会被删除。'
  
  if (!confirm(confirmText)) return
  
  try {
    await removeComment(comment.id)
    ElMessage.success('删除成功')
    await loadComments()
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '删除失败'))
  }
}

async function toggleLike(comment: CommentRecord) {
  if (!auth.isAuthenticated) {
    showLoginModal()
    return
  }

  try {
    if (comment.is_liked) {
      await unlikeComment(comment.id)
      comment.is_liked = false
      comment.like_count = Math.max(0, comment.like_count - 1)
    } else {
      await likeComment(comment.id)
      comment.is_liked = true
      comment.like_count += 1
    }
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '操作失败'))
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
          <ElCard class="main-card">
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
          <ElCard v-if="!loadingCommentsConfig && commentsEnabled && canViewComments" class="main-card" header="评论" style="margin-top: 24px">
            <div v-if="comments.length" class="comment-list">
              <div v-for="c in comments" :id="`comment-${c.id}`" :key="c.id" class="comment-item">
                <div class="comment-header">
                  <ElText tag="b">{{ c.user?.nickname || c.user?.username || c.guest_name || '匿名' }}</ElText>
                  <ElText type="info" style="font-size: 12px; margin-left: 8px">{{ new Date(c.created_at).toLocaleString() }}</ElText>
                </div>
                <p class="comment-content">
                  <template v-for="(part, idx) in parseMentions(c.content)" :key="idx">
                    <span v-if="part.type === 'text'">{{ part.value }}</span>
                    <span
                      v-else
                      class="mention-link"
                      @click="handleMentionClick(part.value, c.id)"
                    >
                      @{{ part.value }}
                    </span>
                  </template>
                </p>
                
                <!-- 评论操作 -->
                <div class="comment-actions">
                  <ElButton 
                    link 
                    :type="c.is_liked ? 'danger' : 'info'" 
                    size="small" 
                    @click="toggleLike(c)"
                  >
                    <ElIcon style="margin-right: 4px">
                      <span v-if="c.is_liked">❤️</span>
                      <span v-else>🤍</span>
                    </ElIcon>
                    {{ c.like_count > 0 ? c.like_count : '点赞' }}
                  </ElButton>
                  <ElButton link type="primary" size="small" @click="startReply(c.id)">
                    回复
                  </ElButton>
                  <ElButton 
                    v-if="canDeleteComment(c)"
                    link 
                    type="danger" 
                    size="small" 
                    @click="deleteComment(c)"
                  >
                    删除
                  </ElButton>
                </div>
                
                <!-- 回复表单 -->
                <div v-if="replyingTo === c.id" class="reply-form">
                  <ElInput
                    v-if="!auth.isAuthenticated"
                    v-model="replyGuestName"
                    placeholder="你的昵称"
                    size="small"
                    style="margin-bottom: 8px; max-width: 200px"
                  />
                  <ElInput
                    v-model="replyContent"
                    type="textarea"
                    :placeholder="`回复 @${c.user?.nickname || c.user?.username || c.guest_name || '匿名'}...`"
                    :rows="2"
                  />
                  <div class="reply-actions">
                    <ElButton size="small" @click="cancelReply">取消</ElButton>
                    <ElButton type="primary" size="small" :loading="loadingReply" @click="submitReply(c.id)">
                      提交回复
                    </ElButton>
                  </div>
                </div>
                
                <div v-if="c.replies?.length" class="replies">
                  <div v-for="r in c.replies" :id="`comment-${r.id}`" :key="r.id" class="comment-item reply">
                    <div class="comment-header">
                      <ElText tag="b">{{ r.user?.nickname || r.user?.username || r.guest_name || '匿名' }}</ElText>
                      <ElText type="info" style="font-size: 12px; margin-left: 8px">{{ new Date(r.created_at).toLocaleString() }}</ElText>
                    </div>
                    <p class="comment-content">
                      <template v-for="(part, idx) in parseMentions(r.content)" :key="idx">
                        <span v-if="part.type === 'text'">{{ part.value }}</span>
                        <span
                          v-else
                          class="mention-link"
                          @click="handleMentionClick(part.value, r.id)"
                        >
                          @{{ part.value }}
                        </span>
                      </template>
                    </p>
                    <!-- 内嵌回复的操作按钮 -->
                    <div class="comment-actions">
                      <ElButton 
                        link 
                        :type="r.is_liked ? 'danger' : 'info'" 
                        size="small" 
                        @click="toggleLike(r)"
                      >
                        <ElIcon style="margin-right: 4px">
                          <span v-if="r.is_liked">❤️</span>
                          <span v-else>🤍</span>
                        </ElIcon>
                        {{ r.like_count > 0 ? r.like_count : '点赞' }}
                      </ElButton>
                      <ElButton link type="primary" size="small" @click="startReply(r.id)">
                        回复
                      </ElButton>
                      <ElButton 
                        v-if="canDeleteComment(r)"
                        link 
                        type="danger" 
                        size="small" 
                        @click="deleteComment(r)"
                      >
                        删除
                      </ElButton>
                    </div>
                    <!-- 内嵌回复的回复表单 -->
                    <div v-if="replyingTo === r.id" class="reply-form">
                      <ElInput
                        v-if="!auth.isAuthenticated"
                        v-model="replyGuestName"
                        placeholder="你的昵称"
                        size="small"
                        style="margin-bottom: 8px; max-width: 200px"
                      />
                      <ElInput
                        v-model="replyContent"
                        type="textarea"
                        :placeholder="`回复 @${r.user?.nickname || r.user?.username || r.guest_name || '匿名'}...`"
                        :rows="2"
                      />
                      <div class="reply-actions">
                        <ElButton size="small" @click="cancelReply">取消</ElButton>
                        <ElButton type="primary" size="small" :loading="loadingReply" @click="submitReply(c.id)">
                          提交回复
                        </ElButton>
                      </div>
                    </div>
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
                placeholder="你的昵称"
                size="small"
                style="margin-bottom: 8px; max-width: 200px"
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
          <!-- 权限不足提示 -->
          <ElCard v-else-if="!loadingCommentsConfig && commentsEnabled && !canViewComments" class="main-card" header="评论" style="margin-top: 24px">
            <ElEmpty :description="permissionMessage">
              <ElButton v-if="!auth.isAuthenticated" type="primary" @click="showLoginModal">立即登录</ElButton>
            </ElEmpty>
          </ElCard>
          <ElCard v-else-if="!loadingCommentsConfig && !commentsStealth" class="main-card" header="评论" style="margin-top: 24px">
            <ElEmpty description="评论功能已关闭" />
          </ElCard>
        </template>
        <ElEmpty v-else-if="!articleStore.loading && articleAccessDenied" description="该文章需要登录后查看">
          <ElButton type="primary" @click="showLoginModal">立即登录</ElButton>
        </ElEmpty>
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
          <p class="profile-desc">测试测试测试</p>
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

.dark .back-link {
  color: var(--text-secondary);
}

.dark .back-link:hover {
  color: #4ade80;
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

.dark .toc-item {
  color: var(--text-secondary);
}

.dark .toc-item:hover {
  background: var(--bg-hover);
  color: #4ade80;
}

.toc-h2 {
  font-weight: 500;
}

.toc-h3 {
  padding-left: 20px;
  font-size: 12px;
  color: #777;
}

.dark .toc-h3 {
  color: var(--text-tertiary);
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

.dark .profile-name {
  color: var(--text-primary);
}

.profile-desc {
  font-size: 12px;
  color: #888;
}

.dark .profile-desc {
  color: var(--text-tertiary);
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

/* 主内容区卡片圆角 */
.main-card {
  border-radius: 12px;
}

.title {
  font-size: 28px;
  margin: 0 0 12px;
  line-height: 1.4;
}

.meta {
  margin-bottom: 12px;
}

.dark .title {
  color: var(--text-primary);
}

.markdown-body {
  line-height: 1.8;
  font-size: 15px;
  color: var(--text-primary);
}

.dark .markdown-body {
  color: var(--text-primary);
}

.dark .markdown-body :deep(h1),
.dark .markdown-body :deep(h2),
.dark .markdown-body :deep(h3),
.dark .markdown-body :deep(h4),
.dark .markdown-body :deep(h5),
.dark .markdown-body :deep(h6) {
  color: var(--text-primary);
}

.dark .markdown-body :deep(p) {
  color: var(--text-secondary);
}

.dark .markdown-body :deep(li) {
  color: var(--text-secondary);
}

.dark .markdown-body :deep(pre) {
  background: var(--code-bg);
}

.dark .markdown-body :deep(code) {
  background: var(--code-bg);
  color: #fbbf24;
}

.dark .markdown-body :deep(blockquote) {
  border-left-color: var(--border-color);
  color: var(--text-tertiary);
}

.dark .markdown-body :deep(a) {
  color: #4ade80;
}

.dark .markdown-body :deep(hr) {
  border-color: var(--border-color);
}

.dark .markdown-body :deep(table) {
  border-color: var(--border-color);
}

.dark .markdown-body :deep(th),
.dark .markdown-body :deep(td) {
  border-color: var(--border-color);
}

.dark .markdown-body :deep(th) {
  background: var(--bg-hover);
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

.dark .comment-item {
  background: var(--bg-hover);
}

.comment-header {
  margin-bottom: 10px;
}

.comment-content {
  font-size: 14px;
  color: #444;
  margin: 0;
}

.dark .comment-content {
  color: var(--text-secondary);
}

.replies {
  margin-top: 12px;
  padding-left: 20px;
  border-left: 2px solid #e0e0e0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.dark .replies {
  border-left-color: var(--border-color);
}

.reply {
  background: #f0f4f0;
}

.dark .reply {
  background: var(--bg-primary);
}

/* @xxx 高亮链接样式 */
.mention-link {
  color: #18a058;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.mention-link:hover {
  color: #0d7a42;
  text-decoration: underline;
}

.dark .mention-link {
  color: #4ade80;
}

.dark .mention-link:hover {
  color: #22c55e;
}

/* 评论高亮动画 */
.comment-highlight {
  animation: highlight-pulse 2s ease;
}

@keyframes highlight-pulse {
  0% {
    background-color: rgba(24, 160, 88, 0.3);
  }
  100% {
    background-color: transparent;
  }
}

.dark .comment-highlight {
  animation: highlight-pulse-dark 2s ease;
}

@keyframes highlight-pulse-dark {
  0% {
    background-color: rgba(74, 222, 128, 0.3);
  }
  100% {
    background-color: transparent;
  }
}

.comment-actions {
  margin-top: 8px;
}

.reply-form {
  margin-top: 12px;
  padding: 12px;
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
}

.dark .reply-form {
  background: var(--bg-secondary);
  border-color: var(--border-color);
}

.reply-actions {
  margin-top: 8px;
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

/* 评论框圆角 */
.comment-form :deep(.el-textarea__inner),
.reply-form :deep(.el-textarea__inner) {
  border-radius: 8px;
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
