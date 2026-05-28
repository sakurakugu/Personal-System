<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import ChatToggleButton from './ChatToggleButton.vue'
import Composer from './Composer.vue'
import MessageList from './MessageList.vue'
import WidgetPanel from './WidgetPanel.vue'
import {
    提取JSON文本,
    是否支持附件,
    生成消息ID,
    生成附件,
    解析数据流行,
    转为接口消息,
    释放附件地址,
} from './chat'
import type { 客服信息, 聊天请求调整器, 聊天请求配置, 聊天消息, 聊天状态, 聊天附件 } from './types'

interface Props {
  url?: string
  headers?: HeadersInit
  beforeRequest?: 聊天请求调整器
  title?: string
  placeholder?: string
  disabled?: boolean
  disableReasoning?: boolean
  activeSupport?: 客服信息 | null
}

const props = withDefaults(defineProps<Props>(), {
  url: '/api/chat',
  headers: undefined,
  beforeRequest: undefined,
  title: 'Helpful Chat',
  placeholder: '输入问题...',
  disabled: false,
  disableReasoning: false,
  activeSupport: null,
})

const 是否打开 = ref(false)
const 输入内容 = ref('')
const 附件列表 = ref<聊天附件[]>([])
const 消息列表 = ref<聊天消息[]>([])
const 状态 = ref<聊天状态>('空闲')
const 错误消息 = ref('')
const 附件错误 = ref<string | null>(null)
const 是否移动端 = ref(false)
const 视口高度 = ref(0)
const 视口顶部偏移 = ref(0)
const 输入组件 = ref<InstanceType<typeof Composer> | null>(null)
const 面板容器 = ref<HTMLElement | null>(null)
const 切换按钮容器 = ref<HTMLElement | null>(null)
let 当前请求控制器: AbortController | null = null

const 是否请求中 = computed(() => 状态.value === '请求中')
const 是否可发送 = computed(
  () =>
    (输入内容.value.trim().length > 0 || 附件列表.value.length > 0) &&
    !是否请求中.value &&
    !props.disabled,
)
const 是否显示等待回复 = computed(() => {
  if (!是否请求中.value) return false
  const lastMessage = 消息列表.value.at(-1)
  return lastMessage?.role === 'assistant' && !lastMessage.content.trim()
})
const 移动端面板高度 = computed(() => (视口高度.value > 0 ? `${Math.round(视口高度.value)}px` : '100dvh'))
const 移动端面板顶部 = computed(() =>
  视口顶部偏移.value > 0 ? `${Math.round(视口顶部偏移.value)}px` : '0px',
)

async function 滚动到底部() {
  await nextTick()
  const container = document.querySelector<HTMLElement>('.ai-chat-messages')
  if (!container) return
  container.scrollTo({
    top: container.scrollHeight,
    behavior: 是否请求中.value ? 'auto' : 'smooth',
  })
}

function 更新移动端状态() {
  是否移动端.value = window.innerWidth <= 768
}

function 更新视觉视口() {
  视口高度.value = window.visualViewport?.height ?? window.innerHeight
  视口顶部偏移.value = window.visualViewport?.offsetTop ?? 0
}

function 打开或关闭() {
  是否打开.value = !是否打开.value
  if (是否打开.value) {
    void nextTick(() => 输入组件.value?.聚焦输入())
  }
}

function 关闭面板() {
  是否打开.value = false
  输入组件.value?.聚焦输入()
  requestAnimationFrame(() => document.activeElement instanceof HTMLElement && document.activeElement.blur())
}

function 释放消息附件() {
  for (const message of 消息列表.value) {
    释放附件地址(message.attachments ?? [])
  }
}

function 清空对话() {
  停止生成()
  释放消息附件()
  释放附件地址(附件列表.value)
  消息列表.value = []
  附件列表.value = []
  输入内容.value = ''
  错误消息.value = ''
  附件错误.value = null
  状态.value = '空闲'
  void nextTick(() => 输入组件.value?.聚焦输入())
}

function 停止生成() {
  当前请求控制器?.abort()
  当前请求控制器 = null
  if (状态.value === '请求中') {
    状态.value = '空闲'
  }
}

function 添加附件(files: File[]) {
  const supportedFiles: File[] = []
  const rejectedFileNames: string[] = []

  for (const file of files) {
    if (是否支持附件(file)) {
      supportedFiles.push(file)
    } else {
      rejectedFileNames.push(file.name)
    }
  }

  if (supportedFiles.length > 0) {
    const existing = new Map<string, 聊天附件>()
    for (const attachment of 附件列表.value) {
      existing.set(`${attachment.filename}:${attachment.size}`, attachment)
    }
    for (const file of supportedFiles) {
      const key = `${file.name}:${file.size}`
      if (!existing.has(key)) {
        existing.set(key, 生成附件(file))
      }
    }
    附件列表.value = Array.from(existing.values())
  }

  if (rejectedFileNames.length > 0) {
    const previewNames = rejectedFileNames.slice(0, 3).join(', ')
    const suffix = rejectedFileNames.length > 3 ? ` +${rejectedFileNames.length - 3} 个` : ''
    附件错误.value = `不支持的文件类型：${previewNames}${suffix}。仅支持图片或 PDF。`
  } else {
    附件错误.value = null
  }
}

