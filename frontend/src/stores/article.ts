import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../utils/api'

export interface Article {
  id: string
  title: string
  slug: string
  content: string
  excerpt: string | null
  cover_url: string | null
  status: string
  view_count: number
  author: { id: string; username: string; nickname: string | null; avatar_url: string | null }
  category: { id: string; name: string; slug: string } | null
  tags: { id: string; name: string; slug: string }[]
  published_at: string | null
  created_at: string
  updated_at: string
}

export const useArticleStore = defineStore('article', () => {
  const articles = ref<Article[]>([])
  const current = ref<Article | null>(null)
  const total = ref(0)
  const page = ref(1)
  const pages = ref(0)
  const loading = ref(false)

  async function fetchArticles(p = 1, query: Record<string, string> = {}) {
    loading.value = true
    try {
      const { data } = await api.get('/articles', { params: { page: p, page_size: 10, ...query } })
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
    try {
      const { data } = await api.get(`/articles/${slug}`)
      current.value = data
    } finally {
      loading.value = false
    }
  }

  return { articles, current, total, page, pages, loading, fetchArticles, fetchBySlug }
})
