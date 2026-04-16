<script setup lang="ts">
import { ElButton, ElDivider, ElEmpty, ElInput, ElMessage, ElSkeleton } from 'element-plus'
import axios from 'axios'
import { computed, defineAsyncComponent, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  createComment,
  deleteComment as removeComment,
  fetchComments,
  likeComment,
  unlikeComment,
} from '../../../features/comments/api'
import type { CommentRecord } from '../../../features/comments/types'
import { fetchPublicSettings, trackPageView } from '../../../features/system/api'
import { useArticleStore } from '../../../stores/article'
import { useAuthStore } from '../../../stores/auth'
import { getApiErrorMessage } from '../../../utils/api'
import SegmentedSwitch from '../../../components/SegmentedSwitch.vue'
import MarkdownRenderer from '../../../components/MarkdownRenderer.vue'
import SharePoster from './SharePoster.vue'
import { sponsorConfig } from '../../../constants/sponsorConfig'
import { fetchAllArticleMeta, fetchArticleRelated } from '../../../features/articles/api'
import type { ArticleMetaRecord } from '../../../features/articles/types'
import readingTime from 'reading-time'
import ArticleMeta from './ArticleMeta.vue'
import ArticleLicense from './ArticleLicense.vue'
import ArticleNav from './ArticleNav.vue'
import ArticleRelated from './ArticleRelated.vue'
import type { RenderedArticleMarkdown } from '../../../utils/articleMarkdown'

const props = defineProps<{
  slug: string
}>()

const emit = defineEmits<{
  back: []
  tagClick: [name: string]
  'update:toc': [items: TocItem[]]
}>()

const route = useRoute()
const router = useRouter()
const articleStore = useArticleStore()
const auth = useAuthStore()
const MarkdownMindmap = defineAsyncComponent(() => import('../../../components/MarkdownMindmap.vue'))

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
const commentsEnabled = ref(false)
const commentsStealth = ref(true)
const commentsMinRole = ref('guest')
const toc = ref<TocItem[]>([])
const articleAccessDenied = ref(false)

const replyingTo = ref<string | null>(null)
const replyContent = ref('')
const replyGuestName = ref('')
const loadingReply = ref(false)
const replyingToComment = ref<CommentRecord | null>(null)
const articleViewMode = ref<'markdown' | 'mindmap'>('markdown')
const allArticles = ref<ArticleMetaRecord[]>([])
const relatedArticles = ref<ArticleMetaRecord[]>([])
const randomArticles = ref<ArticleMetaRecord[]>([])

const readingTimeInfo = computed(() => {
  if (!articleStore.current?.content) return null
  const rt = readingTime(articleStore.current.content)
  return {
    minutes: Math.max(1, Math.round(rt.minutes)),
    words: rt.words,
  }
})

const articleIndex = computed(() => {
  if (!articleStore.current || allArticles.value.length === 0) return -1
  return allArticles.value.findIndex((a) => a.id === articleStore.current!.id)
})

const prevArticle = computed(() => {
  const idx = articleIndex.value
  if (idx <= 0) return null
  const prev = allArticles.value[idx - 1]
  return prev ? { slug: prev.slug, title: prev.title } : null
})

const nextArticle = computed(() => {
  const idx = articleIndex.value
  if (idx === -1 || idx >= allArticles.value.length - 1) return null
  const next = allArticles.value[idx + 1]
  return next ? { slug: next.slug, title: next.title } : null
})

function handleArticleNav(slug: string) {
  router.push(`/blog/${slug}`)
}

function handleRelatedClick(slug: string) {
  router.push(`/blog/${slug}`)
}

const articleViewModeOptions = [
  { label: '正文', value: 'markdown' },
  { label: '思维导图', value: 'mindmap' },
] as const

const siteTitle = 'Sakurakugu'

const articleUrl = computed(() => {
  if (typeof window === 'undefined') return ''
  return window.location.href
})

