<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { 格式化文件大小 } from './chat';
import type { 聊天附件 } from './types';

const props = withDefaults(
  defineProps<{
    input: string
    attachments: readonly 聊天附件[]
    placeholder: string
    disabled?: boolean
    isGenerating: boolean
    canSend: boolean
    isMobileViewport: boolean
  }>(),
  {
    disabled: false,
  },
)

const emit = defineEmits<{
  'update:input': [value: string]
  addAttachments: [files: File[]]
  removeAttachment: [index: number]
  submit: []
  stop: []
  inputKeydown: [event: KeyboardEvent]
  focusInput: []
  blurInput: []
}>()

const textareaRef = ref<HTMLTextAreaElement | null>(null)
const fileInputRef = ref<HTMLInputElement | null>(null)
const attachmentMenuRef = ref<HTMLDivElement | null>(null)
const isInputFocused = ref(false)
const isAttachmentMenuOpen = ref(false)
const isDraggingFiles = ref(false)
const dragDepth = ref(0)

const fileInputAccept = 'image/*,.pdf'
const attachmentError = defineModel<string | null>('attachmentError', { default: null })

const imagePreviewUrls = computed(() =>
  props.attachments.map((attachment) =>
    attachment.url && attachment.mediaType.startsWith('image/') ? attachment.url : null,
  ),
)

function resizeTextarea() {
  const node = textareaRef.value
  if (!node) return

  const computedStyle = window.getComputedStyle(node)
  const lineHeight = Number.parseFloat(computedStyle.lineHeight) || 22
  const paddingTop = Number.parseFloat(computedStyle.paddingTop) || 0
  const paddingBottom = Number.parseFloat(computedStyle.paddingBottom) || 0
  const maxHeight = lineHeight * 10 + paddingTop + paddingBottom

  node.style.height = 'auto'
  node.style.height = `${Math.min(node.scrollHeight, maxHeight)}px`
  node.style.overflowY = node.scrollHeight > maxHeight ? 'auto' : 'hidden'
}

function 更新输入(event: Event) {
  emit('update:input', (event.target as HTMLTextAreaElement).value)
  void nextTick(resizeTextarea)
}

function 选择文件(files: File[]) {
  if (files.length === 0) return
  emit('addAttachments', files)
  isAttachmentMenuOpen.value = false
}

function 处理外部点击(event: PointerEvent) {
  if (!isAttachmentMenuOpen.value) return
  const target = event.target
  if (!(target instanceof Node)) return
  if (!attachmentMenuRef.value?.contains(target)) {
    isAttachmentMenuOpen.value = false
  }
}

function 处理拖入(event: DragEvent) {
  event.preventDefault()
  dragDepth.value += 1
  isDraggingFiles.value = true
}

function 处理拖离(event: DragEvent) {
  event.preventDefault()
  dragDepth.value = Math.max(0, dragDepth.value - 1)
  if (dragDepth.value === 0) {
    isDraggingFiles.value = false
  }
}

function 处理拖放(event: DragEvent) {
  event.preventDefault()
  dragDepth.value = 0
  isDraggingFiles.value = false
  选择文件(Array.from(event.dataTransfer?.files ?? []))
}

function 聚焦输入() {
  textareaRef.value?.focus()
}

defineExpose({
  聚焦输入,
  resizeTextarea,
})

watch(
  () => props.input,
  () => void nextTick(resizeTextarea),
)

onMounted(() => {
  document.addEventListener('pointerdown', 处理外部点击)
  void nextTick(resizeTextarea)
})

onBeforeUnmount(() => {
  document.removeEventListener('pointerdown', 处理外部点击)
})
</script>

