<script setup lang="ts">
import type { ArticleMetaRecord, ArticleNavigationRecord } from '@personal-system/module-articles'
import ArticleLicense from './文章许可.vue'
import ArticleNav from './文章导航.vue'
import ArticleRelated from './相关文章.vue'

defineProps<{
  title: string
  author: string
  articleUrl: string
  pubDate: string | null | undefined
  prevArticle: ArticleNavigationRecord | null
  nextArticle: ArticleNavigationRecord | null
  relatedArticles: ArticleMetaRecord[]
  randomArticles: ArticleMetaRecord[]
}>()

const emit = defineEmits<{
  navigate: [slug: string]
  articleClick: [slug: string]
}>()
</script>

<template>
  <div class="article-footer-section">
    <ArticleLicense
      :title="title"
      :author="author"
      :url="articleUrl"
      :pub-date="pubDate"
    />

    <ArticleNav
      :prev="prevArticle"
      :next="nextArticle"
      @nav-click="emit('navigate', $event)"
    />

    <ArticleRelated
      :related-articles="relatedArticles"
      :random-articles="randomArticles"
      @article-click="emit('articleClick', $event)"
    />
  </div>
</template>

<style scoped>
.article-footer-section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
</style>
