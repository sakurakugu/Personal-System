import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { fetchCategories, fetchTags } from './api'
import type { CategoryRecord, TagRecord } from './types'

export const useArticleTaxonomyStore = defineStore('article-taxonomy', () => {
  const categories = ref<CategoryRecord[]>([])
  const tags = ref<TagRecord[]>([])
  const loaded = ref(false)
  const loading = ref(false)
  let loadTask: Promise<void> | null = null

  const hasData = computed(() => categories.value.length > 0 || tags.value.length > 0)

  async function ensureLoaded(force = false): Promise<void> {
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
          fetchCategories(),
          fetchTags(),
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

  function upsertCategory(category: CategoryRecord) {
    const nextCategories = [...categories.value]
    const index = nextCategories.findIndex((item) => item.id === category.id)
    if (index === -1) {
      nextCategories.push(category)
    } else {
      nextCategories[index] = category
    }
    categories.value = nextCategories
  }

  function upsertTag(tag: TagRecord) {
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
    ensureLoaded,
    upsertCategory,
    upsertTag,
  }
})
