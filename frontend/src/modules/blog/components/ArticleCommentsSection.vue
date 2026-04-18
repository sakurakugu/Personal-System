<script setup lang="ts">
import { ElButton, ElDivider, ElEmpty, ElInput } from 'element-plus'
import type { CommentRecord } from '../../../modules/comments/types'
import ArticleCommentItem from './ArticleCommentItem.vue'

interface MentionPart {
  type: 'text' | 'mention'
  value: string
}

const props = defineProps<{
  isAuthenticated: boolean
  loadingCommentsConfig: boolean
  commentsEnabled: boolean
  commentsStealth: boolean
  canViewComments: boolean
  permissionMessage: string
  comments: CommentRecord[]
  replyingTo: string | null
  replyGuestName: string
  replyContent: string
  loadingReply: boolean
  guestName: string
  newComment: string
  loadingComment: boolean
  parseMentions: (content: string) => MentionPart[]
  canDeleteComment: (comment: CommentRecord) => boolean
}>()

const emit = defineEmits<{
  'show-login': []
  'update:guestName': [value: string]
  'update:newComment': [value: string]
  'update:replyGuestName': [value: string]
  'update:replyContent': [value: string]
  'submit-comment': []
  'start-reply': [commentId: string]
  'cancel-reply': []
  'submit-reply': [parentId: string]
  'toggle-like': [comment: CommentRecord]
  'delete-comment': [comment: CommentRecord]
  'mention-click': [targetName: string, currentCommentId: string]
}>()
</script>

<template>
  <div v-if="!props.loadingCommentsConfig && props.commentsEnabled && props.canViewComments" class="comments-card">
    <div class="comments-header">评论</div>
    <div v-if="props.comments.length" class="comment-list">
      <ArticleCommentItem
        v-for="comment in props.comments"
        :key="comment.id"
        :comment="comment"
        :root-comment-id="comment.id"
        :is-authenticated="props.isAuthenticated"
        :replying-to="props.replyingTo"
        :reply-guest-name="props.replyGuestName"
        :reply-content="props.replyContent"
        :loading-reply="props.loadingReply"
        :parse-mentions="props.parseMentions"
        :can-delete-comment="props.canDeleteComment"
        @mention-click="(targetName, currentCommentId) => emit('mention-click', targetName, currentCommentId)"
        @start-reply="emit('start-reply', $event)"
        @update:reply-guest-name="emit('update:replyGuestName', $event)"
        @update:reply-content="emit('update:replyContent', $event)"
        @cancel-reply="emit('cancel-reply')"
        @submit-reply="emit('submit-reply', $event)"
        @toggle-like="emit('toggle-like', $event)"
        @delete-comment="emit('delete-comment', $event)"
      />
    </div>
    <ElEmpty v-else description="暂无评论，来抢沙发吧！" />

    <ElDivider />

    <div class="comment-form">
      <ElInput
        v-if="!props.isAuthenticated"
        :model-value="props.guestName"
        placeholder="你的昵称"
        size="small"
        style="margin-bottom: 8px; max-width: 200px"
        @update:model-value="emit('update:guestName', String($event))"
      />
      <ElInput
        :model-value="props.newComment"
        type="textarea"
        placeholder="写下你的评论..."
        :rows="3"
        @update:model-value="emit('update:newComment', String($event))"
      />
      <div class="comment-submit-row">
        <ElButton
          type="primary"
          :loading="props.loadingComment"
          @click="emit('submit-comment')"
        >
          发表评论
        </ElButton>
      </div>
    </div>
  </div>

  <div v-else-if="!props.loadingCommentsConfig && props.commentsEnabled && !props.canViewComments" class="comments-card">
    <div class="comments-header">评论</div>
    <ElEmpty :description="props.permissionMessage">
      <ElButton v-if="!props.isAuthenticated" type="primary" @click="emit('show-login')">立即登录</ElButton>
    </ElEmpty>
  </div>

  <div v-else-if="!props.loadingCommentsConfig && !props.commentsStealth" class="comments-card">
    <div class="comments-header">评论</div>
    <ElEmpty description="评论功能已关闭" />
  </div>
</template>

<style scoped>
.comments-card {
  padding: 1rem 1.25rem 1.25rem;
  border-radius: var(--radius-large);
  background: var(--card-bg-transparent);
  border: 1px solid rgba(255, 255, 255, 0.45);
  backdrop-filter: blur(18px);
  background-color: rgba(255, 255, 255, var(--overlay-card-opacity)) !important;
  transition: transform var(--transition-base), box-shadow var(--transition-base), background-color var(--transition-base), border-color var(--transition-base);
}

.dark .comments-card {
  border-color: rgba(148, 163, 184, 0.16);
  background-color: rgba(15, 23, 42, var(--overlay-card-opacity)) !important;
}

.comments-header {
  font-weight: 700;
  font-size: 1rem;
  padding-bottom: 0;
  margin-bottom: 0.75rem;
  border-bottom: none;
  color: var(--text-primary);
  position: relative;
  padding-left: 0.75rem;
}

.comments-header::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0.125rem;
  width: 0.25rem;
  height: 1rem;
  border-radius: 0.25rem;
  background-color: var(--el-color-primary);
}

.comment-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.comment-submit-row {
  margin-top: 8px;
  display: flex;
  justify-content: flex-end;
}

.comment-form :deep(.el-textarea__inner) {
  border-radius: 8px;
}
</style>