function 移除附件(index: number) {
  const nextAttachments = [...附件列表.value]
  const [removed] = nextAttachments.splice(index, 1)
  if (removed) {
    释放附件地址([removed])
  }
  附件列表.value = nextAttachments
}

async function 读取流式响应(response: Response, assistantMessage: 聊天消息) {
  const reader = response.body?.getReader()
  if (!reader) {
    assistantMessage.content = await response.text()
    return
  }

  const decoder = new TextDecoder()
  let buffer = ''
  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split(/\r?\n/)
    buffer = lines.pop() ?? ''
    for (const line of lines) {
      assistantMessage.content += 解析数据流行(line)
    }
    await 滚动到底部()
  }

  const tail = buffer + decoder.decode()
  if (tail.trim()) {
    assistantMessage.content += 解析数据流行(tail)
  }
}

function 生成请求体(messages: 聊天消息[], attachments: readonly 聊天附件[]): BodyInit {
  if (attachments.length === 0) {
    return JSON.stringify({ messages: 转为接口消息(messages) })
  }

  const formData = new FormData()
  formData.append('messages', JSON.stringify(转为接口消息(messages)))
  for (const attachment of attachments) {
    if (attachment.file) {
      formData.append('files', attachment.file, attachment.filename)
    }
  }
  return formData
}

function 生成请求头(hasAttachments: boolean): HeadersInit {
  const headers = new Headers({
    Accept: 'text/event-stream, application/x-ndjson, application/json, text/plain',
  })
  if (props.headers) {
    new Headers(props.headers).forEach((value, key) => headers.set(key, value))
  }
  if (!hasAttachments) {
    headers.set('Content-Type', 'application/json')
  }
  return headers
}

async function 发送消息() {
  const text = 输入内容.value.trim()
  if ((!text && 附件列表.value.length === 0) || 是否请求中.value || props.disabled) {
    return
  }

  const messageAttachments = 附件列表.value
  const userMessage: 聊天消息 = {
    id: 生成消息ID(),
    role: 'user',
    content: text,
    attachments: messageAttachments,
    createdAt: Date.now(),
  }
  const assistantMessage: 聊天消息 = {
    id: 生成消息ID(),
    role: 'assistant',
    content: '',
    createdAt: Date.now(),
  }

  输入内容.value = ''
  附件列表.value = []
  错误消息.value = ''
  附件错误.value = null
  状态.value = '请求中'
  消息列表.value.push(userMessage, assistantMessage)
  await 滚动到底部()

  当前请求控制器 = new AbortController()
  const messagesForApi = 消息列表.value.filter((message) => message.id !== assistantMessage.id)
  const hasAttachments = messageAttachments.length > 0

  try {
    console.info('[AIChatWidget] 开始请求聊天接口', {
      url: props.url,
      messageCount: messagesForApi.length,
      attachmentCount: messageAttachments.length,
    })
    const baseConfig: 聊天请求配置 = {
      url: props.url,
      init: {
        method: 'POST',
        headers: 生成请求头(hasAttachments),
        credentials: 'include',
        signal: 当前请求控制器.signal,
        body: 生成请求体(messagesForApi, messageAttachments),
      },
      context: { hasAttachments },
    }
    const requestConfig = (await props.beforeRequest?.(baseConfig)) ?? baseConfig
    const response = await fetch(requestConfig.url, requestConfig.init)

    if (!response.ok) {
      throw new Error(`聊天接口返回 ${response.status}`)
    }

    const contentType = response.headers.get('content-type') || ''
    if (contentType.includes('application/json')) {
      assistantMessage.content = 提取JSON文本(await response.json())
    } else {
      await 读取流式响应(response, assistantMessage)
    }

    if (!assistantMessage.content.trim()) {
      assistantMessage.content = '接口已响应，但没有返回可显示内容。'
    }
    状态.value = '空闲'
    console.info('[AIChatWidget] 聊天接口请求完成')
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      console.info('[AIChatWidget] 聊天请求已停止')
      状态.value = '空闲'
      return
    }
    const message = error instanceof Error ? error.message : '聊天请求失败'
    错误消息.value = message
    assistantMessage.content = `请求失败：${message}`
    状态.value = '失败'
    console.error('[AIChatWidget] 聊天请求失败', error)
  } finally {
    当前请求控制器 = null
    await 滚动到底部()
  }
}

function 处理键盘(event: KeyboardEvent) {
  if (event.key !== 'Enter' || event.shiftKey || event.isComposing) {
    return
  }
  event.preventDefault()
  void 发送消息()
}

