import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { 获取全部分类列表, 获取全部标签列表, 获取分类列表, 获取标签列表 } from './api'
import type { CategoryRecord, TagRecord } from './types'

type 文章分类加载模式 = 'visible' | 'all'

export const 使用文章分类存储 = defineStore('article-taxonomy', () => {
  const categories = ref<CategoryRecord[]>([])
  const tags = ref<TagRecord[]>([])
  const loaded = ref(false)
  const loadedMode = ref<文章分类加载模式 | null>(null)
  const loading = ref(false)
  let loadTask: Promise<void> | null = null
  let loadTaskMode: 文章分类加载模式 | null = null

  const hasData = computed(() => categories.value.length > 0 || tags.value.length > 0)

  async function 确保已加载(force = false, mode: 文章分类加载模式 = 'visible'): Promise<void> {
    if (!force && loaded.value && loadedMode.value === mode) {
      return
    }

    if (!force && loadTask && loadTaskMode === mode) {
      return loadTask
    }

    loadTaskMode = mode
    loadTask = (async () => {
      loading.value = true
      try {
        const loadCategories = mode === 'all' ? 获取全部分类列表 : 获取分类列表
        const loadTags = mode === 'all' ? 获取全部标签列表 : 获取标签列表
        const [categoryRecords, tagRecords] = await Promise.all([
          loadCategories(),
          loadTags(),
        ])
        categories.value = categoryRecords
        tags.value = tagRecords
        loaded.value = true
        loadedMode.value = mode
      } finally {
        loading.value = false
        loadTask = null
        loadTaskMode = null
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
    loadedMode,
    loading,
    hasData,
    ensureLoaded: 确保已加载,
    upsertCategory: 更新或创建分类,
    upsertTag: 更新或创建标签,
  }
})
