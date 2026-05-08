<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import type { CategoryRecord, TagRecord } from '@personal-system/modules/articles'
import CalendarWidget from './CalendarWidget.vue'
import CategoryListWidget from './CategoryListWidget.vue'
import ProfileCard from './ProfileCard.vue'
import SiteStatsWidget from './SiteStatsWidget.vue'
import TagCloudWidget from './TagCloudWidget.vue'

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
      <TagCloudWidget :tags="popularTags" @tag-click="emit('tagClick', $event)" />
      <CategoryListWidget :categories="categories" @category-click="emit('categoryClick', $event)" />
      <SiteStatsWidget />
      <CalendarWidget />
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
