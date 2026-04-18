<script setup lang="ts">
import { ElButton, ElEmpty, ElSkeleton } from 'element-plus'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import {
  readTwikooEnvId,
  readTwikooRegion,
  TWIKOO_SCRIPT_URL,
  TWIKOO_STYLE_URL,
  type TwikooInitOptions,
  type TwikooInstance,
} from '../constants/twikooConfig'

declare global {
  interface Window {
    twikoo?: TwikooInstance
  }
}

const props = withDefaults(defineProps<{
  path: string
  title?: string
  emptyDescription?: string
  hideAdminEntry?: boolean
}>(), {
  title: '评论',
  emptyDescription: '尚未配置 Twikoo 服务地址',
  hideAdminEntry: false,
})

const containerRef = ref<globalThis.HTMLElement | null>(null)
const loading = ref(true)
const errorMessage = ref('')
const renderToken = ref(0)

const envId = computed(() => readTwikooEnvId())
const region = computed(() => readTwikooRegion())
const isConfigured = computed(() => envId.value.length > 0)
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

function syncAdminEntryVisibility() {
  const element = mountTargetRef.value
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
  const element = mountTargetRef.value
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

function ensureMountTarget(): globalThis.HTMLElement | null {
  const host = containerRef.value
  if (!host) {
    return null
  }
  const shadowRoot = host.shadowRoot ?? host.attachShadow({ mode: 'open' })
  shadowRootRef = shadowRoot
  shadowRoot.replaceChildren()

  const styleLink = document.createElement('link')
  styleLink.rel = 'stylesheet'
  styleLink.href = TWIKOO_STYLE_URL
  shadowRoot.appendChild(styleLink)

  const mountTarget = document.createElement('div')
  mountTarget.className = 'twikoo-shadow-host'
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

  if (!isConfigured.value) {
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
    startAdminEntryObserver()
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
  void mountTwikoo()
})

watch(
  () => [props.path, envId.value, region.value],
  () => {
    void mountTwikoo()
  },
)

watch(
  () => props.hideAdminEntry,
  () => {
    syncAdminEntryVisibility()
  },
)

onBeforeUnmount(() => {
  renderToken.value += 1
  stopAdminEntryObserver()
  resetContainer()
})
</script>

<template>
  <section class="twikoo-card">
    <header class="twikoo-card-header">
      <div class="twikoo-card-title">{{ props.title }}</div>
      <p class="twikoo-card-subtitle">当前评论与页面路径绑定，留言页和文章页互不干扰。</p>
    </header>

    <div v-if="!isConfigured" class="twikoo-empty-wrap">
      <ElEmpty :description="props.emptyDescription">
        <template #default>
          <p class="twikoo-empty-tip">请在 `frontend/.env` 中配置 `VITE_TWIKOO_ENV_ID` 后刷新页面。</p>
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
  </section>
</template>

<style scoped>
.twikoo-card {
  padding: 1rem 1.25rem 1.25rem;
  border-radius: var(--radius-large);
  background: var(--card-bg-transparent);
  border: 1px solid rgba(255, 255, 255, 0.45);
  backdrop-filter: blur(18px);
  background-color: rgba(255, 255, 255, var(--overlay-card-opacity)) !important;
  transition: transform var(--transition-base), box-shadow var(--transition-base), background-color var(--transition-base), border-color var(--transition-base);
}

.dark .twikoo-card {
  border-color: rgba(148, 163, 184, 0.16);
  background-color: rgba(15, 23, 42, var(--overlay-card-opacity)) !important;
}

.twikoo-card-header {
  margin-bottom: 1rem;
}

.twikoo-card-title {
  font-weight: 700;
  font-size: 1rem;
  color: var(--text-primary);
  position: relative;
  padding-left: 0.75rem;
}

.twikoo-card-title::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0.125rem;
  width: 0.25rem;
  height: 1rem;
  border-radius: 0.25rem;
  background-color: var(--el-color-primary);
}

.twikoo-card-subtitle {
  margin: 0.4rem 0 0;
  color: var(--text-secondary);
  font-size: 0.875rem;
  line-height: 1.6;
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

.twikoo-shell :deep(.tk-comments-container) {
  overflow: visible;
}

.twikoo-shell :deep(.twikoo) {
  color: var(--text-primary);
}

.twikoo-shell :deep(.tk-comments-title),
.twikoo-shell :deep(.tk-submit-action-icon),
.twikoo-shell :deep(.tk-action-link),
.twikoo-shell :deep(.tk-nick-link),
.twikoo-shell :deep(.tk-expand) {
  color: var(--el-color-primary);
}

.twikoo-shell :deep(.tk-content),
.twikoo-shell :deep(.tk-extras),
.twikoo-shell :deep(.tk-meta),
.twikoo-shell :deep(.tk-footer),
.twikoo-shell :deep(.tk-extra-text) {
  color: var(--text-secondary);
}

.twikoo-shell :deep(.el-input__inner),
.twikoo-shell :deep(.el-textarea__inner),
.twikoo-shell :deep(.tk-preview-container),
.twikoo-shell :deep(.tk-comment),
.twikoo-shell :deep(.tk-row .tk-avatar),
.twikoo-shell :deep(.tk-comments-container),
.twikoo-shell :deep(.OwO .OwO-body),
.twikoo-shell :deep(.tk-content),
.twikoo-shell :deep(.tk-submit .tk-row) {
  border-radius: 12px;
}

.twikoo-shell :deep(.el-input__inner),
.twikoo-shell :deep(.el-textarea__inner),
.twikoo-shell :deep(.tk-preview-container),
.twikoo-shell :deep(.OwO .OwO-body),
.twikoo-shell :deep(.tk-preview-container),
.twikoo-shell :deep(.tk-comment),
.twikoo-shell :deep(.tk-comments-container) {
  background: rgba(255, 255, 255, 0.72);
  border-color: rgba(15, 23, 42, 0.08);
}

.dark .twikoo-shell :deep(.el-input__inner),
.dark .twikoo-shell :deep(.el-textarea__inner),
.dark .twikoo-shell :deep(.tk-preview-container),
.dark .twikoo-shell :deep(.OwO .OwO-body),
.dark .twikoo-shell :deep(.tk-comment),
.dark .twikoo-shell :deep(.tk-comments-container) {
  background: rgba(15, 23, 42, 0.75);
  border-color: rgba(148, 163, 184, 0.18);
  color: var(--text-primary);
}

.twikoo-shell :deep(.el-button--primary),
.twikoo-shell :deep(.tk-tag-green),
.twikoo-shell :deep(.tk-pagination-pager.__current) {
  background: var(--el-color-primary);
  border-color: var(--el-color-primary);
}

.twikoo-shell :deep(.el-button:not(.el-button--primary):not(.el-button--text)) {
  border-radius: 999px;
}

.twikoo-shell :deep(.el-button--primary) {
  border-radius: 999px;
}
</style>
