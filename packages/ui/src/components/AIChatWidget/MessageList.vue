<script setup lang="ts">
import EmptyState from './EmptyState.vue';
import MarkdownMessage from './MarkdownMessage.vue';
import type { 聊天消息 } from './types';

defineProps<{
  messages: readonly 聊天消息[]
  isGenerating: boolean
  errorMessage?: string
  isMobileViewport: boolean
}>()

function 是图片附件(mediaType: string): boolean {
  return mediaType.startsWith('image/')
}
</script>

<template>
  <div class="ai-chat-messages" :class="{ 'ai-chat-messages--mobile': isMobileViewport }">
    <div v-if="messages.length === 0" class="ai-chat-messages__empty">
      <EmptyState :is-mobile-viewport="isMobileViewport" />
    </div>

    <template v-for="message in messages" :key="message.id">
      <article v-if="message.role === 'user'" class="ai-chat-messages__user">
        <div v-if="message.attachments?.length" class="ai-chat-messages__files" :class="{ 'ai-chat-messages__files--with-text': message.content.trim() }">
          <a
            v-for="(attachment, index) in message.attachments"
            :key="`${message.id}-file-${index}-${attachment.url ?? attachment.filename}`"
            class="ai-chat-messages__file"
            :href="attachment.url"
            target="_blank"
            rel="noreferrer"
          >
            <img
              v-if="attachment.url && 是图片附件(attachment.mediaType)"
              :src="attachment.url"
              :alt="attachment.filename"
            />
            <span>{{ attachment.filename || `附件 ${index + 1}` }}</span>
          </a>
        </div>
        <p v-if="message.content.trim()">{{ message.content }}</p>
      </article>

      <div v-else-if="message.role === 'assistant' && message.content.trim()" class="ai-chat-messages__assistant">
        <article>
          <MarkdownMessage :text="message.content" />
        </article>
      </div>
    </template>

    <div v-if="isGenerating" class="ai-chat-messages__pending" aria-label="助手正在回复">
      <span />
    </div>

    <p v-if="errorMessage" class="ai-chat-messages__error">{{ errorMessage }}</p>
  </div>
</template>

<style scoped>
.ai-chat-messages {
  display: flex;
  min-height: 0;
  flex: 1;
  flex-direction: column;
  gap: 14px;
  overflow-y: auto;
  overscroll-behavior-y: contain;
  padding: 8px 18px 14px;
  -webkit-overflow-scrolling: touch;
}

.ai-chat-messages--mobile {
  gap: 16px;
  padding: 10px 14px 12px;
}

.ai-chat-messages__empty {
  display: flex;
  width: 100%;
  flex: 1;
  align-items: center;
  justify-content: center;
  padding: 2px 2px 4px;
}

.ai-chat-messages--mobile .ai-chat-messages__empty {
  padding: 4px 2px 2px;
}

.ai-chat-messages__user {
  max-width: 86%;
  align-self: flex-end;
  padding: 10px 14px;
  border: none;
  border-radius: 20px;
  color: #111827;
  background: #f3f4f6;
  box-shadow: none;
  font-size: 15px;
  line-height: 1.5;
}

.ai-chat-messages--mobile .ai-chat-messages__user {
  max-width: 90%;
  padding: 11px 14px;
  font-size: 16px;
}

.ai-chat-messages__user p {
  margin: 0;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.ai-chat-messages__files {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.ai-chat-messages__files--with-text {
  margin-bottom: 10px;
}

.ai-chat-messages__file {
  overflow: hidden;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  color: #111827;
  background: #fff;
  text-decoration: none;
}

.ai-chat-messages__file img {
  display: block;
  width: 100%;
  max-height: 220px;
  object-fit: cover;
}

.ai-chat-messages__file span {
  display: block;
  overflow: hidden;
  padding: 8px 10px;
  color: #374151;
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ai-chat-messages__file img + span {
  border-top: 1px solid #e5e7eb;
}

.ai-chat-messages__assistant {
  width: 100%;
  align-self: flex-start;
}

.ai-chat-messages__assistant article {
  max-width: 100%;
  padding: 0;
  border: none;
  border-radius: 0;
  color: #111827;
  background: transparent;
  box-shadow: none;
  font-size: 15px;
  line-height: 1.5;
}

.ai-chat-messages--mobile .ai-chat-messages__assistant article {
  font-size: 16px;
}

.ai-chat-messages__pending {
  display: inline-flex;
  width: 18px;
  height: 18px;
  align-items: center;
  justify-content: center;
  align-self: flex-start;
}

.ai-chat-messages__pending span {
  width: 8px;
  height: 8px;
  border-radius: 9999px;
  animation: helpfulChatDotPulse 1.1s ease-in-out infinite;
  background: #9ca3af;
}

.ai-chat-messages__error {
  margin: 0;
  color: #b91c1c;
  font-size: 14px;
}
</style>
