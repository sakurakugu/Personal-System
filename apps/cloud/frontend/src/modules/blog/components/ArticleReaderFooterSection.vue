<script setup lang="ts">
import type { ArticleMetaRecord, ArticleNavigationRecord } from '../../articles/types'
import ArticleLicense from './ArticleLicense.vue'
import ArticleNav from './ArticleNav.vue'
import ArticleRelated from './ArticleRelated.vue'

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
