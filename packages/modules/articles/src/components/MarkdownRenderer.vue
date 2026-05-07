<script setup lang="ts">
import { nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { enhanceArticleMarkdown } from '../composables/useArticleMarkdown'
import {
  renderArticleMarkdown,
  type RenderedArticleMarkdown,
} from '../markdown'
import '../styles/article-markdown.css'

interface Props {
  content: string
  tag?: string
  enableEnhance?: boolean
  debounceMs?: number
  buildHeadingId?: (index: number) => string
}

const props = withDefaults(defineProps<Props>(), {
  tag: 'div',
  enableEnhance: true,
  debounceMs: 0,
  buildHeadingId: undefined,
})

const emit = defineEmits<{
  rendered: [result: RenderedArticleMarkdown]
}>()

const containerRef = ref<globalThis.HTMLElement | null>(null)
const renderedMarkdown = ref<RenderedArticleMarkdown>({
  html: '',
  headings: [],
})
let markdownRenderTimer: number | null = null

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

function 执行Markdown渲染() {
  renderedMarkdown.value = renderArticleMarkdown(
    props.content,
    props.buildHeadingId ?? ((index) => `heading-${index}`),
  )
}

function 调度Markdown渲染() {
  if (markdownRenderTimer !== null) {
    window.clearTimeout(markdownRenderTimer)
    markdownRenderTimer = null
  }

  if (props.debounceMs <= 0) {
    执行Markdown渲染()
    return
  }

  markdownRenderTimer = window.setTimeout(() => {
    markdownRenderTimer = null
    执行Markdown渲染()
  }, props.debounceMs)
}

watch(renderedMarkdown, (result) => {
  emit('rendered', result)
  应用Markdown增强()
}, { immediate: true })

watch(() => props.enableEnhance, (enabled) => {
  if (enabled) {
    应用Markdown增强()
  }
})

watch(
  [() => props.content, () => props.buildHeadingId, () => props.debounceMs],
  () => {
    调度Markdown渲染()
  },
  { immediate: true },
)

onBeforeUnmount(() => {
  if (markdownRenderTimer !== null) {
    window.clearTimeout(markdownRenderTimer)
    markdownRenderTimer = null
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
