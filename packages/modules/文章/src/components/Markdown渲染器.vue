<script setup lang="ts">
import { nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { 增强文章Markdown } from '../composables/增强文章Markdown'
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
let 复制状态计时器: number | null = null
let 当前复制状态按钮: HTMLElement | null = null

function 应用Markdown增强() {
  if (!props.enableEnhance) {
    return
  }

  nextTick(() => {
    const element = containerRef.value
    if (element) {
      增强文章Markdown(element)
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

function 读取代码块纯文本(codeElement: HTMLElement): string {
  const lineElements = Array.from(codeElement.querySelectorAll<HTMLElement>('.article-code-line'))
  if (lineElements.length === 0) {
    return codeElement.textContent ?? ''
  }

  return lineElements.map((lineElement) => {
    const contentElement = lineElement.querySelector<HTMLElement>('.article-code-line-content')
    const content = contentElement?.innerText ?? contentElement?.textContent ?? ''
    return content === '\u00a0' ? '' : content
  }).join('\n')
}

async function 写入剪贴板(text: string) {
  if (navigator.clipboard?.writeText && window.isSecureContext) {
    await navigator.clipboard.writeText(text)
    return
  }

  const textarea = document.createElement('textarea')
  textarea.value = text
  textarea.setAttribute('readonly', 'true')
  textarea.style.position = 'fixed'
  textarea.style.insetInlineStart = '-9999px'
  textarea.style.insetBlockStart = '0'
  document.body.append(textarea)
  textarea.select()

  try {
    const copied = document.execCommand('copy')
    if (!copied) {
      throw new Error('复制命令执行失败')
    }
  } finally {
    textarea.remove()
  }
}

function 设置复制按钮状态(button: HTMLElement, state: 'success' | 'error') {
  if (当前复制状态按钮 && 当前复制状态按钮 !== button) {
    delete 当前复制状态按钮.dataset.copyState
  }

  当前复制状态按钮 = button
  button.dataset.copyState = state

  if (复制状态计时器 !== null) {
    window.clearTimeout(复制状态计时器)
  }

  复制状态计时器 = window.setTimeout(() => {
    delete button.dataset.copyState
    if (当前复制状态按钮 === button) {
      当前复制状态按钮 = null
    }
    复制状态计时器 = null
  }, 1600)
}

async function 处理代码复制点击(event: MouseEvent) {
  const target = event.target
  if (!(target instanceof HTMLElement)) {
    return
  }

  const button = target.closest<HTMLElement>('[data-article-code-copy]')
  if (!button) {
    return
  }

  const codeRoot = button.closest('.article-code-frame, .article-code-standalone')
  const codeElement = codeRoot?.querySelector<HTMLElement>('pre.article-code-block > code')
  if (!codeElement) {
    return
  }

  event.preventDefault()
  event.stopPropagation()

  try {
    await 写入剪贴板(读取代码块纯文本(codeElement))
    设置复制按钮状态(button, 'success')
  } catch (error) {
    console.error('[Markdown] 复制代码块失败', error)
    设置复制按钮状态(button, 'error')
  }
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

  if (复制状态计时器 !== null) {
    window.clearTimeout(复制状态计时器)
    复制状态计时器 = null
  }

  当前复制状态按钮 = null
})
</script>

<template>
  <!-- eslint-disable vue/no-v-text-v-html-on-component -->
  <component
    :is="tag"
    ref="containerRef"
    class="article-markdown-preview"
    @click="处理代码复制点击"
    v-html="renderedMarkdown.html"
  />
  <!-- eslint-enable vue/no-v-text-v-html-on-component -->
</template>
