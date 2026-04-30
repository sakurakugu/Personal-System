<script setup lang="ts">
import type { CategoryRecord, TagRecord } from '../../articles/types'
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
</script>

<template>
  <div :class="rootClass">
    <div class="mobile-bottom-widgets">
      <ProfileCard />
      <TagCloudWidget :tags="popularTags" @tag-click="emit('tagClick', $event)" />
      <CategoryListWidget :categories="categories" @category-click="emit('categoryClick', $event)" />
      <SiteStatsWidget />
      <CalendarWidget />
    </div>
  </div>
</template>

<style scoped>
.mobile-bottom-widgets {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
</style>