<template>
  <form
    class="ai-chat-composer"
    :class="{ 'ai-chat-composer--mobile': isMobileViewport }"
    @submit.prevent="$emit('submit')"
    @dragover.prevent
    @dragenter="处理拖入"
    @dragleave="处理拖离"
    @drop="处理拖放"
  >
    <div class="ai-chat-composer__box" :class="{ 'ai-chat-composer__box--focused': isInputFocused, 'ai-chat-composer__box--dragging': isDraggingFiles }">
      <input
        ref="fileInputRef"
        type="file"
        multiple
        :accept="fileInputAccept"
        class="ai-chat-composer__file-input"
        @change="(event) => {
          选择文件(Array.from((event.target as HTMLInputElement).files ?? []))
          ;(event.target as HTMLInputElement).value = ''
        }"
      />

      <div v-if="isDraggingFiles" class="ai-chat-composer__drop-hint">松开后添加图片或 PDF</div>

      <div v-if="attachments.length > 0" class="ai-chat-composer__attachments">
        <div
          v-for="(attachment, index) in attachments"
          :key="attachment.id"
          class="ai-chat-composer__attachment"
        >
          <img v-if="imagePreviewUrls[index]" :src="imagePreviewUrls[index] ?? ''" :alt="attachment.filename" />
          <span v-else class="ai-chat-composer__attachment-type">
            {{ attachment.mediaType === 'application/pdf' ? 'PDF' : 'FILE' }}
          </span>
          <span class="ai-chat-composer__attachment-name" :title="attachment.filename">{{ attachment.filename }}</span>
          <span class="ai-chat-composer__attachment-size">{{ 格式化文件大小(attachment.size) }}</span>
          <button type="button" :aria-label="`移除 ${attachment.filename}`" @click="$emit('removeAttachment', index)">x</button>
        </div>
      </div>

      <textarea
        ref="textareaRef"
        :value="input"
        :placeholder="placeholder"
        :disabled="disabled"
        rows="2"
        enterkeyhint="send"
        @input="更新输入"
        @keydown="$emit('inputKeydown', $event)"
        @focus="() => {
          isInputFocused = true
          $emit('focusInput')
        }"
        @blur="() => {
          isInputFocused = false
          $emit('blurInput')
        }"
      />

      <div class="ai-chat-composer__toolbar">
        <div ref="attachmentMenuRef" class="ai-chat-composer__attachment-menu">
          <button
            type="button"
            class="ai-chat-composer__round-button ai-chat-composer__round-button--secondary"
            aria-label="打开附件菜单"
            :disabled="disabled"
            @click="isAttachmentMenuOpen = !isAttachmentMenuOpen"
          >
            <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path d="M12 5v14M5 12h14" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
            </svg>
          </button>

          <div v-if="isAttachmentMenuOpen" class="ai-chat-composer__menu">
            <button type="button" @click="fileInputRef?.click()">
              <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <path d="M21.4 11.6 12 21a6 6 0 0 1-8.5-8.5l9.9-9.9a4 4 0 1 1 5.7 5.7L9.2 18.2a2 2 0 0 1-2.8-2.8l9.2-9.2" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
              上传图片或 PDF
            </button>
          </div>
        </div>

        <button
          type="button"
          class="ai-chat-composer__round-button ai-chat-composer__round-button--primary"
          :class="{ 'ai-chat-composer__round-button--disabled': !isGenerating && !canSend }"
          :disabled="isGenerating ? false : !canSend"
          :aria-label="isGenerating ? '停止生成' : '发送消息'"
          @click="isGenerating ? $emit('stop') : $emit('submit')"
        >
          <span v-if="isGenerating" class="ai-chat-composer__stop" aria-hidden="true" />
          <svg v-else viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path d="M12 19V5m0 0-5 5m5-5 5 5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </button>
      </div>
    </div>

    <p v-if="attachmentError" class="ai-chat-composer__error" role="status" aria-live="polite">{{ attachmentError }}</p>
  </form>
</template>

<style scoped>
.ai-chat-composer {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 0 16px 16px;
  background: #fff;
}

.ai-chat-composer--mobile {
  padding: 8px 12px calc(10px + env(safe-area-inset-bottom, 0px));
}

.ai-chat-composer__box {
  display: flex;
  flex-direction: column;
  padding: 6px;
  border: 1px solid #e5e7eb;
  border-radius: 16px;
  background: #fff;
  transition: box-shadow 120ms ease, border-color 120ms ease, background 120ms ease;
}

.ai-chat-composer--mobile .ai-chat-composer__box {
  padding: 8px;
}

.ai-chat-composer__box--focused {
  border-color: #cbd5e1;
  box-shadow: 0 0 0 3px rgba(15, 23, 42, 0.06);
}

.ai-chat-composer__box--dragging {
  border-color: #94a3b8;
  background: #f8fafc;
}

.ai-chat-composer__file-input {
  display: none;
}

