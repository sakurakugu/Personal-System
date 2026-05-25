<script setup lang="ts">
import { BlogCalendarWidget, BlogSiteStatsWidget, BlogTocWidget } from '@personal-system/module-blog/widgets'

interface BlogTocItem {
  id: string
  text: string
  level: number
}

defineProps<{
  rootClass: string
  articleSlug: string
  articleToc: BlogTocItem[]
}>()

const emit = defineEmits<{
  itemClick: [id: string]
}>()
</script>

<template>
  <div :class="rootClass">
    <BlogSiteStatsWidget v-if="!(articleSlug && articleToc.length)" />
    <div class="sidebar-right-sticky">
      <template v-if="articleSlug && articleToc.length">
        <BlogTocWidget :toc="articleToc" @item-click="emit('itemClick', $event)" />
      </template>
      <template v-else>
        <BlogCalendarWidget />
      </template>
    </div>
  </div>
</template>

<style scoped>
.sidebar-right-sticky {
  display: flex;
  flex-direction: column;
  gap: 16px;
  position: sticky;
  top: 80px;
  width: 100%;
  min-width: 0;
  height: fit-content;
  align-self: stretch;
  transition:
    opacity var(--transition-slow) ease-in-out,
    transform var(--transition-slow) ease-in-out;
}
</style>
