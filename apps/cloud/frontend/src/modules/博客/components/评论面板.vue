<script setup lang="ts">
import { ChatLineRound } from '@element-plus/icons-vue'
import { ElButton, ElEmpty, ElSkeleton } from 'element-plus'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import type { CommentVisibilityMode } from '../../系统/types'
import {
  读取Twikoo环境ID,
  读取Twikoo区域,
  TWIKOO_SCRIPT_URL,
  TWIKOO_STYLE_URL,
  type TwikooInitOptions,
  type TwikooInstance,
} from '../constants/twikooConfig'
import twikooCustomStyleText from '../styles/twikoo-firefly.css?raw'

interface TwikooVueInstance {
  showAdmin?: boolean
  showAdminEntry?: boolean
  onShowAdminEntry?: (visible: boolean) => void
}

declare global {
  interface Window {
    twikoo?: TwikooInstance
  }

  interface HTMLElement {
    __vue__?: TwikooVueInstance
  }
}

const props = withDefaults(defineProps<{
  path: string
  title?: string
  emptyDescription?: string
  hideAdminEntry?: boolean
  forceAdminEntry?: boolean
  visibility?: CommentVisibilityMode
  fillHeight?: boolean
  showPanelHeader?: boolean
  autoOpenAdmin?: boolean
}>(), {
  title: '评论区',
  emptyDescription: '尚未配置 Twikoo 服务地址',
  hideAdminEntry: false,
  forceAdminEntry: false,
  visibility: 'enabled',
  fillHeight: false,
  showPanelHeader: true,
  autoOpenAdmin: false,
})

const containerRef = ref<globalThis.HTMLElement | null>(null)
const loading = ref(true)
const errorMessage = ref('')
const renderToken = ref(0)

const envId = computed(() => 读取Twikoo环境ID())
const region = computed(() => 读取Twikoo区域())
const isConfigured = computed(() => envId.value.length > 0)
const isHidden = computed(() => props.visibility === 'hidden')
const isClosed = computed(() => props.visibility === 'closed')
const canRenderTwikoo = computed(() => props.visibility === 'enabled')
const normalizedPath = computed(() => {
  const path = props.path.trim()
  if (!path) return '/'
  if (path === '/') return path
  return path.endsWith('/') ? path.slice(0, -1) : path
})
let twikooScriptTask: Promise<TwikooInstance> | null = null
let adminEntryObserver: globalThis.MutationObserver | null = null
let shadowRootRef: globalThis.ShadowRoot | null = null
const mountTargetRef = ref<globalThis.HTMLElement | null>(null)

function syncHostModeClasses() {
  const host = containerRef.value
  if (!host) {
    return
  }
  host.classList.toggle('twikoo-host--fill-height', props.fillHeight)
  host.classList.toggle('twikoo-host--admin-mode', props.autoOpenAdmin)
}

function resetContainer() {
  stopAdminEntryObserver()
  mountTargetRef.value = null
  if (shadowRootRef) {
    shadowRootRef.replaceChildren()
    return
  }
  if (containerRef.value) {
    containerRef.value.innerHTML = ''
  }
}

function stopAdminEntryObserver() {
  adminEntryObserver?.disconnect()
  adminEntryObserver = null
}

function getRenderedRoot(): globalThis.HTMLElement | null {
  return shadowRootRef?.querySelector<globalThis.HTMLElement>('#twikoo') ?? mountTargetRef.value
}

function syncAdminEntryVisibility() {
  const element = getRenderedRoot()
  if (!element) {
    return
  }
  const actionIcons = element.querySelectorAll<globalThis.HTMLElement>('.tk-comments-actions > .tk-icon.__comments')
  if (actionIcons.length < 2) {
    return
  }
  const adminEntry = actionIcons[actionIcons.length - 1]
  adminEntry.style.display = props.hideAdminEntry ? 'none' : ''
}

function startAdminEntryObserver() {
  stopAdminEntryObserver()
  const element = getRenderedRoot()
  if (!element) {
    return
  }
  adminEntryObserver = new globalThis.MutationObserver(() => {
    syncAdminEntryVisibility()
  })
  adminEntryObserver.observe(element, {
    childList: true,
    subtree: true,
  })
  syncAdminEntryVisibility()
}

function resolveTwikooRoot(element: globalThis.HTMLElement): globalThis.HTMLElement {
  if (element.id === 'twikoo' || element.classList.contains('twikoo')) {
    return element
  }
  return element.querySelector<globalThis.HTMLElement>('#twikoo') ?? element
}