.ai-chat-composer__drop-hint {
  margin: 4px 8px 2px;
  padding: 6px 8px;
  border: 1px dashed #94a3b8;
  border-radius: 8px;
  color: #334155;
  background: #f1f5f9;
  font-size: 12px;
}

.ai-chat-composer--mobile .ai-chat-composer__drop-hint {
  margin: 6px 8px 2px;
}

.ai-chat-composer__attachments {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding: 4px 8px 2px;
}

.ai-chat-composer--mobile .ai-chat-composer__attachments {
  padding: 6px 8px 2px;
}

.ai-chat-composer__attachment {
  display: inline-flex;
  max-width: 240px;
  align-items: center;
  gap: 6px;
  padding: 2px 6px 2px 2px;
  border: 1px solid #e5e7eb;
  border-radius: 9999px;
  background: #fff;
}

.ai-chat-composer--mobile .ai-chat-composer__attachment {
  max-width: 100%;
}

.ai-chat-composer__attachment img,
.ai-chat-composer__attachment-type {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  border-radius: 9999px;
}

.ai-chat-composer__attachment img {
  object-fit: cover;
}

.ai-chat-composer__attachment-type {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #4b5563;
  background: #f3f4f6;
  font-size: 9px;
}

.ai-chat-composer__attachment-name {
  overflow: hidden;
  color: #111827;
  font-size: 11px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ai-chat-composer__attachment-size {
  flex-shrink: 0;
  color: #6b7280;
  font-size: 10px;
}

.ai-chat-composer__attachment button {
  display: inline-flex;
  width: 16px;
  height: 16px;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 9999px;
  color: #6b7280;
  background: transparent;
  cursor: pointer;
}

.ai-chat-composer textarea {
  width: 100%;
  min-height: 44px;
  padding: 8px 8px 12px;
  border: none;
  outline: none;
  color: #111827;
  background: transparent;
  font: inherit;
  font-size: 15px;
  line-height: 1.45;
  resize: none;
}

.ai-chat-composer--mobile textarea {
  min-height: 48px;
  padding: 8px 8px 10px;
  font-size: 16px;
}

.ai-chat-composer__toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 4px 2px;
}

.ai-chat-composer__attachment-menu {
  position: relative;
}

.ai-chat-composer__round-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 9999px;
  cursor: pointer;
}

.ai-chat-composer__round-button svg {
  display: block;
  width: 17px;
  height: 17px;
}

.ai-chat-composer__round-button--secondary {
  width: 30px;
  height: 30px;
  border: 1px solid #e5e7eb;
  color: #374151;
  background: #fff;
}

.ai-chat-composer__round-button--secondary svg {
  width: 16px;
  height: 16px;
}

.ai-chat-composer__round-button--primary {
  width: 36px;
  height: 36px;
  border: none;
  color: #fff;
  background: #111827;
}

.ai-chat-composer--mobile .ai-chat-composer__round-button--primary {
  width: 38px;
  height: 38px;
}

.ai-chat-composer__round-button--disabled {
  background: #d1d5db;
  cursor: default;
}

.ai-chat-composer__stop {
  display: block;
  width: 10px;
  height: 10px;
  border-radius: 2px;
  background: currentColor;
}

.ai-chat-composer__menu {
  position: absolute;
  bottom: 38px;
  left: 0;
  z-index: 5;
  width: 180px;
  padding: 6px;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  background: #fff;
  box-shadow: 0 8px 20px rgba(15, 23, 42, 0.12);
}

.ai-chat-composer--mobile .ai-chat-composer__menu {
  width: 168px;
}

.ai-chat-composer__menu button {
  display: inline-flex;
  width: 100%;
  align-items: center;
  gap: 6px;
  padding: 7px 8px;
  border: none;
  border-radius: 8px;
  color: #111827;
  background: transparent;
  cursor: pointer;
  font-size: 13px;
  text-align: left;
}

.ai-chat-composer__menu svg {
  width: 14px;
  height: 14px;
}

.ai-chat-composer__error {
  margin: 0;
  padding: 0 2px;
  color: #b91c1c;
  font-size: 12px;
  line-height: 1.3;
}

.ai-chat-composer--mobile .ai-chat-composer__error {
  padding: 0 4px;
}

</style>
