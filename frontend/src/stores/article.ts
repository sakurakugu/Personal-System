import { defineStore } from 'pinia'
import { ref } from 'vue'
import { fetchArticleBySlug, fetchArticleList } from '../features/articles/api'
import type { ArticleQuery, ArticleRecord } from '../features/articles/types'
import axios from 'axios'

export type Article = ArticleRecord

export const useArticleStore = defineStore('article', () => {
  const articles = ref<ArticleRecord[]>([])
  const current = ref<ArticleRecord | null>(null)
  const total = ref(0)
  const page = ref(1)
  const pages = ref(0)
  const loading = ref(false)
  const refreshing = ref(false)
  const currentErrorStatus = ref<number | null>(null)

  async function fetchArticles(p = 1, query: ArticleQuery = {}, options: { silent?: boolean } = {}) {
    const silent = options.silent ?? articles.value.length > 0
    if (silent) {
      refreshing.value = true
    } else {
      loading.value = true
    }
    try {
      const data = await fetchArticleList(p, query)
      articles.value = data.items
      total.value = data.total
      page.value = data.page
      pages.value = data.pages
    } finally {
      if (silent) {
        refreshing.value = false
      } else {
        loading.value = false
      }
    }
  }

  async function fetchBySlug(slug: string) {
    loading.value = true
    current.value = null
    currentErrorStatus.value = null
    try {
      current.value = await fetchArticleBySlug(slug)
    } catch (error) {
      if (axios.isAxiosError(error)) {
        currentErrorStatus.value = error.response?.status ?? null
      }
      throw error
    } finally {
      loading.value = false
    }
  }

  return { articles, current, total, page, pages, loading, refreshing, currentErrorStatus, fetchArticles, fetchBySlug }
})