function syncRootAdminEntry(visible: boolean): boolean {
  const element = getRenderedRoot()
  if (!element) {
    return false
  }

  const twikooRoot = resolveTwikooRoot(element)
  const rootInstance = twikooRoot.__vue__
  if (!rootInstance) {
    return false
  }

  if (typeof rootInstance.onShowAdminEntry === 'function') {
    rootInstance.onShowAdminEntry(visible)
  }
  if (typeof rootInstance.showAdminEntry === 'boolean') {
    rootInstance.showAdminEntry = visible
  }

  return true
}

async function forceOpenAdminPanel(): Promise<boolean> {
  const element = getRenderedRoot()
  if (!element) {
    return false
  }

  const twikooRoot = resolveTwikooRoot(element)
  const rootInstance = twikooRoot.__vue__
  if (!rootInstance) {
    return false
  }

  syncRootAdminEntry(true)
  if (typeof rootInstance.showAdmin === 'boolean') {
    rootInstance.showAdmin = true
  }

  await new Promise<void>((resolve) => {
    window.setTimeout(resolve, 80)
  })

  const adminPanel = twikooRoot.querySelector<globalThis.HTMLElement>('.tk-admin')
  return Boolean(
    adminPanel
    && adminPanel.classList.contains('__show'),
  )
}

function tryForceAdminEntry(token: number, remaining = 20) {
  if (renderToken.value !== token || props.hideAdminEntry || !props.forceAdminEntry) {
    return
  }
  const synced = syncRootAdminEntry(true)
  if (synced || remaining <= 0 || renderToken.value !== token) {
    return
  }
  window.setTimeout(() => {
    tryForceAdminEntry(token, remaining - 1)
  }, 120)
}

function tryAutoOpenAdmin(token: number, remaining = 20) {
  if (!props.autoOpenAdmin || renderToken.value !== token) {
    return
  }
  void forceOpenAdminPanel().then((opened) => {
    if (opened || remaining <= 0 || renderToken.value !== token) {
      return
    }
    window.setTimeout(() => {
      tryAutoOpenAdmin(token, remaining - 1)
    }, 120)
  })
}

function ensureMountTarget(): globalThis.HTMLElement | null {
  const host = containerRef.value
  if (!host) {
    return null
  }
  syncHostModeClasses()
  const shadowRoot = host.shadowRoot ?? host.attachShadow({ mode: 'open' })
  shadowRootRef = shadowRoot
  shadowRoot.replaceChildren()

  const styleLink = document.createElement('link')
  styleLink.rel = 'stylesheet'
  styleLink.href = TWIKOO_STYLE_URL
  shadowRoot.appendChild(styleLink)

  const customStyle = document.createElement('style')
  customStyle.textContent = twikooCustomStyleText
  shadowRoot.appendChild(customStyle)

  const mountTarget = document.createElement('div')
  mountTarget.className = [
    'twikoo-shadow-host',
    props.fillHeight ? 'twikoo-shadow-host--fill-height' : '',
    props.autoOpenAdmin ? 'twikoo-shadow-host--admin-mode' : '',
  ].filter(Boolean).join(' ')
  shadowRoot.appendChild(mountTarget)
  mountTargetRef.value = mountTarget
  return mountTarget
}

function buildInitOptions(el: globalThis.HTMLElement): TwikooInitOptions {
  return {
    envId: envId.value,
    el,
    path: normalizedPath.value,
    lang: 'zh-CN',
    region: region.value,
  }
}

function ensureTwikooLoaded(): Promise<TwikooInstance> {
  if (window.twikoo) {
    return Promise.resolve(window.twikoo)
  }

  if (twikooScriptTask) {
    return twikooScriptTask
  }

  twikooScriptTask = new Promise<TwikooInstance>((resolve, reject) => {
    const existingScript = document.querySelector<globalThis.HTMLScriptElement>('script[data-twikoo-script="true"]')
    if (existingScript) {
      existingScript.addEventListener('load', () => {
        if (window.twikoo) {
          resolve(window.twikoo)
          return
        }
        reject(new Error('Twikoo 脚本已加载，但未找到全局对象'))
      }, { once: true })
      existingScript.addEventListener('error', () => {
        reject(new Error('Twikoo 脚本加载失败'))
      }, { once: true })
      return
    }

    const script = document.createElement('script')
    script.src = TWIKOO_SCRIPT_URL
    script.async = true
    script.defer = true
    script.dataset.twikooScript = 'true'
    script.onload = () => {
      if (window.twikoo) {
        resolve(window.twikoo)
        return
      }
      reject(new Error('Twikoo 脚本已加载，但未找到全局对象'))
    }
    script.onerror = () => {
      reject(new Error('Twikoo 脚本加载失败'))
    }
    document.head.appendChild(script)
  }).catch((error) => {
    twikooScriptTask = null
    throw error
  })

  return twikooScriptTask
}