const articleCoverImage = computed(() => {
  if (!articleStore.current?.cover_url) return null
  return articleStore.current.cover_url
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

function 构建标题锚点(index: number) {
  return `heading-${index}`
}

function 同步文章目录(result: RenderedArticleMarkdown) {
  toc.value = result.headings
    .map((item, index) => ({
      id: 构建标题锚点(index + 1),
      text: item.text,
      level: item.level,
    }))
    .filter((item) => item.level === 2 || item.level === 3)
  emit('update:toc', toc.value)
}

async function loadCommentsConfig() {
  loadingCommentsConfig.value = true
  try {
    const data = await fetchPublicSettings()
    commentsEnabled.value = data.comments_enabled
    commentsStealth.value = data.comments_stealth
    commentsMinRole.value = data.comments_min_role || 'guest'
  } catch {
    commentsEnabled.value = false
    commentsStealth.value = true
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

function 从评论树移除评论(commentList: CommentRecord[], commentId: string): CommentRecord[] {
  return commentList
    .filter((comment) => comment.id !== commentId)
    .map((comment) => ({
      ...comment,
      replies: 从评论树移除评论(comment.replies || [], commentId),
    }))
}

function 规范化评论(comment: CommentRecord): CommentRecord {
  return {
    ...comment,
    replies: comment.replies || [],
  }
}

function 插入顶级评论(comment: CommentRecord) {
  comments.value = [...comments.value, 规范化评论(comment)]
}

function 插入回复评论(parentId: string, reply: CommentRecord): boolean {
  let hasInserted = false
  comments.value = comments.value.map((comment) => {
    if (comment.id !== parentId) {
      return comment
    }
    hasInserted = true
    return {
      ...comment,
      replies: [...(comment.replies || []), 规范化评论(reply)],
    }
  })
  return hasInserted
}

async function loadArticlePage(slug: string) {
  comments.value = []
  toc.value = []
  replyingTo.value = null
  replyingToComment.value = null
  articleAccessDenied.value = false
  relatedArticles.value = []
  randomArticles.value = []
  const commentsConfigTask = loadCommentsConfig()
  const allMetaTask = fetchAllArticleMeta().then((data) => {
    allArticles.value = data.sort((a, b) => {
      const ta = a.published_at || a.id
      const tb = b.published_at || b.id
      return ta > tb ? -1 : 1
    })
  }).catch(() => {
    allArticles.value = []
  })
  const relatedTask = fetchArticleRelated(slug).then((data) => {
    relatedArticles.value = data.related
    randomArticles.value = data.random
  }).catch(() => {
    relatedArticles.value = []
    randomArticles.value = []
  })
  try {
    await articleStore.fetchBySlug(slug)
  } catch (error) {
    if (axios.isAxiosError(error) && articleStore.currentErrorStatus === 401) {
      articleAccessDenied.value = true
      return
    }
    return
  }
  await Promise.all([commentsConfigTask, allMetaTask, relatedTask])
  if (articleStore.current) {
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
  if (!newContent) {
    toc.value = []
  }
})

watch(() => props.slug, (slug) => {
  if (slug) {
    void loadArticlePage(slug)
  }
}, { immediate: true })

function showLoginModal() {
  router.replace({ query: { ...route.query, login: '1' } })
}

async function submitComment() {
  if (!articleStore.current || !newComment.value.trim() || !commentsEnabled.value) return
  loadingComment.value = true
  try {
    const created = await createComment({
      article_id: articleStore.current.id,
      content: newComment.value,
      guest_name: auth.isAuthenticated ? undefined : (guestName.value || '匿名'),
    })
    newComment.value = ''
    if (created.status === 'approved') {
      插入顶级评论(created)
      ElMessage.success('评论已发布')
    } else {
      ElMessage.success('评论已提交，等待审核')
    }
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
  
  ElMessage.info(`未找到用户 ${targetName} 的更早评论`)
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
    
    const created = await createComment({
      article_id: articleStore.current.id,
      content,
      parent_id: parentId,
      guest_name: auth.isAuthenticated ? undefined : (replyGuestName.value || '匿名'),
    })
    replyContent.value = ''
    replyingTo.value = null
    replyingToComment.value = null
    if (created.status === 'approved') {
      const hasInserted = 插入回复评论(parentId, created)
      if (!hasInserted) {
        await loadComments()
      }
      ElMessage.success('回复已发布')
    } else {
      ElMessage.success('回复已提交，等待审核')
    }
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
    comments.value = 从评论树移除评论(comments.value, comment.id)
    ElMessage.success('删除成功')
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
  <div class="article-reader">
    <ElSkeleton :loading="articleStore.loading" animated>
      <template v-if="articleStore.current">
        <div class="post-container">
          <!-- 头部 Meta -->
          <div class="post-header">
            <div class="post-title">{{ articleStore.current.title }}</div>
            <ArticleMeta
              :published-at="articleStore.current.published_at || articleStore.current.created_at"
              :author="articleStore.current.author.nickname || articleStore.current.author.username"
              :category="articleStore.current.category"
              :tags="articleStore.current.tags"
              :view-count="articleStore.current.view_count"
              :reading-time-info="readingTimeInfo"
              @tag-click="emit('tagClick', $event)"
            />
          </div>

          <!-- 操作栏 -->
          <div class="post-actions-bar">
            <div class="post-actions-left">
              <SharePoster
                v-if="articleStore.current"
                :title="articleStore.current.title"
                :author="articleStore.current.author.nickname || articleStore.current.author.username"
                :description="articleStore.current.excerpt || ''"
                :pub-date="articleStore.current.published_at || articleStore.current.created_at"
                :cover-image="articleCoverImage"
                :url="articleUrl"
                :site-title="siteTitle"
                avatar="/头像.avif"
              />
              <ElButton
                v-if="sponsorConfig.showButtonInPost"
                size="small"
                class="sponsor-btn"
                @click="router.push('/blog?mode=sponsor')"
              >
                <span class="sponsor-heart">❤️</span>
                <span>赞助支持</span>
              </ElButton>
            </div>
            <div class="article-view-switch">
              <SegmentedSwitch
                v-model="articleViewMode"
                aria-label="文章查看模式"
                :options="articleViewModeOptions"
                active-color="var(--el-color-primary)"
                size="small"
              />
            </div>
          </div>

          <!-- 正文 -->
          <div class="post-content-wrap">
            <MarkdownRenderer
              v-if="articleViewMode === 'markdown'"
              class="article-markdown-preview"
              :content="articleStore.current?.content || ''"
              :build-heading-id="构建标题锚点"
              @rendered="同步文章目录"
            />
            <MarkdownMindmap
              v-else
              class="article-mindmap"
              :content="articleStore.current.content"
              :title="articleStore.current.title"
              :height="640"
            />
          </div>

          <!-- 版权 -->
          <ArticleLicense
            :title="articleStore.current.title"
            :url="articleUrl"
            :pub-date="articleStore.current.published_at || articleStore.current.created_at"
          />

          <!-- 上/下一篇 -->
          <ArticleNav
            :prev="prevArticle"
            :next="nextArticle"
            @navigate="handleArticleNav"
          />

          <!-- 相关文章 / 随机推荐 -->
          <ArticleRelated
            :related-articles="relatedArticles"
            :random-articles="randomArticles"
            @article-click="handleRelatedClick"
          />

          <!-- 标签 -->
          <div v-if="articleStore.current.tags?.length" class="article-tags-section">
            <div class="tags-title">🏷️ 本文标签</div>
            <div class="tag-list">
              <span
                v-for="tag in articleStore.current.tags"
                :key="tag.id"
                class="tag-chip"
                @click="emit('tagClick', tag.name)"
              >
                {{ tag.name }}
              </span>
            </div>
          </div>

          <!-- 评论区 -->
          <div v-if="!loadingCommentsConfig && commentsEnabled && canViewComments" class="comments-card">
            <div class="comments-header">评论</div>
            <div v-if="comments.length" class="comment-list">
              <div
                v-for="c in comments"
                :id="`comment-${c.id}`"
                :key="c.id"
                class="comment-item"
              >
                <div class="comment-header">
                  <span class="comment-author">{{ c.user?.nickname || c.user?.username || c.guest_name || '匿名' }}</span>
                  <span class="comment-time">{{ new Date(c.created_at).toLocaleString() }}</span>
                </div>
                <p class="comment-content">
                  <template v-for="(part, idx) in parseMentions(c.content)" :key="idx">
                    <span v-if="part.type === 'text'">{{ part.value }}</span>
                    <span v-else class="mention-link" @click="handleMentionClick(part.value, c.id)">
                      @{{ part.value }}
                    </span>
                  </template>
                </p>

                <div class="comment-actions">
                  <ElButton
                    link
                    :type="c.is_liked ? 'danger' : 'info'"
                    size="small"
                    @click="toggleLike(c)"
                  >
                    <span style="margin-right: 4px">{{ c.is_liked ? '❤️' : '🤍' }}</span>
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
                  <div
                    v-for="r in c.replies"
                    :id="`comment-${r.id}`"
                    :key="r.id"
                    class="comment-item reply"
                  >
                    <div class="comment-header">
                      <span class="comment-author">{{ r.user?.nickname || r.user?.username || r.guest_name || '匿名' }}</span>
                      <span class="comment-time">{{ new Date(r.created_at).toLocaleString() }}</span>
                    </div>
                    <p class="comment-content">
                      <template v-for="(part, idx) in parseMentions(r.content)" :key="idx">
                        <span v-if="part.type === 'text'">{{ part.value }}</span>
                        <span v-else class="mention-link" @click="handleMentionClick(part.value, r.id)">
                          @{{ part.value }}
                        </span>
                      </template>
                    </p>
                    <div class="comment-actions">
                      <ElButton
                        link
                        :type="r.is_liked ? 'danger' : 'info'"
                        size="small"
                        @click="toggleLike(r)"
                      >
                        <span style="margin-right: 4px">{{ r.is_liked ? '❤️' : '🤍' }}</span>
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
              <div class="comment-submit-row">
                <ElButton
                  type="primary"
                  :loading="loadingComment"
                  @click="submitComment"
                >
                  发表评论
                </ElButton>
              </div>
            </div>
          </div>

          <!-- 权限不足提示 -->
          <div v-else-if="!loadingCommentsConfig && commentsEnabled && !canViewComments" class="comments-card">
            <div class="comments-header">评论</div>
            <ElEmpty :description="permissionMessage">
              <ElButton v-if="!auth.isAuthenticated" type="primary" @click="showLoginModal">立即登录</ElButton>
            </ElEmpty>
          </div>
          <div v-else-if="!loadingCommentsConfig && !commentsStealth" class="comments-card">
            <div class="comments-header">评论</div>
            <ElEmpty description="评论功能已关闭" />
          </div>
        </div>
      </template>

      <ElEmpty v-else-if="!articleStore.loading && articleAccessDenied" description="该文章需要登录后查看">
        <ElButton type="primary" @click="showLoginModal">立即登录</ElButton>
      </ElEmpty>
      <ElEmpty v-else-if="!articleStore.loading" description="文章不存在" />
    </ElSkeleton>
  </div>
</template>

<style scoped>
.article-reader {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.post-container {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.post-header {
  padding: 1rem;
  border-radius: var(--radius-large);
  background: var(--card-bg-transparent);
  border: 1px solid rgba(255, 255, 255, 0.45);
  backdrop-filter: blur(18px);
  background-color: rgba(255, 255, 255, var(--overlay-card-opacity)) !important;
}

.dark .post-header {
  border-color: rgba(148, 163, 184, 0.16);
  background-color: rgba(15, 23, 42, var(--overlay-card-opacity)) !important;
}

.post-title {
  font-size: 1.75rem;
  font-weight: 800;
  line-height: 1.35;
  margin: 0 0 0.75rem;
  color: var(--text-primary);
}

.post-actions-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  border-radius: var(--radius-large);
  background: var(--card-bg-transparent);
  border: 1px solid rgba(255, 255, 255, 0.45);
  backdrop-filter: blur(18px);
  background-color: rgba(255, 255, 255, var(--overlay-card-opacity)) !important;
}

.dark .post-actions-bar {
  border-color: rgba(148, 163, 184, 0.16);
  background-color: rgba(15, 23, 42, var(--overlay-card-opacity)) !important;
}

.post-actions-left {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.sponsor-btn .sponsor-heart {
  margin-right: 4px;
}

.post-content-wrap {
  padding: 1.25rem;
  border-radius: var(--radius-large);
  background: var(--card-bg-transparent);
  border: 1px solid rgba(255, 255, 255, 0.45);
  backdrop-filter: blur(18px);
  background-color: rgba(255, 255, 255, var(--overlay-card-opacity)) !important;
}

.dark .post-content-wrap {
  border-color: rgba(148, 163, 184, 0.16);
  background-color: rgba(15, 23, 42, var(--overlay-card-opacity)) !important;
}

.article-markdown-preview {
  width: 100%;
}

.article-markdown-preview h2,
.article-markdown-preview h3 {
  scroll-margin-top: 80px;
}

.article-mindmap {
  width: 100%;
  min-height: 640px;
}

.article-tags-section {
  padding: 1rem 1.25rem;
  border-radius: var(--radius-large);
  background: var(--card-bg-transparent);
  border: 1px solid rgba(255, 255, 255, 0.45);
  backdrop-filter: blur(18px);
  background-color: rgba(255, 255, 255, var(--overlay-card-opacity)) !important;
}

.dark .article-tags-section {
  border-color: rgba(148, 163, 184, 0.16);
  background-color: rgba(15, 23, 42, var(--overlay-card-opacity)) !important;
}

.tags-title {
  font-weight: 700;
  margin-bottom: 0.75rem;
  color: var(--text-primary);
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.tag-chip {
  display: inline-flex;
  align-items: center;
  padding: 0.25rem 0.625rem;
  font-size: 0.8125rem;
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.05);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
}

.tag-chip:hover {
  background: rgba(0, 0, 0, 0.1);
  color: var(--text-primary);
}

.dark .tag-chip {
  background: rgba(255, 255, 255, 0.08);
}

.dark .tag-chip:hover {
  background: rgba(255, 255, 255, 0.12);
}

.comments-card {
  padding: 1rem 1.25rem 1.25rem;
  border-radius: var(--radius-large);
  background: var(--card-bg-transparent);
  border: 1px solid rgba(255, 255, 255, 0.45);
  backdrop-filter: blur(18px);
  background-color: rgba(255, 255, 255, var(--overlay-card-opacity)) !important;
}

.dark .comments-card {
  border-color: rgba(148, 163, 184, 0.16);
  background-color: rgba(15, 23, 42, var(--overlay-card-opacity)) !important;
}

.comments-header {
  font-weight: 700;
  font-size: 1rem;
  padding-bottom: 0.75rem;
  margin-bottom: 0.5rem;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  color: var(--text-primary);
}

.dark .comments-header {
  border-bottom-color: rgba(255, 255, 255, 0.08);
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

.comment-author {
  font-weight: 700;
  color: var(--text-primary);
}

.comment-time {
  font-size: 12px;
  margin-left: 8px;
  color: var(--text-secondary);
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

.mention-link {
  color: var(--el-color-primary);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.mention-link:hover {
  color: var(--el-color-primary-dark-2);
  text-decoration: underline;
}

.dark .mention-link {
  color: var(--el-color-primary-light-5);
}

.dark .mention-link:hover {
  color: var(--el-color-primary-light-3);
}

.comment-highlight {
  animation: highlight-pulse 2s ease;
}

@keyframes highlight-pulse {
  0% {
    background-color: var(--theme-accent-overlay-30);
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

.comment-submit-row {
  margin-top: 8px;
  display: flex;
  justify-content: flex-end;
}

.comment-form :deep(.el-textarea__inner),
.reply-form :deep(.el-textarea__inner) {
  border-radius: 8px;
}

@media (max-width: 576px) {
  .post-title {
    font-size: 1.375rem;
  }
}
</style>
