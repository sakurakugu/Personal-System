<script setup lang="ts">
import { 使用设置存储 } from '../../../shared/stores/settings'
import { ElButton, ElEmpty, ElSkeleton } from 'element-plus'
import ArticleReaderContentSection from './阅读器内容区.vue'
import ArticleReaderFooterSection from './阅读器页脚.vue'
import ArticleReaderHeaderSection from './阅读器标题区.vue'
import TwikooPanel from './评论面板.vue'
import { 使用文章阅读器 } from '../composables/使用文章阅读器'

const props = defineProps<{
  slug: string
}>()

const settings = 使用设置存储()

const emit = defineEmits<{
  back: []
  tagClick: [name: string]
  'update:toc': [items: TocItem[]]
}>()

interface TocItem {
  id: string
  text: string
  level: number
}

const {
  articleStore,
  articleAccessDenied,
  articleViewMode,
  prevArticle,
  nextArticle,
  relatedArticles,
  randomArticles,
  articleLiking,
  readingTimeInfo,
  articleViewModeOptions,
  siteTitle,
  articleUrl,
  articleCoverImage,
  articleCommentsPath,
  buildHeadingId,
  syncArticleToc,
  handleArticleNav,
  handleRelatedClick,
  handleLikeArticle,
  goSponsor,
  showLoginModal,
} = 使用文章阅读器({
  slug: () => props.slug,
  onTocUpdate: (items) => emit('update:toc', items),
})
</script>

<template>
  <div class="article-reader">
    <ElSkeleton :loading="articleStore.loading" animated>
      <template v-if="articleStore.current">
        <div class="post-container">
          <ArticleReaderHeaderSection
            :article="articleStore.current"
            :reading-time-info="readingTimeInfo"
            :article-view-mode="articleViewMode"
            :article-view-mode-options="articleViewModeOptions"
            :article-cover-image="articleCoverImage"
            :article-url="articleUrl"
            :site-title="siteTitle"
            :article-liking="articleLiking"
            @tag-click="emit('tagClick', $event)"
            @like="handleLikeArticle"
            @sponsor="goSponsor"
            @update:article-view-mode="articleViewMode = $event"
          />

          <ArticleReaderContentSection
            :title="articleStore.current.title"
            :content="articleStore.current.content"
            :article-view-mode="articleViewMode"
            :build-heading-id="buildHeadingId"
            @rendered="syncArticleToc"
          />

          <ArticleReaderFooterSection
            :title="articleStore.current.title"
            :author="articleStore.current.author.nickname || articleStore.current.author.username"
            :article-url="articleUrl"
            :pub-date="articleStore.current.published_at || articleStore.current.created_at"
            :prev-article="prevArticle"
            :next-article="nextArticle"
            :related-articles="relatedArticles"
            :random-articles="randomArticles"
            @navigate="handleArticleNav"
            @article-click="handleRelatedClick"
          />

          <TwikooPanel
            :path="articleCommentsPath"
            :hide-admin-entry="true"
            :visibility="settings.commentVisibility"
          />
        </div>
      </template>

      <ElEmpty v-else-if="!articleStore.loading && articleAccessDenied" description="该文章需要登录后查看">
        <ElButton type="primary" @click="showLoginModal">立即登录</ElButton>
      </ElEmpty>
      <ElEmpty v-else-if="!articleStore.loading" description="文章不存在" />
    </ElSkeleton>
  </div>
</template>

<style scoped>
.article-reader {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.post-container {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
</style>
