<script setup lang="ts">
defineProps<{
  isMobileViewport: boolean
}>()
</script>

<template>
  <section class="ai-chat-empty" :class="{ 'ai-chat-empty--mobile': isMobileViewport }" aria-label="对话介绍">
    <div class="ai-chat-empty__inner">
      <h2>今天想聊什么？</h2>
    </div>
  </section>
</template>

<style scoped>
.ai-chat-empty {
  display: flex;
  min-height: 124px;
  align-items: center;
  justify-content: center;
}

.ai-chat-empty--mobile {
  min-height: 110px;
}

.ai-chat-empty__inner {
  display: flex;
  width: 100%;
  align-items: center;
  justify-content: center;
  animation: helpfulChatEmptyFadeIn 240ms ease-out both;
}

.ai-chat-empty h2 {
  margin: 0;
  color: #0f172a;
  font-size: 18px;
  font-weight: 500;
  line-height: 1.25;
  letter-spacing: 0;
  text-align: center;
}

.ai-chat-empty--mobile h2 {
  font-size: 17px;
}
</style>