async function mountTwikoo() {
  const token = renderToken.value + 1
  renderToken.value = token
  errorMessage.value = ''
  loading.value = true

  if (!canRenderTwikoo.value || !isConfigured.value) {
    resetContainer()
    loading.value = false
    return
  }

  await nextTick()
  resetContainer()
  const element = ensureMountTarget()
  if (!element) {
    loading.value = false
    return
  }

  try {
    const twikoo = await ensureTwikooLoaded()
    if (renderToken.value !== token) {
      return
    }
    await twikoo.init(buildInitOptions(element))
    if (renderToken.value !== token) {
      return
    }
    syncHostModeClasses()
    tryForceAdminEntry(token)
    startAdminEntryObserver()
    tryAutoOpenAdmin(token)
  } catch (error) {
    if (renderToken.value !== token) {
      return
    }
    errorMessage.value = error instanceof Error ? error.message : 'Twikoo 初始化失败'
    resetContainer()
    stopAdminEntryObserver()
  } finally {
    if (renderToken.value === token) {
      loading.value = false
    }
  }
}

function retryMount() {
  void mountTwikoo()
}

onMounted(() => {
  syncHostModeClasses()
  void mountTwikoo()
})

watch(
  () => [props.path, envId.value, region.value, props.visibility],
  () => {
    void mountTwikoo()
  },
)

watch(
  () => [props.hideAdminEntry, props.forceAdminEntry],
  () => {
    syncAdminEntryVisibility()
    if (!props.hideAdminEntry && props.forceAdminEntry) {
      tryForceAdminEntry(renderToken.value)
    }
  },
)

watch(
  () => [props.fillHeight, props.autoOpenAdmin],
  () => {
    syncHostModeClasses()
    if (props.autoOpenAdmin) {
      tryAutoOpenAdmin(renderToken.value)
    }
  },
)

onBeforeUnmount(() => {
  renderToken.value += 1
  stopAdminEntryObserver()
  resetContainer()
})
</script>

<template>
  <section v-if="!isHidden" class="twikoo-card" :class="{ 'twikoo-card--fill-height': props.fillHeight }">
    <div class="twikoo-card-decoration" aria-hidden="true">
      <div class="twikoo-card-decoration-ring twikoo-card-decoration-ring--outer" />
      <div class="twikoo-card-decoration-ring twikoo-card-decoration-ring--inner" />
      <div class="twikoo-card-decoration-dot" />
    </div>

    <header v-if="props.showPanelHeader" class="twikoo-card-header">
      <div class="twikoo-card-title-row">
        <div class="twikoo-card-title-bar" />
        <div>
          <div class="twikoo-card-title">{{ props.title }}</div>
          <p class="twikoo-card-subtitle">分享你的想法，与大家交流讨论</p>
        </div>
      </div>
    </header>

    <div class="twikoo-card-body">
      <div v-if="isClosed" class="twikoo-state">
        <div class="twikoo-state-icon">
          <ChatLineRound />
        </div>
        <div class="twikoo-state-title">评论区已关闭</div>
        <p class="twikoo-state-text">站点当前暂不开放评论功能，稍后再来看看，或者通过其他页面联系我。</p>
      </div>

      <div v-else-if="!isConfigured" class="twikoo-empty-wrap">
        <ElEmpty :description="props.emptyDescription">
          <template #default>
            <p class="twikoo-empty-tip">请在 `apps/cloud/frontend/.env` 中配置 `VITE_TWIKOO_ENV_ID` 后刷新页面。</p>
          </template>
        </ElEmpty>
      </div>

      <div v-else-if="errorMessage" class="twikoo-empty-wrap">
        <ElEmpty description="Twikoo 加载失败">
          <template #default>
            <p class="twikoo-empty-tip">{{ errorMessage }}</p>
            <ElButton type="primary" plain @click="retryMount">重试</ElButton>
          </template>
        </ElEmpty>
      </div>

      <div v-else class="twikoo-shell" :class="{ 'twikoo-shell--loading': loading }">
        <div v-if="loading" class="twikoo-skeleton">
          <ElSkeleton animated :rows="6" />
        </div>
        <div ref="containerRef" class="twikoo-mount" />
      </div>
    </div>
  </section>
</template>

<style scoped>
.twikoo-card {
  position: relative;
  overflow: hidden;
  padding: 1.5rem 1.5rem 1.25rem;
  border-radius: var(--radius-large);
  background: var(--card-bg-transparent);
  border: 1px solid rgba(255, 255, 255, 0.45);
  backdrop-filter: blur(18px);
  box-shadow: 0 14px 34px rgba(148, 163, 184, 0.14);
  background-color: rgba(255, 255, 255, var(--overlay-card-opacity)) !important;
  transition: transform var(--transition-base), box-shadow var(--transition-base), background-color var(--transition-base), border-color var(--transition-base);
}

