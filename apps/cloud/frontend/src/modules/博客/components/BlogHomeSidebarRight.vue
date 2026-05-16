<script setup lang="ts">
import { defineAsyncComponent } from 'vue'
import SiteStatsWidget from './SiteStatsWidget.vue'
import CalendarWidget from './CalendarWidget.vue'

const BlogTocWidget = defineAsyncComponent(() => import('./BlogTocWidget.vue'))

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
    <SiteStatsWidget v-if="!(articleSlug && articleToc.length)" />
    <div class="sidebar-right-sticky">
      <template v-if="articleSlug && articleToc.length">
        <BlogTocWidget :toc="articleToc" @item-click="emit('itemClick', $event)" />
      </template>
      <template v-else>
        <CalendarWidget />
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
