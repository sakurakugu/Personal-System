<script setup lang="ts">
import type { CategoryRecord, TagRecord } from '@personal-system/module-articles'
import CategoryListWidget from './分类列表.vue'
import NavCard from './导航卡片.vue'
import ProfileCard from './个人资料卡.vue'
import TagCloudWidget from './标签云.vue'

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
