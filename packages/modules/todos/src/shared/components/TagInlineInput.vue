<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'

interface Props {
  modelValue: string
  existingTags: string[]
  placeholder?: string
}

type Segment = {
  kind: 'text' | 'tag'
  text: string
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: '',
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const editorRef = ref<globalThis.HTMLDivElement | null>(null)
const isFocused = ref(false)
const isComposing = ref(false)
const existingTagSet = computed(() => new Set(props.existingTags))

function normalizeValue(value: string): string {
  return value.replace(/\r?\n/g, '')
}

function pushTagPart(segments: Segment[], part: string) {
  if (!part) return
  const matched = part.match(/^(\s*)(.*?)(\s*)$/)
  const leading = matched?.[1] ?? ''
  const core = matched?.[2] ?? ''
  const trailing = matched?.[3] ?? ''

  if (leading) {
    segments.push({ kind: 'text', text: leading })
  }
  if (core) {
    segments.push({
      kind: existingTagSet.value.has(core) ? 'tag' : 'text',
      text: core,
    })
  }
  if (trailing) {
    segments.push({ kind: 'text', text: trailing })
  }
}

function buildSegments(value: string): Segment[] {
  const segments: Segment[] = []
  let buffer = ''

  for (const char of value) {
    if (char === ',' || char === '，') {
      pushTagPart(segments, buffer)
      buffer = ''
      segments.push({ kind: 'text', text: char })
      continue
    }
    buffer += char
  }

  pushTagPart(segments, buffer)
  return segments
}

function getEditorText(): string {
  return normalizeValue(editorRef.value?.textContent ?? '')
}

function getSelectionOffsets(root: globalThis.HTMLElement): { start: number, end: number } | null {
  const selection = window.getSelection()
  if (!selection || selection.rangeCount === 0) return null

  const range = selection.getRangeAt(0)
  if (!root.contains(range.startContainer) || !root.contains(range.endContainer)) {
    return null
  }

  const startRange = range.cloneRange()
  startRange.selectNodeContents(root)
  startRange.setEnd(range.startContainer, range.startOffset)

  const endRange = range.cloneRange()
  endRange.selectNodeContents(root)
  endRange.setEnd(range.endContainer, range.endOffset)

  return {
    start: startRange.toString().length,
    end: endRange.toString().length,
  }
}

function resolveTextPosition(root: globalThis.HTMLElement, offset: number): { node: globalThis.Node, offset: number } {
  const walker = document.createTreeWalker(root, window.NodeFilter.SHOW_TEXT)
  let traversed = 0
  let current = walker.nextNode()
  let lastTextNode: globalThis.Node | null = null

  while (current) {
    const length = current.textContent?.length ?? 0
    if (offset <= traversed + length) {
      return {
        node: current,
        offset: offset - traversed,
      }
    }
    traversed += length
    lastTextNode = current
    current = walker.nextNode()
  }

  if (lastTextNode) {
    return {
      node: lastTextNode,
      offset: lastTextNode.textContent?.length ?? 0,
    }
  }

  return {
    node: root,
    offset: root.childNodes.length,
  }
}

function setSelectionOffsets(root: globalThis.HTMLElement, start: number, end: number) {
  const selection = window.getSelection()
  if (!selection) return

  const range = document.createRange()
  const startPoint = resolveTextPosition(root, start)
  const endPoint = resolveTextPosition(root, end)

  range.setStart(startPoint.node, startPoint.offset)
  range.setEnd(endPoint.node, endPoint.offset)

  selection.removeAllRanges()
  selection.addRange(range)
}

function renderValue(value: string, preserveSelection: boolean) {
  const root = editorRef.value
  if (!root) return

  const selection = preserveSelection ? getSelectionOffsets(root) : null
  const fragment = document.createDocumentFragment()

  for (const segment of buildSegments(value)) {
    const span = document.createElement('span')
    span.className = segment.kind === 'tag' ? 'tag-inline-input__tag' : 'tag-inline-input__text'
    span.textContent = segment.text
    fragment.appendChild(span)
  }

  root.replaceChildren(fragment)

  if (selection) {
    setSelectionOffsets(root, selection.start, selection.end)
  }
}

function syncDomToModel() {
  const value = getEditorText()
  emit('update:modelValue', value)
  renderValue(value, true)
}

function handleInput() {
  if (isComposing.value) return
  syncDomToModel()
}

function handleCompositionStart() {
  isComposing.value = true
}

function handleCompositionEnd() {
  isComposing.value = false
  syncDomToModel()
}

function handleKeydown(event: globalThis.KeyboardEvent) {
  if (event.key === 'Enter') {
    event.preventDefault()
  }
}

function insertTextAtSelection(text: string) {
  const selection = window.getSelection()
  if (!selection || selection.rangeCount === 0) return

  const range = selection.getRangeAt(0)
  range.deleteContents()
  const textNode = document.createTextNode(text)
  range.insertNode(textNode)
  range.setStartAfter(textNode)
  range.collapse(true)

  selection.removeAllRanges()
  selection.addRange(range)
}

function handlePaste(event: globalThis.ClipboardEvent) {
  event.preventDefault()
  const text = normalizeValue(event.clipboardData?.getData('text') ?? '')
  insertTextAtSelection(text)
  syncDomToModel()
}

watch(
  () => [props.modelValue, props.existingTags.join('\u001f')],
  ([value]) => {
    if (isComposing.value) return
    renderValue(value, document.activeElement === editorRef.value)
  },
)

onMounted(() => {
  renderValue(props.modelValue, false)
})
</script>

<template>
  <div class="tag-inline-input" :class="{ 'is-focused': isFocused }">
    <div
      ref="editorRef"
      class="tag-inline-input__editor"
      contenteditable="true"
      role="textbox"
      aria-multiline="false"
      spellcheck="false"
      :data-placeholder="placeholder"
      @focus="isFocused = true"
      @blur="isFocused = false"
      @input="handleInput"
      @keydown="handleKeydown"
      @paste="handlePaste"
      @compositionstart="handleCompositionStart"
      @compositionend="handleCompositionEnd"
    />
  </div>
</template>

<style>
.tag-inline-input {
  width: 100%;
  min-height: var(--el-component-size);
  border-radius: var(--el-border-radius-base);
  background: var(--input-bg, var(--el-bg-color));
  box-shadow: 0 0 0 1px var(--el-border-color) inset;
  transition: box-shadow 0.2s;
  cursor: text;
  box-sizing: border-box;
}

.tag-inline-input:hover {
  box-shadow: 0 0 0 1px var(--el-border-color-hover) inset;
}

.tag-inline-input.is-focused {
  box-shadow: 0 0 0 1px var(--el-color-primary) inset;
}

.tag-inline-input__editor {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  width: 100%;
  min-height: calc(var(--el-component-size) - 2px);
  padding: 1px 11px;
  background: transparent;
  box-sizing: border-box;
  color: var(--el-text-color-regular);
  font-size: 14px;
  line-height: calc(var(--el-component-size) - 2px);
  overflow-x: auto;
  overflow-y: hidden;
  outline: none;
  caret-color: var(--el-text-color-regular);
}

.tag-inline-input__editor:empty::before {
  content: attr(data-placeholder);
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  color: var(--el-text-color-placeholder);
  line-height: 1;
  pointer-events: none;
}

.tag-inline-input__editor::-webkit-scrollbar {
  display: none;
}

.tag-inline-input__text {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  line-height: 1;
  white-space: pre;
}

.tag-inline-input__tag {
  display: inline-flex;
  align-items: center;
  height: 24px;
  box-sizing: border-box;
  padding: 0 8px;
  border: 1px solid var(--el-color-primary-light-5);
  border-radius: 4px;
  background: var(--el-fill-color-blank);
  color: var(--el-color-primary);
  font-size: inherit;
  line-height: 1;
  white-space: nowrap;
}

.dark .tag-inline-input {
  background: var(--input-bg, var(--el-bg-color));
}

.dark .tag-inline-input__editor {
  color: var(--text-primary);
  caret-color: var(--text-primary);
}

.dark .tag-inline-input__tag {
  border-color: rgb(var(--el-color-primary-rgb) / 0.35);
  background: rgb(var(--el-color-primary-rgb) / 0.16);
  color: var(--el-color-primary);
}
</style>
