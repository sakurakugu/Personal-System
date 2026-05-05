import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  deleteMoment as requestDeleteMoment,
  fetchMomentDraft,
  fetchMyMoments as requestMyMoments,
    fetchPublishedMoments as requestPublishedMoments,
    publishMoment,
    restoreMoment as requestRestoreMoment,
    saveMomentDraft,
    updateMoment as requestUpdateMoment,
  } from './api'
import type { MomentDraft, MomentPayload, UserMoment } from './types'

export const useMomentStore = defineStore('moment', () => {
  // 已发布的动态列表
  const moments = ref<UserMoment[]>([])
  const total = ref(0)
  const page = ref(1)
  const pages = ref(0)

  // 草稿（只有一个）
  const draft = ref<MomentDraft | null>(null)

  const loading = ref(false)
  const saving = ref(false)

  // 获取首页已发布动态列表（登录可见）
  async function fetchPublishedMoments(p = 1) {
    loading.value = true
    try {
      const data = await requestPublishedMoments(p)
      total.value = data.total
      page.value = data.page
      pages.value = data.pages
      moments.value = data.items as unknown as UserMoment[]
    } finally {
      loading.value = false
    }
  }

  // 获取当前用户的动态列表
  async function fetchMyMoments(p = 1, isDeleted = false) {
    loading.value = true
    try {
      const data = await requestMyMoments(p, 10, isDeleted)
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
    const data = await fetchMomentDraft()
    draft.value = data
    return data
  }

  // 保存草稿
  async function saveDraft(body: MomentPayload) {
    saving.value = true
    try {
      const data = await saveMomentDraft(body)
      draft.value = data
      return data
    } finally {
      saving.value = false
    }
  }

  // 发布动态
  async function publish(body: MomentPayload) {
    const data = await publishMoment(body)
    // 发布后清空草稿
    draft.value = null
    // 添加到列表开头
    moments.value.unshift(data)
    total.value++
    return data
  }

  async function updateMoment(id: string, body: MomentPayload) {
    const data = await requestUpdateMoment(id, body)
    moments.value = moments.value.map(moment => (moment.id === id ? data : moment))
    return data
  }

  // 删除动态
  async function deleteMoment(id: string, permanent = false) {
    await requestDeleteMoment(id, permanent)
    moments.value = moments.value.filter(m => m.id !== id)
    total.value--
  }

  async function restoreMoment(id: string) {
    const data = await requestRestoreMoment(id)
    moments.value = moments.value.filter(m => m.id !== id)
    total.value--
    return data
  }

  return {
    moments,
    draft,
    total,
    page,
    pages,
    loading,
    saving,
    fetchPublishedMoments,
    fetchMyMoments,
    fetchDraft,
    saveDraft,
    publish,
    updateMoment,
    deleteMoment,
    restoreMoment,
  }
})