function 处理外部点击(event: PointerEvent) {
  if (!是否打开.value) return
  const target = event.target
  if (!(target instanceof Node)) return
  if (面板容器.value?.contains(target) || 切换按钮容器.value?.contains(target)) {
    return
  }
  是否打开.value = false
}

let 原始BodyOverflow = ''
let 原始BodyOverscroll = ''

function 同步移动端滚动锁定() {
  if (!是否打开.value || !是否移动端.value) {
    document.body.style.overflow = 原始BodyOverflow
    document.body.style.overscrollBehavior = 原始BodyOverscroll
    return
  }
  原始BodyOverflow = document.body.style.overflow
  原始BodyOverscroll = document.body.style.overscrollBehavior
  document.body.style.overflow = 'hidden'
  document.body.style.overscrollBehavior = 'none'
}

onMounted(() => {
  更新移动端状态()
  更新视觉视口()
  window.addEventListener('resize', 更新移动端状态)
  window.addEventListener('resize', 更新视觉视口)
  window.visualViewport?.addEventListener('resize', 更新视觉视口)
  window.visualViewport?.addEventListener('scroll', 更新视觉视口)
  document.addEventListener('pointerdown', 处理外部点击)
})

watch([是否打开, 是否移动端], 同步移动端滚动锁定)

onBeforeUnmount(() => {
  停止生成()
  释放消息附件()
  释放附件地址(附件列表.value)
  window.removeEventListener('resize', 更新移动端状态)
  window.removeEventListener('resize', 更新视觉视口)
  window.visualViewport?.removeEventListener('resize', 更新视觉视口)
  window.visualViewport?.removeEventListener('scroll', 更新视觉视口)
  document.removeEventListener('pointerdown', 处理外部点击)
  document.body.style.overflow = 原始BodyOverflow
  document.body.style.overscrollBehavior = 原始BodyOverscroll
})
</script>

<template>
  <div data-aichatwidget-root class="ai-chat-widget-root">
    <Transition name="ai-chat-panel">
      <div v-if="是否打开" ref="面板容器" class="ai-chat-widget-root__panel-host">
        <WidgetPanel
          :title="title"
          :is-mobile-viewport="是否移动端"
          :mobile-height="移动端面板高度"
          :mobile-top="移动端面板顶部"
          :active-support="activeSupport"
          @close="关闭面板"
          @reset="清空对话"
        >
          <div class="ai-chat-widget-root__body">
            <MessageList
              :messages="消息列表"
              :is-generating="是否显示等待回复"
              :error-message="错误消息"
              :is-mobile-viewport="是否移动端"
            />
            <Composer
              ref="输入组件"
              v-model:input="输入内容"
              v-model:attachment-error="附件错误"
              :attachments="附件列表"
              :placeholder="placeholder"
              :disabled="disabled"
              :is-generating="是否请求中"
              :can-send="是否可发送"
              :is-mobile-viewport="是否移动端"
              @add-attachments="添加附件"
              @remove-attachment="移除附件"
              @submit="发送消息"
              @stop="停止生成"
              @input-keydown="处理键盘"
            />
          </div>
        </WidgetPanel>
      </div>
    </Transition>

    <div ref="切换按钮容器">
      <ChatToggleButton
        :is-open="是否打开"
        :is-mobile="是否移动端"
        @toggle="打开或关闭"
      />
    </div>
  </div>
</template>

<style>
[data-aichatwidget-root],
[data-aichatwidget-root] *,
[data-aichatwidget-root] *::before,
[data-aichatwidget-root] *::after {
  box-sizing: border-box;
}

[data-aichatwidget-root] {
  color: #1b1d22;
  font-family: 'Space Grotesk', 'Avenir Next', 'Segoe UI', sans-serif;
  font-size: 16px;
  line-height: 1.4;
  text-size-adjust: 100%;
  -webkit-font-smoothing: antialiased;
  -webkit-text-size-adjust: 100%;
  -moz-osx-font-smoothing: grayscale;
}

[data-aichatwidget-root] button,
[data-aichatwidget-root] input,
[data-aichatwidget-root] select,
[data-aichatwidget-root] textarea {
  font: inherit;
}

@keyframes helpfulChatDotPulse {
  0%,
  100% {
    opacity: 0.2;
    transform: translateY(0);
  }
  50% {
    opacity: 1;
    transform: translateY(-2px);
  }
}

@keyframes helpfulChatEmptyFadeIn {
  from {
    opacity: 0;
    transform: translateY(4px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>

<style scoped>
.ai-chat-widget-root__panel-host {
  display: contents;
}

.ai-chat-widget-root__body {
  position: relative;
  display: flex;
  min-height: 0;
  flex: 1;
  flex-direction: column;
}

.ai-chat-panel-enter-active,
.ai-chat-panel-leave-active {
  transition: opacity 160ms ease, transform 160ms ease;
}

.ai-chat-panel-enter-from,
.ai-chat-panel-leave-to {
  opacity: 0;
  transform: translateY(8px) scale(0.98);
}
</style>
