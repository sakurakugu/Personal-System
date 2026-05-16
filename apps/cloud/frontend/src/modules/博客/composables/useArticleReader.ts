import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import readingTime from 'reading-time/lib/reading-time'
import { ElMessage } from 'element-plus'
import { 追踪页面访问 } from '../../../modules/系统/api'
import {
  获取相关文章,
  点赞文章,
  取消点赞文章,
  使用文章存储,
  type ArticleMetaRecord,
  type ArticleNavigationRecord,
} from '@personal-system/module-articles'
import type { RenderedArticleMarkdown } from '@personal-system/module-articles/markdown'

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
  const articleStore = 使用文章存储()

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

  function 处理文章导航(slug: string) {
    void router.push(`/blog/${slug}`)
  }

  function 处理相关点击(slug: string) {
    void router.push(`/blog/${slug}`)
  }

  function 前往赞助() {
    void router.push('/sponsor')
  }

  async function 处理点赞文章() {
    if (!articleStore.current || articleLiking.value) return
    articleLiking.value = true
    try {
      const result = articleStore.current.liked
        ? await 取消点赞文章(articleStore.current.slug)
        : await 点赞文章(articleStore.current.slug)
      articleStore.current = {
        ...articleStore.current,
        like_count: result.like_count,
        liked: result.liked,
      }
      if (result.changed) {
        ElMessage.success(result.liked ? '点赞成功' : '已取消点赞')
      } else {
        ElMessage.info(result.liked ? '已经点过赞了' : '当前还没有点赞')
      }
    } catch {
      ElMessage.error('点赞失败')
    } finally {
      articleLiking.value = false
    }
  }

  function 构建标题ID(index: number) {
    return `heading-${index}`
  }

  function 同步文章目录(result: RenderedArticleMarkdown) {
    toc.value = result.headings
      .map((item, index) => ({
        id: 构建标题ID(index + 1),
        text: item.text,
        level: item.level,
      }))
      .filter((item) => item.level === 2 || item.level === 3)
    options.onTocUpdate(toc.value)
  }

  async function 加载文章页面(slug: string) {
    toc.value = []
    articleAccessDenied.value = false
    prevArticle.value = null
    nextArticle.value = null
    relatedArticles.value = []
    randomArticles.value = []

    const relatedTask = 获取相关文章(slug).then((data) => {
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
        await 追踪页面访问({
          path: `/blog/${slug}`,
          article_id: articleStore.current.id,
        })
      } catch {
        // 页面访问统计失败时不阻塞正文渲染。
      }
    }
  }

  function 显示登录弹窗() {
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
      void 加载文章页面(slug)
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
    buildHeadingId: 构建标题ID,
    syncArticleToc: 同步文章目录,
    handleArticleNav: 处理文章导航,
    handleRelatedClick: 处理相关点击,
    handleLikeArticle: 处理点赞文章,
    goSponsor: 前往赞助,
    showLoginModal: 显示登录弹窗,
  }
}
