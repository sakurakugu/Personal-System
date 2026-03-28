import { defineStore } from 'pinia'
import { ref } from 'vue'
import { fetchArticleBySlug, fetchArticleList } from '../features/articles/api'
import type { ArticleQuery, ArticleRecord } from '../features/articles/types'

export type Article = ArticleRecord

export const useArticleStore = defineStore('article', () => {
  const articles = ref<ArticleRecord[]>([])
  const current = ref<ArticleRecord | null>(null)
  const total = ref(0)
  const page = ref(1)
  const pages = ref(0)
  const loading = ref(false)

  async function fetchArticles(p = 1, query: ArticleQuery = {}) {
    loading.value = true
    try {
      const data = await fetchArticleList(p, query)
      articles.value = data.items
      total.value = data.total
      page.value = data.page
      pages.value = data.pages
    } finally {
      loading.value = false
    }
  }

  async function fetchBySlug(slug: string) {
    loading.value = true
    current.value = null
    try {
      current.value = await fetchArticleBySlug(slug)
    } finally {
      loading.value = false
    }
  }

  return { articles, current, total, page, pages, loading, fetchArticles, fetchBySlug }
})
