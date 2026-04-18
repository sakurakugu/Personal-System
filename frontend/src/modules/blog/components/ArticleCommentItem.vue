<script setup lang="ts">
import { ElButton, ElInput } from 'element-plus'
import type { CommentRecord } from '../../../modules/comments/types'

defineOptions({
  name: 'ArticleCommentItem',
})

interface MentionPart {
  type: 'text' | 'mention'
  value: string
}

const props = defineProps<{
  comment: CommentRecord
  rootCommentId: string
  isAuthenticated: boolean
  replyingTo: string | null
  replyGuestName: string
  replyContent: string
  loadingReply: boolean
  parseMentions: (content: string) => MentionPart[]
  canDeleteComment: (comment: CommentRecord) => boolean
}>()

const emit = defineEmits<{
  'mention-click': [targetName: string, currentCommentId: string]
  'start-reply': [commentId: string]
  'update:replyGuestName': [value: string]
  'update:replyContent': [value: string]
  'cancel-reply': []
  'submit-reply': [parentId: string]
  'toggle-like': [comment: CommentRecord]
  'delete-comment': [comment: CommentRecord]
}>()

function getCommentDisplayName(comment: CommentRecord): string {
  return comment.user?.nickname || comment.user?.username || comment.guest_name || '匿名'
}
</script>

<template>
  <div
    :id="`comment-${props.comment.id}`"
    class="comment-item"
    :class="{ reply: props.rootCommentId !== props.comment.id }"
  >
    <div class="comment-header">
      <span class="comment-author">{{ getCommentDisplayName(props.comment) }}</span>
      <span class="comment-time">{{ new Date(props.comment.created_at).toLocaleString() }}</span>
    </div>
    <p class="comment-content">
      <template v-for="(part, idx) in props.parseMentions(props.comment.content)" :key="idx">
        <span v-if="part.type === 'text'">{{ part.value }}</span>
        <span
          v-else
          class="mention-link"
          @click="emit('mention-click', part.value, props.comment.id)"
        >
          @{{ part.value }}
        </span>
      </template>
    </p>

    <div class="comment-actions">
      <ElButton
        link
        :type="props.comment.is_liked ? 'danger' : 'info'"
        size="small"
        @click="emit('toggle-like', props.comment)"
      >
        <span style="margin-right: 4px">{{ props.comment.is_liked ? '❤️' : '🤍' }}</span>
        {{ props.comment.like_count > 0 ? props.comment.like_count : '点赞' }}
      </ElButton>
      <ElButton link type="primary" size="small" @click="emit('start-reply', props.comment.id)">
        回复
      </ElButton>
      <ElButton
        v-if="props.canDeleteComment(props.comment)"
        link
        type="danger"
        size="small"
        @click="emit('delete-comment', props.comment)"
      >
        删除
      </ElButton>
    </div>

    <div v-if="props.replyingTo === props.comment.id" class="reply-form">
      <ElInput
        v-if="!props.isAuthenticated"
        :model-value="props.replyGuestName"
        placeholder="你的昵称"
        size="small"
        style="margin-bottom: 8px; max-width: 200px"
        @update:model-value="emit('update:replyGuestName', String($event))"
      />
      <ElInput
        :model-value="props.replyContent"
        type="textarea"
        :placeholder="`回复 @${getCommentDisplayName(props.comment)}...`"
        :rows="2"
        @update:model-value="emit('update:replyContent', String($event))"
      />
      <div class="reply-actions">
        <ElButton size="small" @click="emit('cancel-reply')">取消</ElButton>
        <ElButton
          type="primary"
          size="small"
          :loading="props.loadingReply"
          @click="emit('submit-reply', props.rootCommentId)"
        >
          提交回复
        </ElButton>
      </div>
    </div>

    <div v-if="props.comment.replies?.length" class="replies">
      <ArticleCommentItem
        v-for="reply in props.comment.replies"
        :key="reply.id"
        :comment="reply"
        :root-comment-id="props.rootCommentId"
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
  </div>
</template>

<style scoped>
.comment-item {
  padding: 12px;
  background: #f9f9f9;
  border-radius: 8px;
}

.dark .comment-item {
  background: var(--bg-hover);
}

.comment-header {
  margin-bottom: 10px;
}

.comment-author {
  font-weight: 700;
  color: var(--text-primary);
}

.comment-time {
  font-size: 12px;
  margin-left: 8px;
  color: var(--text-secondary);
}

.comment-content {
  font-size: 14px;
  color: #444;
  margin: 0;
}

.dark .comment-content {
  color: var(--text-secondary);
}

.replies {
  margin-top: 12px;
  padding-left: 20px;
  border-left: 2px solid #e0e0e0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.dark .replies {
  border-left-color: var(--border-color);
}

.reply {
  background: #f0f4f0;
}

.dark .reply {
  background: var(--bg-primary);
}

.mention-link {
  color: var(--el-color-primary);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-base);
}

.mention-link:hover {
  color: var(--el-color-primary-dark-2);
  text-decoration: underline;
}

.dark .mention-link {
  color: var(--el-color-primary-light-5);
}

.dark .mention-link:hover {
  color: var(--el-color-primary-light-3);
}

.comment-highlight {
  animation: highlight-pulse 2s ease;
}

@keyframes highlight-pulse {
  0% {
    background-color: var(--theme-accent-overlay-30);
  }
  100% {
    background-color: transparent;
  }
}

.dark .comment-highlight {
  animation: highlight-pulse-dark 2s ease;
}

@keyframes highlight-pulse-dark {
  0% {
    background-color: rgba(74, 222, 128, 0.3);
  }
  100% {
    background-color: transparent;
  }
}

.comment-actions {
  margin-top: 8px;
}

.reply-form {
  margin-top: 12px;
  padding: 12px;
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
}

.dark .reply-form {
  background: var(--bg-secondary);
  border-color: var(--border-color);
}

.reply-actions {
  margin-top: 8px;
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.reply-form :deep(.el-textarea__inner) {
  border-radius: 8px;
}
</style>
