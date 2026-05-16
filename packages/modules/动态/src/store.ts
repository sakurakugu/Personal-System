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
  const moments = ref<UserMoment[]>([])
  const total = ref(0)
  const page = ref(1)
  const pages = ref(0)
  const draft = ref<MomentDraft | null>(null)
  const loading = ref(false)
  const saving = ref(false)

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

  async function fetchDraft() {
    const data = await fetchMomentDraft()
    draft.value = data
    return data
  }

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

  async function publish(body: MomentPayload) {
    const data = await publishMoment(body)
    draft.value = null
    moments.value.unshift(data)
    total.value += 1
    return data
  }

  async function updateMoment(id: string, body: MomentPayload) {
    const data = await requestUpdateMoment(id, body)
    moments.value = moments.value.map((moment) => (moment.id === id ? data : moment))
    return data
  }

  async function deleteMoment(id: string, permanent = false) {
    await requestDeleteMoment(id, permanent)
    moments.value = moments.value.filter((moment) => moment.id !== id)
    total.value = Math.max(0, total.value - 1)
  }

  async function restoreMoment(id: string) {
    const data = await requestRestoreMoment(id)
    moments.value = moments.value.filter((moment) => moment.id !== id)
    total.value = Math.max(0, total.value - 1)
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