.twikoo-card--fill-height {
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.twikoo-card:hover {
  box-shadow: 0 20px 38px rgba(148, 163, 184, 0.18);
}

.dark .twikoo-card {
  border-color: rgba(148, 163, 184, 0.16);
  box-shadow: 0 14px 32px rgba(2, 6, 23, 0.3);
  background-color: rgba(15, 23, 42, var(--overlay-card-opacity)) !important;
}

.dark .twikoo-card:hover {
  box-shadow: 0 20px 40px rgba(2, 6, 23, 0.36);
}

.twikoo-card-decoration {
  position: absolute;
  top: -1rem;
  right: -1rem;
  width: 7rem;
  height: 7rem;
  opacity: 0.1;
  pointer-events: none;
}

.twikoo-card-decoration-ring {
  position: absolute;
  inset: 0;
  border-radius: 999px;
  border: 2px solid color-mix(in srgb, var(--el-color-primary) 70%, transparent);
}

.twikoo-card-decoration-ring--inner {
  inset: 1.2rem;
}

.twikoo-card-decoration-dot {
  position: absolute;
  inset: 2.5rem;
  border-radius: 999px;
  background: color-mix(in srgb, var(--el-color-primary) 82%, white);
}

.twikoo-card-header {
  position: relative;
  z-index: 1;
  margin-bottom: 1.25rem;
}

.twikoo-card-title-row {
  display: flex;
  align-items: flex-start;
  gap: 0.875rem;
}

.twikoo-card-title-bar {
  width: 0.25rem;
  min-height: 1.75rem;
  border-radius: 999px;
  background: linear-gradient(180deg, var(--el-color-primary), transparent);
  flex: 0 0 auto;
}

.twikoo-card-title {
  font-weight: 700;
  font-size: 1.125rem;
  color: var(--text-primary);
}

.twikoo-card-subtitle {
  margin: 0.35rem 0 0;
  color: var(--text-secondary);
  font-size: 0.875rem;
  line-height: 1.6;
}

.twikoo-card-body {
  position: relative;
  z-index: 1;
  padding-inline: 0.125rem;
}

.twikoo-card--fill-height .twikoo-card-body {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.twikoo-empty-wrap {
  padding: 0.5rem 0;
}

.twikoo-empty-tip {
  margin: 0 0 0.75rem;
  color: var(--text-secondary);
  font-size: 0.875rem;
  line-height: 1.6;
}

.twikoo-shell {
  position: relative;
  min-height: 12rem;
}

.twikoo-card--fill-height .twikoo-shell {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.twikoo-state {
  display: flex;
  min-height: 12rem;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  text-align: center;
  gap: 0.75rem;
  padding: 1.5rem 1rem;
  border-radius: 1rem;
  border: 1px solid rgba(148, 163, 184, 0.18);
  background: color-mix(in srgb, var(--card-bg, rgba(255, 255, 255, 0.82)) 84%, transparent);
}

.dark .twikoo-state {
  border-color: rgba(148, 163, 184, 0.2);
  background: color-mix(in srgb, var(--card-bg, rgba(15, 23, 42, 0.78)) 88%, transparent);
}

.twikoo-state-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 3.5rem;
  height: 3.5rem;
  border-radius: 999px;
  background: color-mix(in srgb, var(--el-color-primary) 14%, white);
  color: var(--el-color-primary);
  box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--el-color-primary) 18%, transparent);
}

.twikoo-state-icon :deep(svg) {
  width: 1.4rem;
  height: 1.4rem;
}

.twikoo-state-title {
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--text-primary);
}

.twikoo-state-text {
  margin: 0;
  max-width: 34rem;
  color: var(--text-secondary);
  line-height: 1.8;
}

.twikoo-shell--loading .twikoo-mount {
  opacity: 0;
}

.twikoo-skeleton {
  position: absolute;
  inset: 0;
  z-index: 1;
}

.twikoo-mount {
  min-height: 12rem;
}

.twikoo-card--fill-height .twikoo-mount {
  flex: 1;
  min-height: 0;
  height: 100%;
}

@media (max-width: 576px) {
  .twikoo-card {
    padding: 1.25rem 1rem 1rem;
  }

  .twikoo-card-title {
    font-size: 1rem;
  }

  .twikoo-state {
    min-height: 10rem;
    padding-inline: 0.75rem;
  }
}
</style>
