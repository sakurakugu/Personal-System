<script setup lang="ts">
import { defineAsyncComponent } from 'vue'
import MarkdownRenderer from '../../articles/components/MarkdownRenderer.vue'
import type { RenderedArticleMarkdown } from '../../articles/markdown'

defineProps<{
  title: string
  content: string
  articleViewMode: 'markdown' | 'mindmap'
  buildHeadingId: (index: number) => string
}>()

const emit = defineEmits<{
  rendered: [result: RenderedArticleMarkdown]
}>()

const MarkdownMindmap = defineAsyncComponent(() => import('../../articles/components/MarkdownMindmap.vue'))
</script>

<template>
  <div class="post-content-wrap">
    <MarkdownRenderer
      v-if="articleViewMode === 'markdown'"
      class="article-markdown-preview"
      :content="content"
      :build-heading-id="buildHeadingId"
      @rendered="emit('rendered', $event)"
    />
    <MarkdownMindmap
      v-else
      class="article-mindmap"
      :content="content"
      :title="title"
      :height="640"
    />
  </div>
</template>

<style scoped>
.post-content-wrap {
  padding: 1.25rem;
  border-radius: var(--radius-large);
  background: var(--card-bg-transparent);
  border: 1px solid rgba(255, 255, 255, 0.45);
  backdrop-filter: blur(18px);
  background-color: rgba(255, 255, 255, var(--overlay-card-opacity)) !important;
  transition: transform var(--transition-base), box-shadow var(--transition-base), background-color var(--transition-base), border-color var(--transition-base);
}

.dark .post-content-wrap {
  border-color: rgba(148, 163, 184, 0.16);
  background-color: rgba(15, 23, 42, var(--overlay-card-opacity)) !important;
}

.article-markdown-preview {
  width: 100%;
}

.article-markdown-preview h2,
.article-markdown-preview h3 {
  scroll-margin-top: 80px;
}

.article-mindmap {
  width: 100%;
  min-height: 640px;
}
</style>
