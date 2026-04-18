<script setup lang="ts">
import { ElButton, ElEmpty, ElSkeleton } from 'element-plus'
import ArticleCommentsSection from './ArticleCommentsSection.vue'
import ArticleReaderContentSection from './ArticleReaderContentSection.vue'
import ArticleReaderFooterSection from './ArticleReaderFooterSection.vue'
import ArticleReaderHeaderSection from './ArticleReaderHeaderSection.vue'
import { useArticleReader } from '../composables/useArticleReader'

const props = defineProps<{
  slug: string
}>()

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
  auth,
  comments,
  newComment,
  guestName,
  loadingComment,
  loadingCommentsConfig,
  commentsEnabled,
  commentsStealth,
  articleAccessDenied,
  replyingTo,
  replyContent,
  replyGuestName,
  loadingReply,
  articleViewMode,
  prevArticle,
  nextArticle,
  relatedArticles,
  randomArticles,
  readingTimeInfo,
  articleViewModeOptions,
  siteTitle,
  articleUrl,
  articleCoverImage,
  canViewComments,
  permissionMessage,
  buildHeadingId,
  syncArticleToc,
  handleArticleNav,
  handleRelatedClick,
  goSponsor,
  showLoginModal,
  submitComment,
  parseMentions,
  handleMentionClick,
  startReply,
  cancelReply,
  submitReply,
  canDeleteComment,
  deleteComment,
  toggleLike,
} = useArticleReader({
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
            @tag-click="emit('tagClick', $event)"
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

          <ArticleCommentsSection
            :is-authenticated="auth.isAuthenticated"
            :loading-comments-config="loadingCommentsConfig"
            :comments-enabled="commentsEnabled"
            :comments-stealth="commentsStealth"
            :can-view-comments="canViewComments"
            :permission-message="permissionMessage"
            :comments="comments"
            :replying-to="replyingTo"
            :reply-guest-name="replyGuestName"
            :reply-content="replyContent"
            :loading-reply="loadingReply"
            :guest-name="guestName"
            :new-comment="newComment"
            :loading-comment="loadingComment"
            :parse-mentions="parseMentions"
            :can-delete-comment="canDeleteComment"
            @show-login="showLoginModal"
            @update:guest-name="guestName = $event"
            @update:new-comment="newComment = $event"
            @update:reply-guest-name="replyGuestName = $event"
            @update:reply-content="replyContent = $event"
            @submit-comment="submitComment"
            @start-reply="startReply"
            @cancel-reply="cancelReply"
            @submit-reply="submitReply"
            @toggle-like="toggleLike"
            @delete-comment="deleteComment"
            @mention-click="handleMentionClick"
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

