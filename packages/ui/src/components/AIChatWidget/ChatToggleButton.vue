<script setup lang="ts">
import { Icon } from '@iconify/vue'

withDefaults(
  defineProps<{
    isOpen: boolean
    isMobile?: boolean
    unreadCount?: number
  }>(),
  {
    isMobile: false,
    unreadCount: 0,
  },
)

defineEmits<{
  toggle: []
}>()
</script>

<template>
  <button
    type="button"
    class="ai-chat-toggle"
    :class="{ 'ai-chat-toggle--open': isOpen, 'ai-chat-toggle--mobile': isMobile }"
    :aria-label="isOpen ? '关闭聊天' : '打开聊天'"
    @click="$emit('toggle')"
  >
    <span v-if="!isOpen && unreadCount > 0" class="ai-chat-toggle__unread">
      {{ unreadCount > 99 ? '99+' : unreadCount }}
    </span>
    <Icon
      class="ai-chat-toggle__icon"
      :icon="isOpen ? 'material-symbols:close-rounded' : 'material-symbols:chat-bubble-outline-rounded'"
      aria-hidden="true"
    />
  </button>
</template>

<style scoped>
.ai-chat-toggle {
  position: fixed;
  right: 16px;
  bottom: calc(0.5rem + var(--app-safe-area-bottom, 0px));
  z-index: 1200;
  display: flex;
  width: 3rem;
  height: 3rem;
  align-items: center;
  justify-content: center;
  padding: 0;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 1rem;
  color: var(--el-color-primary);
  background: var(--bg-card);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  backdrop-filter: blur(12px);
  cursor: pointer;
  pointer-events: auto;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.ai-chat-toggle:hover {
  background: var(--bg-hover);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.12);
  transform: translateY(-2px);
}

.ai-chat-toggle:active {
  transform: scale(0.9);
}

.dark .ai-chat-toggle {
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: var(--el-color-primary-light-3);
  background: oklch(0.22 0.015 var(--hue));
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.dark .ai-chat-toggle:hover {
  background: oklch(0.28 0.02 var(--hue));
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.4);
}

.ai-chat-toggle--mobile {
  right: 0.75rem;
  bottom: calc(0.25rem + var(--app-safe-area-bottom, 0px));
  width: 2.75rem;
  height: 2.75rem;
  border-radius: 0.875rem;
}

.ai-chat-toggle__unread {
  position: absolute;
  top: 0;
  right: 0;
  display: inline-flex;
  min-width: 20px;
  height: 20px;
  align-items: center;
  justify-content: center;
  padding: 0 5px;
  border: 1.5px solid #fff;
  border-radius: 9999px;
  color: #fff;
  background: #ef4444;
  font-size: 11px;
  font-weight: 700;
  line-height: 1;
}

.ai-chat-toggle--mobile .ai-chat-toggle__unread {
  top: -2px;
  right: -2px;
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  font-size: 10px;
}

.ai-chat-toggle__icon {
  display: block;
  width: 1.5rem;
  height: 1.5rem;
}

@media (max-width: 480px) {
  .ai-chat-toggle--mobile {
    right: 0.5rem;
    bottom: var(--app-safe-area-bottom, 0px);
    width: 2.5rem;
    height: 2.5rem;
    border-radius: 0.75rem;
  }

  .ai-chat-toggle__icon {
    width: 1.25rem;
    height: 1.25rem;
  }
}
</style>
