import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  删除动态 as 请求删除动态,
  获取动态草稿,
  获取我的动态 as 请求我的动态,
  获取已发布动态 as 请求已发布动态,
  发布动态,
  恢复动态 as 请求恢复动态,
  保存动态草稿,
  更新动态 as 请求更新动态,
} from './api'
import type { MomentDraft, MomentPayload, UserMoment } from './types'

export const 使用动态存储 = defineStore('moment', () => {
  const moments = ref<UserMoment[]>([])
  const total = ref(0)
  const page = ref(1)
  const pages = ref(0)
  const draft = ref<MomentDraft | null>(null)
  const loading = ref(false)
  const saving = ref(false)

  async function 获取已发布动态(p = 1) {
    loading.value = true
    try {
      const data = await 请求已发布动态(p)
      total.value = data.total
      page.value = data.page
      pages.value = data.pages
      moments.value = data.items as unknown as UserMoment[]
    } finally {
      loading.value = false
    }
  }

  async function 获取我的动态(p = 1, isDeleted = false) {
    loading.value = true
    try {
      const data = await 请求我的动态(p, 10, isDeleted)
      moments.value = data.items
      total.value = data.total
      page.value = data.page
      pages.value = data.pages
    } finally {
      loading.value = false
    }
  }

  async function 获取草稿() {
    const data = await 获取动态草稿()
    draft.value = data
    return data
  }

  async function 保存草稿(body: MomentPayload) {
    saving.value = true
    try {
      const data = await 保存动态草稿(body)
      draft.value = data
      return data
    } finally {
      saving.value = false
    }
  }

  async function 发布(body: MomentPayload) {
    const data = await 发布动态(body)
    draft.value = null
    moments.value.unshift(data)
    total.value += 1
    return data
  }

  async function 更新动态(id: string, body: MomentPayload) {
    const data = await 请求更新动态(id, body)
    moments.value = moments.value.map((moment) => (moment.id === id ? data : moment))
    return data
  }

  async function 删除动态(id: string, permanent = false) {
    await 请求删除动态(id, permanent)
    moments.value = moments.value.filter((moment) => moment.id !== id)
    total.value = Math.max(0, total.value - 1)
  }

  async function 恢复动态(id: string) {
    const data = await 请求恢复动态(id)
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
    获取已发布动态,
    获取我的动态,
    获取草稿,
    保存草稿,
    发布,
    更新动态,
    删除动态,
    恢复动态,
  }
})
