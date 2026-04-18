import { ElMessage } from 'element-plus'
import axios from 'axios'
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  createComment,
  deleteComment as removeComment,
  fetchComments,
  likeComment,
  unlikeComment,
} from '../../../modules/comments/api'
import type { CommentRecord } from '../../../modules/comments/types'
import { trackPageView } from '../../../modules/system/api'
import { useArticleStore } from '../../../modules/articles/store'
import type { ArticleMetaRecord, ArticleNavigationRecord } from '../../../modules/articles/types'
import { useAuthStore } from '../../../modules/auth/store'
import { useSettingsStore } from '../../../shared/stores/settings'
import { getApiErrorMessage } from '../../../shared/api'
import { fetchArticleRelated } from '../../../modules/articles/api'
import readingTime from 'reading-time'
import type { RenderedArticleMarkdown } from '../../articles/markdown'

export interface TocItem {
  id: string
  text: string
  level: number
}

interface UseArticleReaderOptions {
  slug: () => string
  onTocUpdate: (items: TocItem[]) => void
}

export function useArticleReader(options: UseArticleReaderOptions) {
  const route = useRoute()
  const router = useRouter()
  const articleStore = useArticleStore()
  const auth = useAuthStore()
  const settingsStore = useSettingsStore()

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
  const prevArticle = ref<ArticleNavigationRecord | null>(null)
  const nextArticle = ref<ArticleNavigationRecord | null>(null)
  const relatedArticles = ref<ArticleMetaRecord[]>([])
  const randomArticles = ref<ArticleMetaRecord[]>([])

  const articleViewModeOptions = [
    { label: '正文', value: 'markdown' },
    { label: '思维导图', value: 'mindmap' },
  ] as const
  const siteTitle = 'Sakurakugu'

  const readingTimeInfo = computed(() => {
    if (!articleStore.current?.content) return null
    const rt = readingTime(articleStore.current.content)
    return {
      minutes: Math.max(1, Math.round(rt.minutes)),
      words: rt.words,
    }
  })

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

  function handleArticleNav(slug: string) {
    router.push(`/blog/${slug}`)
  }

  function handleRelatedClick(slug: string) {
    router.push(`/blog/${slug}`)
  }

  function goSponsor() {
    router.push('/sponsor')
  }

  function buildHeadingId(index: number) {
    return `heading-${index}`
  }

  function syncArticleToc(result: RenderedArticleMarkdown) {
    toc.value = result.headings
      .map((item, index) => ({
        id: buildHeadingId(index + 1),
        text: item.text,
        level: item.level,
      }))
      .filter((item) => item.level === 2 || item.level === 3)
    options.onTocUpdate(toc.value)
  }

  async function loadCommentsConfig() {
    loadingCommentsConfig.value = true
    try {
      await settingsStore.ensurePublicSettingsLoaded()
      const data = settingsStore.settings
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

  function removeCommentFromTree(commentList: CommentRecord[], commentId: string): CommentRecord[] {
    return commentList
      .filter((comment) => comment.id !== commentId)
      .map((comment) => ({
        ...comment,
        replies: removeCommentFromTree(comment.replies || [], commentId),
      }))
  }

  function normalizeComment(comment: CommentRecord): CommentRecord {
    return {
      ...comment,
      replies: comment.replies || [],
    }
  }

  function insertRootComment(comment: CommentRecord) {
    comments.value = [...comments.value, normalizeComment(comment)]
  }

  function insertReplyComment(parentId: string, reply: CommentRecord): boolean {
    let hasInserted = false
    comments.value = comments.value.map((comment) => {
      if (comment.id !== parentId) {
        return comment
      }
      hasInserted = true
      return {
        ...comment,
        replies: [...(comment.replies || []), normalizeComment(reply)],
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
    prevArticle.value = null
    nextArticle.value = null
    relatedArticles.value = []
    randomArticles.value = []
    const commentsConfigTask = loadCommentsConfig()
    const relatedTask = fetchArticleRelated(slug).then((data) => {
      prevArticle.value = data.prev
      nextArticle.value = data.next
      relatedArticles.value = data.related
      randomArticles.value = data.random
    }).catch(() => {
      prevArticle.value = null
      nextArticle.value = null
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
    await Promise.all([commentsConfigTask, relatedTask])
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
        insertRootComment(created)
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
    let match: RegExpExecArray | null

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

    for (const comment of comments.value) {
      allComments.push(comment)
      for (const reply of comment.replies || []) {
        allComments.push(reply)
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

  function findCommentById(commentId: string): CommentRecord | null {
    for (const comment of comments.value) {
      if (comment.id === commentId) return comment
      for (const reply of comment.replies || []) {
        if (reply.id === commentId) return reply
      }
    }
    return null
  }

  function startReply(commentId: string) {
    replyingTo.value = commentId
    replyingToComment.value = findCommentById(commentId)
    replyGuestName.value = guestName.value
    replyContent.value = ''
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
        const hasInserted = insertReplyComment(parentId, created)
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
      comments.value = removeCommentFromTree(comments.value, comment.id)
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

  watch(() => articleStore.current?.content, (newContent) => {
    if (!newContent) {
      toc.value = []
      options.onTocUpdate([])
    }
  })

  watch(() => options.slug(), (slug) => {
    if (slug) {
      void loadArticlePage(slug)
    }
  }, { immediate: true })

  return {
    articleStore,
    auth,
    comments,
    newComment,
    guestName,
    loadingComment,
    loadingCommentsConfig,
    commentsEnabled,
    commentsStealth,
    articleAccessDenied,
    replyingTo,
    replyContent,
    replyGuestName,
    loadingReply,
    articleViewMode,
    prevArticle,
    nextArticle,
    relatedArticles,
    randomArticles,
    readingTimeInfo,
    articleViewModeOptions,
    siteTitle,
    articleUrl,
    articleCoverImage,
    canViewComments,
    permissionMessage,
    buildHeadingId,
    syncArticleToc,
    handleArticleNav,
    handleRelatedClick,
    goSponsor,
    showLoginModal,
    submitComment,
    parseMentions,
    handleMentionClick,
    startReply,
    cancelReply,
    submitReply,
    canDeleteComment,
    deleteComment,
    toggleLike,
  }
}
