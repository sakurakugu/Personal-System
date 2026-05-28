<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{
  text: string
}>()

function 转义HTML(text: string): string {
  return text
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;')
}

function 渲染行内Markdown(text: string): string {
  return 转义HTML(text)
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g, '<a href="$2" target="_blank" rel="noreferrer">$1</a>')
}

const 渲染内容 = computed(() => {
  const lines = props.text.split(/\r?\n/)
  const blocks: string[] = []
  let listItems: string[] = []

  function flushList() {
    if (listItems.length === 0) return
    blocks.push(`<ul>${listItems.map((item) => `<li>${item}</li>`).join('')}</ul>`)
    listItems = []
  }

  for (const line of lines) {
    const trimmed = line.trim()
    if (!trimmed) {
      flushList()
      continue
    }

    const heading = trimmed.match(/^(#{1,3})\s+(.+)$/)
    if (heading) {
      flushList()
      const level = heading[1]?.length ?? 1
      blocks.push(`<h${level}>${渲染行内Markdown(heading[2] ?? '')}</h${level}>`)
      continue
    }

    const listItem = trimmed.match(/^[-*]\s+(.+)$/)
    if (listItem) {
      listItems.push(渲染行内Markdown(listItem[1] ?? ''))
      continue
    }

    flushList()
    blocks.push(`<p>${渲染行内Markdown(trimmed)}</p>`)
  }

  flushList()
  return blocks.join('')
})
</script>

<template>
  <div class="ai-chat-markdown" v-html="渲染内容" />
</template>

<style scoped>
.ai-chat-markdown {
  color: #111827;
  font-size: inherit;
  line-height: 1.5;
  overflow-wrap: anywhere;
}

.ai-chat-markdown :deep(p),
.ai-chat-markdown :deep(ul),
.ai-chat-markdown :deep(h1),
.ai-chat-markdown :deep(h2),
.ai-chat-markdown :deep(h3) {
  margin: 0 0 10px;
}

.ai-chat-markdown :deep(:last-child) {
  margin-bottom: 0;
}

.ai-chat-markdown :deep(h1) {
  font-size: 1.2rem;
  line-height: 1.3;
}

.ai-chat-markdown :deep(h2) {
  font-size: 1.1rem;
  line-height: 1.3;
}

.ai-chat-markdown :deep(h3) {
  font-size: 1rem;
  line-height: 1.3;
}

.ai-chat-markdown :deep(ul) {
  padding-left: 20px;
}

.ai-chat-markdown :deep(li + li) {
  margin-top: 6px;
}

.ai-chat-markdown :deep(a) {
  color: #0f172a;
  text-decoration: underline;
}

.ai-chat-markdown :deep(code) {
  padding: 2px 6px;
  border-radius: 6px;
  background: #f3f4f6;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New',
    monospace;
  font-size: 0.9em;
}
</style>
