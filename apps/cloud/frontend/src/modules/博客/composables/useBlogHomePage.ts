import { computed, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@personal-system/domain/auth'
import { 追踪页面访问 } from '../../系统/api'
import { useArticleTaxonomyStore } from '@personal-system/module-articles'
import { useBlogAppearanceStore } from '../store'
import {
  构建博客Feed查询,
  获取博客路由名称,
  解析博客Feed查询,
  解析博客视图模式,
  type BlogSortMode,
  type BlogViewMode,
} from '../view'

export interface BlogTocItem {
  id: string
  text: string
  level: number
}

export function useBlogHomePage() {
  const auth = useAuthStore()
  const taxonomyStore = useArticleTaxonomyStore()
  const appearance = useBlogAppearanceStore()
  const route = useRoute()
  const router = useRouter()
  const { categories, tags: popularTags } = storeToRefs(taxonomyStore)

  const search = ref('')
  const categoryFilter = ref<string | null>(null)
  const totalArticles = ref(0)
  const showAnnouncements = ref(true)
  const showFilterBar = ref(false)
  const previousAnnouncementsState = ref(true)
  const activeSort = ref<BlogSortMode>('comprehensive')
  const articleToc = ref<BlogTocItem[]>([])

  const hasSearchFilters = computed(() => Boolean(search.value || categoryFilter.value || activeSort.value !== 'comprehensive'))
  const articleSlug = computed(() => {
    const slug = route.params.slug
    return typeof slug === 'string' ? slug : ''
  })
  const momentId = computed(() => {
    const value = route.params.momentId
    return typeof value === 'string' ? value : ''
  })
  const currentViewMode = computed<BlogViewMode>(() => 解析博客视图模式(route))
  const isDetailView = computed(() => Boolean(articleSlug.value || momentId.value))
  const mainViewKey = computed(() => articleSlug.value || momentId.value || route.path)
  const isAuthenticated = computed(() => auth.isAuthenticated)
  const isBannerMode = computed(() => appearance.wallpaperMode === 'banner')
  const blogHomeClass = computed(() => ({
    'is-banner-mode': isBannerMode.value,
    'is-overlay-mode': appearance.wallpaperMode === 'overlay',
    'is-plain-mode': appearance.wallpaperMode === 'none',
  }))
  const blogHomeStyle = computed(() => ({
    '--overlay-opacity': String(appearance.overlayOpacity / 100),
    '--overlay-blur': `${appearance.overlayBlur}px`,
    '--overlay-card-opacity': String(appearance.overlayCardOpacity / 100),
    '--overlay-card-opacity-strong': String(Math.min(appearance.overlayCardOpacity / 100 + 0.08, 1)),
  }))

  function 前往博客视图(view: BlogViewMode) {
    return router.push({
      name: 获取博客路由名称(view),
    })
  }

  function 前往博客Feed(
    nextState: {
      search: string
      category: string | null
      sort: BlogSortMode
    },
    replace = false,
  ) {
    const target = {
      name: 'BlogHome',
      query: 构建博客Feed查询(nextState),
    }

    if (replace) {
      return router.replace(target)
    }

    return router.push(target)
  }

  function 从路由同步() {
    const nextState = 解析博客Feed查询(route)
    search.value = nextState.search
    categoryFilter.value = nextState.category
    activeSort.value = nextState.sort
  }

  function 返回Feed() {
    articleToc.value = []
    void 前往博客Feed({
      search: search.value,
      category: categoryFilter.value,
      sort: activeSort.value,
    }, true)
  }

  function 滚动到章节(id: string) {
    const element = document.getElementById(id)
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }

  function 切换到归档() {
    void 前往博客视图('archive')
  }

  function 切换到公告() {
    void 前往博客视图('announcements')
  }

  function 切换到番剧() {
    void 前往博客视图('bangumi')
  }

  function 按标签搜索(tagName: string) {
    void 前往博客Feed({
      search: tagName,
      category: null,
      sort: 'comprehensive',
    })
  }

  function 前往文章(slug: string) {
    void router.push(`/blog/${slug}`)
  }

  function 前往动态(id: string) {
    void router.push(`/moments/${id}`)
  }

  function 执行搜索() {
    void 前往博客Feed({
      search: search.value,
      category: categoryFilter.value,
      sort: activeSort.value,
    })
  }

  function 处理分类选择(slug: string | null) {
    categoryFilter.value = slug
    if (slug === null) {
      search.value = ''
      activeSort.value = 'comprehensive'
      showFilterBar.value = false
      showAnnouncements.value = true
    } else {
      showAnnouncements.value = false
    }
    执行搜索()
  }

  function 选择排序(key: string) {
    activeSort.value = key as BlogSortMode
    执行搜索()
  }

  function 清除搜索筛选() {
    search.value = ''
    categoryFilter.value = null
    activeSort.value = 'comprehensive'
    void 前往博客Feed({
      search: '',
      category: null,
      sort: 'comprehensive',
    })
  }

  function 切换筛选栏() {
    if (!showFilterBar.value) {
      previousAnnouncementsState.value = showAnnouncements.value
      showAnnouncements.value = false
    } else {
      showAnnouncements.value = previousAnnouncementsState.value
    }
    showFilterBar.value = !showFilterBar.value
  }

  void taxonomyStore.ensureLoaded()

  watch(
    () => route.query,
    () => {
      从路由同步()
    },
    { immediate: true },
  )

  watch(
    () => route.path,
    (path) => {
      if (!articleSlug.value && !momentId.value) {
        void 追踪页面访问({ path })
      }
    },
    { immediate: true },
  )

  watch(
    () => [articleSlug.value, momentId.value],
    ([slug, 当前动态]) => {
      if (!slug && !当前动态) {
        articleToc.value = []
      }
    },
  )

  watch(
    () => route.name,
    () => {
      if (currentViewMode.value !== 'feed') {
        showFilterBar.value = false
      }
    },
  )

  return {
    categories,
    popularTags,
    search,
    categoryFilter,
    totalArticles,
    showAnnouncements,
    showFilterBar,
    activeSort,
    hasSearchFilters,
    articleSlug,
    momentId,
    isDetailView,
    currentViewMode,
    articleToc,
    mainViewKey,
    isAuthenticated,
    isBannerMode,
    blogHomeClass,
    blogHomeStyle,
    backToFeed: 返回Feed,
    scrollToSection: 滚动到章节,
    switchToArchive: 切换到归档,
    switchToAnnouncements: 切换到公告,
    switchToBangumi: 切换到番剧,
    searchByTag: 按标签搜索,
    goArticle: 前往文章,
    goMoment: 前往动态,
    handleCategorySelect: 处理分类选择,
    selectSort: 选择排序,
    clearSearchFilters: 清除搜索筛选,
    toggleFilterBar: 切换筛选栏,
  }
}
