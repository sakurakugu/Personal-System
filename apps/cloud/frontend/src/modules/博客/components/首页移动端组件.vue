<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import type { CategoryRecord, TagRecord } from '@personal-system/module-articles'
import {
  BlogCalendarWidget,
  BlogCategoryListWidget,
  BlogSiteStatsWidget,
  BlogTagCloudWidget,
} from '@personal-system/module-blog/widgets'
import ProfileCard from './个人资料卡.vue'

defineProps<{
  rootClass: string
  categories: CategoryRecord[]
  popularTags: TagRecord[]
}>()

const emit = defineEmits<{
  tagClick: [name: string]
  categoryClick: [slug: string | null]
}>()

const rootRef = ref<globalThis.HTMLElement | null>(null)
const shouldRenderWidgets = ref(false)
let observer: globalThis.IntersectionObserver | null = null

function activateWidgets() {
  shouldRenderWidgets.value = true
  observer?.disconnect()
  observer = null
}

onMounted(() => {
  if (typeof window === 'undefined' || typeof window.IntersectionObserver === 'undefined') {
    activateWidgets()
    return
  }
  if (!rootRef.value) {
    activateWidgets()
    return
  }

  observer = new window.IntersectionObserver((entries) => {
    if (entries.some(entry => entry.isIntersecting)) {
      activateWidgets()
    }
  }, {
    rootMargin: '900px 0px',
    threshold: 0.01,
  })

  observer.observe(rootRef.value)
})

onBeforeUnmount(() => {
  observer?.disconnect()
  observer = null
})
</script>

<template>
  <div ref="rootRef" :class="rootClass">
    <div v-if="shouldRenderWidgets" class="mobile-bottom-widgets">
      <ProfileCard />
      <BlogTagCloudWidget :tags="popularTags" @tag-click="emit('tagClick', $event)" />
      <BlogCategoryListWidget :categories="categories" @category-click="emit('categoryClick', $event)" />
      <BlogSiteStatsWidget />
      <BlogCalendarWidget />
    </div>
    <div v-else class="mobile-bottom-widgets-placeholder" aria-hidden="true" />
  </div>
</template>

<style scoped>
.mobile-bottom-widgets {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.mobile-bottom-widgets-placeholder {
  min-height: 1px;
}
</style>
