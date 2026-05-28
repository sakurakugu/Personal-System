<script setup lang="ts">
import { computed, ref } from 'vue';
import type { 客服信息 } from './types';

const props = withDefaults(
  defineProps<{
    title: string
    isMobileViewport: boolean
    mobileTop?: string
    mobileHeight?: string
    activeSupport?: 客服信息 | null
  }>(),
  {
    mobileTop: '0px',
    mobileHeight: '100dvh',
    activeSupport: null,
  },
)

defineEmits<{
  close: []
  reset: []
}>()

const isResetHovered = ref(false)

const panelStyle = computed(() => {
  if (props.isMobileViewport) {
    return {
      top: props.mobileTop,
      height: props.mobileHeight,
    }
  }
  return {}
})
</script>

<template>
  <section class="ai-chat-panel" :class="{ 'ai-chat-panel--mobile': isMobileViewport }" :style="panelStyle" :aria-label="title">
    <header class="ai-chat-panel__header">
      <div v-if="activeSupport" class="ai-chat-panel__support">
        <div class="ai-chat-panel__avatar">
          <img v-if="activeSupport.pictureUrl" :src="activeSupport.pictureUrl" alt="" aria-hidden="true" />
          <span v-else>{{ activeSupport.name.slice(0, 1).toUpperCase() }}</span>
          <span v-if="activeSupport.isOnline" class="ai-chat-panel__online" aria-hidden="true" />
        </div>
        <div class="ai-chat-panel__support-text">
          <p>{{ activeSupport.name }}</p>
          <span :class="{ 'ai-chat-panel__status--online': activeSupport.isOnline }">
            {{ activeSupport.statusLabel ?? (activeSupport.isOnline ? '在线' : '离线') }}
          </span>
        </div>
      </div>
      <div v-else />

      <div class="ai-chat-panel__actions">
        <div class="ai-chat-panel__tooltip-host">
          <button
            type="button"
            class="ai-chat-panel__icon-button"
            aria-label="重置对话"
            @click="$emit('reset')"
            @mouseenter="isResetHovered = true"
            @mouseleave="isResetHovered = false"
            @focus="isResetHovered = true"
            @blur="isResetHovered = false"
          >
            <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path d="M3 12a9 9 0 1 0 3-6.7M3 4v5h5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </button>
          <div v-if="isResetHovered" class="ai-chat-panel__tooltip" role="tooltip">重置</div>
        </div>

        <button type="button" class="ai-chat-panel__icon-button" aria-label="关闭聊天" @click="$emit('close')">
          <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path d="M6 6l12 12M18 6 6 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
          </svg>
        </button>
      </div>
    </header>

    <slot />
  </section>
</template>

<style scoped>
.ai-chat-panel {
  position: fixed;
  right: 16px;
  bottom: 96px;
  z-index: 1000;
  display: flex;
  width: min(700px, calc(100vw - 20px));
  height: min(820px, calc(100vh - 116px));
  overflow: hidden;
  flex-direction: column;
  border-radius: 20px;
  background: #fff;
  box-shadow: 0 20px 48px rgba(15, 23, 42, 0.16), 0 3px 10px rgba(15, 23, 42, 0.08);
}

.ai-chat-panel--mobile {
  right: 0;
  bottom: auto;
  left: 0;
  width: 100vw;
  border-radius: 0;
  box-shadow: none;
}

.ai-chat-panel__header {
  position: relative;
  z-index: 10;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 10px;
  padding: 14px 16px 8px;
}

.ai-chat-panel--mobile .ai-chat-panel__header {
  padding: calc(8px + env(safe-area-inset-top, 0px)) 14px 8px;
}

.ai-chat-panel__support {
  display: flex;
  min-width: 0;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.ai-chat-panel__avatar {
  position: relative;
  display: flex;
  width: 30px;
  height: 30px;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border-radius: 9999px;
  color: #334155;
  background: #e2e8f0;
  font-size: 11px;
  font-weight: 600;
}

.ai-chat-panel__avatar img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.ai-chat-panel__online {
  position: absolute;
  right: 1px;
  bottom: 1px;
  width: 8px;
  height: 8px;
  border: 1.5px solid #fff;
  border-radius: 9999px;
  background: #22c55e;
}

.ai-chat-panel__support-text {
  min-width: 0;
}

.ai-chat-panel__support-text p,
.ai-chat-panel__support-text span {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ai-chat-panel__support-text p {
  margin: 0;
  color: #0f172a;
  font-size: 13px;
  font-weight: 600;
  line-height: 1.2;
}

.ai-chat-panel--mobile .ai-chat-panel__support-text p {
  font-size: 12px;
}

.ai-chat-panel__support-text span {
  margin-top: 1px;
  color: #64748b;
  font-size: 11px;
  line-height: 1.2;
}

.ai-chat-panel__support-text .ai-chat-panel__status--online {
  color: #166534;
}

.ai-chat-panel__actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.ai-chat-panel__tooltip-host {
  position: relative;
}

.ai-chat-panel__icon-button {
  display: inline-flex;
  width: 32px;
  height: 32px;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 9999px;
  color: #4b5563;
  background: transparent;
  cursor: pointer;
}

.ai-chat-panel--mobile .ai-chat-panel__icon-button {
  width: 36px;
  height: 36px;
}

.ai-chat-panel__icon-button svg {
  width: 16px;
  height: 16px;
}

.ai-chat-panel__tooltip {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  z-index: 20;
  padding: 6px 8px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  color: #111827;
  background: #fff;
  font-size: 11px;
  line-height: 1;
  pointer-events: none;
  white-space: nowrap;
}
</style>
