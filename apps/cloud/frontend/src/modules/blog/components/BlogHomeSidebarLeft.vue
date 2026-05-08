<script setup lang="ts">
import type { CategoryRecord, TagRecord } from '@personal-system/modules/articles'
import CategoryListWidget from './CategoryListWidget.vue'
import NavCard from './NavCard.vue'
import ProfileCard from './ProfileCard.vue'
import TagCloudWidget from './TagCloudWidget.vue'

defineProps<{
  topClass: string
  stickyClass: string
  categories: CategoryRecord[]
  popularTags: TagRecord[]
}>()

const emit = defineEmits<{
  tagClick: [name: string]
  categoryClick: [slug: string | null]
}>()
</script>

<template>
  <div :class="topClass">
    <ProfileCard />
  </div>

  <aside :class="stickyClass">
    <NavCard />
    <TagCloudWidget :tags="popularTags" @tag-click="emit('tagClick', $event)" />
    <CategoryListWidget :categories="categories" @category-click="emit('categoryClick', $event)" />
  </aside>
</template>
