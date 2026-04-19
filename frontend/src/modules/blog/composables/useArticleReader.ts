import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import readingTime from 'reading-time'
import { ElMessage } from 'element-plus'
import { trackPageView } from '../../../modules/system/api'
import { useArticleStore } from '../../../modules/articles/store'
import { fetchArticleRelated, likeArticle } from '../../../modules/articles/api'
import type { ArticleMetaRecord, ArticleNavigationRecord } from '../../../modules/articles/types'
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

  const toc = ref<TocItem[]>([])
  const articleAccessDenied = ref(false)
  const articleViewMode = ref<'markdown' | 'mindmap'>('markdown')
  const prevArticle = ref<ArticleNavigationRecord | null>(null)
  const nextArticle = ref<ArticleNavigationRecord | null>(null)
  const relatedArticles = ref<ArticleMetaRecord[]>([])
  const randomArticles = ref<ArticleMetaRecord[]>([])
  const articleLiking = ref(false)

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

  const articleCommentsPath = computed(() => {
    const slug = options.slug().trim()
    return slug ? `/blog/${slug}` : '/blog'
  })

  function handleArticleNav(slug: string) {
    void router.push(`/blog/${slug}`)
  }

  function handleRelatedClick(slug: string) {
    void router.push(`/blog/${slug}`)
  }

  function goSponsor() {
    void router.push('/sponsor')
  }

  async function handleLikeArticle() {
    if (!articleStore.current || articleLiking.value) return
    articleLiking.value = true
    try {
      const result = await likeArticle(articleStore.current.slug)
      articleStore.current = {
        ...articleStore.current,
        like_count: result.like_count,
      }
      ElMessage.success(result.changed ? '点赞成功' : '已经点过赞了')
    } catch {
      ElMessage.error('点赞失败')
    } finally {
      articleLiking.value = false
    }
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

  async function loadArticlePage(slug: string) {
    toc.value = []
    articleAccessDenied.value = false
    prevArticle.value = null
    nextArticle.value = null
    relatedArticles.value = []
    randomArticles.value = []

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
      }
      return
    }

    await relatedTask
    if (articleStore.current) {
      try {
        await trackPageView({
          path: `/blog/${slug}`,
          article_id: articleStore.current.id,
        })
      } catch {
        // 页面访问统计失败时不阻塞正文渲染。
      }
    }
  }

  function showLoginModal() {
    void router.replace({ query: { ...route.query, login: '1' } })
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
    articleAccessDenied,
    articleViewMode,
    prevArticle,
    nextArticle,
    relatedArticles,
    randomArticles,
    articleLiking,
    readingTimeInfo,
    articleViewModeOptions,
    siteTitle,
    articleUrl,
    articleCoverImage,
    articleCommentsPath,
    buildHeadingId,
    syncArticleToc,
    handleArticleNav,
    handleRelatedClick,
    handleLikeArticle,
    goSponsor,
    showLoginModal,
  }
}
