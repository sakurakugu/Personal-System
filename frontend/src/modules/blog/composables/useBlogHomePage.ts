import { computed, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useRoute, useRouter } from 'vue-router'
import { trackPageView } from '../../system/api'
import { useArticleTaxonomyStore } from '../../articles/taxonomy'
import { useBlogAppearanceStore } from '../store'
import { useAuthStore } from '../../auth/store'
import {
  buildBlogFeedQuery,
  getBlogRouteName,
  parseBlogFeedQuery,
  resolveBlogViewMode,
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
  const currentViewMode = computed<BlogViewMode>(() => resolveBlogViewMode(route))
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

  function goToBlogView(view: BlogViewMode) {
    return router.push({
      name: getBlogRouteName(view),
    })
  }

  function goToBlogFeed(
    nextState: {
      search: string
      category: string | null
      sort: BlogSortMode
    },
    replace = false,
  ) {
    const target = {
      name: 'BlogHome',
      query: buildBlogFeedQuery(nextState),
    }

    if (replace) {
      return router.replace(target)
    }

    return router.push(target)
  }

  function syncFromRoute() {
    const nextState = parseBlogFeedQuery(route)
    search.value = nextState.search
    categoryFilter.value = nextState.category
    activeSort.value = nextState.sort
  }

  function backToFeed() {
    articleToc.value = []
    void goToBlogFeed({
      search: search.value,
      category: categoryFilter.value,
      sort: activeSort.value,
    }, true)
  }

  function scrollToSection(id: string) {
    const element = document.getElementById(id)
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }

  function switchToArchive() {
    void goToBlogView('archive')
  }

  function switchToAnnouncements() {
    void goToBlogView('announcements')
  }

  function switchToBangumi() {
    void goToBlogView('bangumi')
  }

  function searchByTag(tagName: string) {
    void goToBlogFeed({
      search: tagName,
      category: null,
      sort: 'comprehensive',
    })
  }

  function goArticle(slug: string) {
    void router.push(`/blog/${slug}`)
  }

  function goMoment(id: string) {
    void router.push(`/moments/${id}`)
  }

  function doSearch() {
    void goToBlogFeed({
      search: search.value,
      category: categoryFilter.value,
      sort: activeSort.value,
    })
  }

  function handleCategorySelect(slug: string | null) {
    categoryFilter.value = slug
    if (slug === null) {
      search.value = ''
      activeSort.value = 'comprehensive'
      showFilterBar.value = false
      showAnnouncements.value = true
    } else {
      showAnnouncements.value = false
    }
    doSearch()
  }

  function selectSort(key: string) {
    activeSort.value = key as BlogSortMode
    doSearch()
  }

  function clearSearchFilters() {
    search.value = ''
    categoryFilter.value = null
    activeSort.value = 'comprehensive'
    void goToBlogFeed({
      search: '',
      category: null,
      sort: 'comprehensive',
    })
  }

  function toggleFilterBar() {
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
      syncFromRoute()
    },
    { immediate: true },
  )

  watch(
    () => route.path,
    (path) => {
      if (!articleSlug.value && !momentId.value) {
        void trackPageView({ path })
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
    backToFeed,
    scrollToSection,
    switchToArchive,
    switchToAnnouncements,
    switchToBangumi,
    searchByTag,
    goArticle,
    goMoment,
    handleCategorySelect,
    selectSort,
    clearSearchFilters,
    toggleFilterBar,
  }
}
