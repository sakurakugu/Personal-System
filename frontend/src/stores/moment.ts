import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../utils/api'

export interface Moment {
  id: string
  title: string | null
  content: string
  is_published: boolean
  user_id: string
  published_at: string | null
  created_at: string
  updated_at: string
  user?: {
    id: string
    username: string
    nickname: string | null
    avatar_url: string | null
  }
}

export interface MomentDraft {
  id: string
  title: string | null
  content: string
  updated_at: string
}

export const useMomentStore = defineStore('moment', () => {
  // 已发布的动态列表
  const moments = ref<Moment[]>([])
  const total = ref(0)
  const page = ref(1)
  const pages = ref(0)

  // 草稿（只有一个）
  const draft = ref<MomentDraft | null>(null)

  const loading = ref(false)
  const saving = ref(false)

  // 获取公开动态列表（博客端）
  async function fetchPublicMoments(p = 1) {
    loading.value = true
    try {
      const { data } = await api.get('/moments', { params: { page: p, page_size: 10 } })
      moments.value = data.items
      total.value = data.total
      page.value = data.page
      pages.value = data.pages
    } finally {
      loading.value = false
    }
  }

  // 获取当前用户的动态列表
  async function fetchMyMoments(p = 1) {
    loading.value = true
    try {
      const { data } = await api.get('/moments/my/list', { params: { page: p, page_size: 10 } })
      moments.value = data.items
      total.value = data.total
      page.value = data.page
      pages.value = data.pages
    } finally {
      loading.value = false
    }
  }

  // 获取草稿（自动获取上次未发布的内容）
  async function fetchDraft() {
    const { data } = await api.get('/moments/draft')
    draft.value = data
    return data
  }

  // 保存草稿
  async function saveDraft(body: { title?: string; content: string }) {
    saving.value = true
    try {
      const { data } = await api.put('/moments/draft', body)
      draft.value = data
      return data
    } finally {
      saving.value = false
    }
  }

  // 发布动态
  async function publish(body: { title?: string; content: string }) {
    const { data } = await api.post('/moments/publish', body)
    // 发布后清空草稿
    draft.value = null
    // 添加到列表开头
    moments.value.unshift(data)
    total.value++
    return data
  }

  // 删除动态
  async function deleteMoment(id: string) {
    await api.delete(`/moments/${id}`)
    moments.value = moments.value.filter(m => m.id !== id)
    total.value--
  }

  return {
    moments,
    draft,
    total,
    page,
    pages,
    loading,
    saving,
    fetchPublicMoments,
    fetchMyMoments,
    fetchDraft,
    saveDraft,
    publish,
    deleteMoment,
  }
})
