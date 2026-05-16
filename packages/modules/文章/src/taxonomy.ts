import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { 获取分类列表, 获取标签列表 } from './api'
import type { CategoryRecord, TagRecord } from './types'

export const 使用文章分类存储 = defineStore('article-taxonomy', () => {
  const categories = ref<CategoryRecord[]>([])
  const tags = ref<TagRecord[]>([])
  const loaded = ref(false)
  const loading = ref(false)
  let loadTask: Promise<void> | null = null

  const hasData = computed(() => categories.value.length > 0 || tags.value.length > 0)

  async function 确保已加载(force = false): Promise<void> {
    if (!force && loaded.value) {
      return
    }

    if (!force && loadTask) {
      return loadTask
    }

    loadTask = (async () => {
      loading.value = true
      try {
        const [categoryRecords, tagRecords] = await Promise.all([
          获取分类列表(),
          获取标签列表(),
        ])
        categories.value = categoryRecords
        tags.value = tagRecords
        loaded.value = true
      } finally {
        loading.value = false
        loadTask = null
      }
    })()

    return loadTask
  }

  function 更新或创建分类(category: CategoryRecord) {
    const nextCategories = [...categories.value]
    const index = nextCategories.findIndex((item) => item.id === category.id)
    if (index === -1) {
      nextCategories.push(category)
    } else {
      nextCategories[index] = category
    }
    categories.value = nextCategories
  }

  function 更新或创建标签(tag: TagRecord) {
    const nextTags = [...tags.value]
    const index = nextTags.findIndex((item) => item.id === tag.id)
    if (index === -1) {
      nextTags.push(tag)
    } else {
      nextTags[index] = tag
    }
    tags.value = nextTags
  }

  return {
    categories,
    tags,
    loaded,
    loading,
    hasData,
    ensureLoaded: 确保已加载,
    upsertCategory: 更新或创建分类,
    upsertTag: 更新或创建标签,
  }
})
