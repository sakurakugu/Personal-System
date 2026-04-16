<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { enhanceArticleMarkdown } from '../composables/useArticleMarkdown'
import {
  renderArticleMarkdown,
  type RenderedArticleMarkdown,
} from '../utils/articleMarkdown'
import '../styles/article-markdown.css'

interface Props {
  content: string
  tag?: string
  enableEnhance?: boolean
  buildHeadingId?: (index: number) => string
}

const props = withDefaults(defineProps<Props>(), {
  tag: 'div',
  enableEnhance: true,
  buildHeadingId: undefined,
})

const emit = defineEmits<{
  rendered: [result: RenderedArticleMarkdown]
}>()

const containerRef = ref<globalThis.HTMLElement | null>(null)

const renderedMarkdown = computed(() => (
  renderArticleMarkdown(
    props.content,
    props.buildHeadingId ?? ((index) => `heading-${index}`),
  )
))

function 应用Markdown增强() {
  if (!props.enableEnhance) {
    return
  }

  nextTick(() => {
    const element = containerRef.value
    if (element) {
      enhanceArticleMarkdown(element)
    }
  })
}

watch(() => renderedMarkdown.value, (result) => {
  emit('rendered', result)
  应用Markdown增强()
}, { immediate: true })

watch(() => props.enableEnhance, (enabled) => {
  if (enabled) {
    应用Markdown增强()
  }
})
</script>

<template>
  <!-- eslint-disable vue/no-v-text-v-html-on-component -->
  <component
    :is="tag"
    ref="containerRef"
    class="article-markdown-preview"
    v-html="renderedMarkdown.html"
  />
  <!-- eslint-enable vue/no-v-text-v-html-on-component -->
</template>
