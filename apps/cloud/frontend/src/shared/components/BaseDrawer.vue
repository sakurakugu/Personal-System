<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { 使用视口 } from '../composables/使用视口'

const props = withDefaults(defineProps<{
  modelValue: boolean
  title?: string
  ariaLabel?: string
  anchorSelector?: string
  themeSourceSelector?: string
  topGapDesktop?: number
  topGapMobile?: number
  fallbackTopDesktop?: number
  fallbackTopMobile?: number
  widthDesktop?: string
  widthMobile?: string
}>(), {
  title: '详情',
  ariaLabel: '详情抽屉',
  anchorSelector: '',
  themeSourceSelector: '',
  topGapDesktop: 16,
  topGapMobile: 12,
  fallbackTopDesktop: 64,
  fallbackTopMobile: 58,
  widthDesktop: 'min(560px, calc(100vw - 16px))',
  widthMobile: 'min(560px, calc(100vw - 12px))',
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'after-leave': []
}>()

const { width } = 使用视口()
const 顶部偏移 = ref(72)
const 主题样式变量 = ref<Record<string, string>>({})
const 主题模式 = ref<'overlay' | 'plain' | 'banner'>('banner')
let 主题观察器: globalThis.MutationObserver | null = null
const 抽屉宽度 = computed(() => width.value <= 768 ? props.widthMobile : props.widthDesktop)
const 抽屉层样式 = computed(() => ({
  ...主题样式变量.value,
  '--base-drawer-top-offset': `${顶部偏移.value}px`,
}))
const 抽屉层类名 = computed(() => ({
  'base-drawer-layer--overlay': 主题模式.value === 'overlay',
  'base-drawer-layer--plain': 主题模式.value === 'plain',
  'base-drawer-layer--banner': 主题模式.value === 'banner',
}))
const 抽屉类名 = computed(() => ({
  'base-drawer--overlay': 主题模式.value === 'overlay',
  'base-drawer--plain': 主题模式.value === 'plain',
  'base-drawer--banner': 主题模式.value === 'banner',
}))

const 需要同步的主题变量 = [
  '--card-bg',
  '--card-bg-transparent',
  '--radius-large',
  '--transition-base',
  '--text-primary',
  '--text-secondary',
  '--theme-overlay',
] as const

function 关闭抽屉() {
  emit('update:modelValue', false)
}

function 获取主题源元素() {
  if (props.themeSourceSelector) {
    return document.querySelector<globalThis.HTMLElement>(props.themeSourceSelector)
  }
  return document.documentElement
}

function 同步主题样式变量() {
  const 主题源元素 = 获取主题源元素()
  if (!主题源元素) {
    主题样式变量.value = {}
    主题模式.value = 'banner'
    return
  }
  const 计算样式 = window.getComputedStyle(主题源元素)
  const 下一个变量: Record<string, string> = {}
  for (const 变量名 of 需要同步的主题变量) {
    const 值 = 计算样式.getPropertyValue(变量名).trim()
    if (值) {
      下一个变量[变量名] = 值
    }
  }
  主题样式变量.value = 下一个变量
  if (主题源元素.classList.contains('is-overlay-mode')) {
    主题模式.value = 'overlay'
    return
  }
  if (主题源元素.classList.contains('is-plain-mode')) {
    主题模式.value = 'plain'
    return
  }
  主题模式.value = 'banner'
}

function 更新抽屉顶部偏移() {
  const 锚点元素 = props.anchorSelector ? document.querySelector<globalThis.HTMLElement>(props.anchorSelector) : null
  const 默认顶部 = width.value <= 768 ? props.fallbackTopMobile : props.fallbackTopDesktop
  const 顶部安全间距 = width.value <= 768 ? props.topGapMobile : props.topGapDesktop
  const 锚点底部位置 = 锚点元素?.getBoundingClientRect().bottom ?? 默认顶部
  顶部偏移.value = Math.ceil(锚点底部位置 + 顶部安全间距)
}

function 开始监听主题变化() {
  停止监听主题变化()
  主题观察器 = new globalThis.MutationObserver(() => {
    同步主题样式变量()
  })
  主题观察器.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['class', 'style'],
  })
  const 主题源元素 = 获取主题源元素()
  if (主题源元素 && 主题源元素 !== document.documentElement) {
    主题观察器.observe(主题源元素, {
      attributes: true,
      attributeFilter: ['class', 'style'],
    })
  }
}

function 停止监听主题变化() {
  主题观察器?.disconnect()
  主题观察器 = null
}

function 处理抽屉键盘事件(event: globalThis.KeyboardEvent) {
  if (event.key === 'Escape' && props.modelValue) {
    关闭抽屉()
  }
}

watch(width, () => {
  更新抽屉顶部偏移()
})

watch(() => props.anchorSelector, () => {
  更新抽屉顶部偏移()
})

watch(() => props.themeSourceSelector, () => {
  同步主题样式变量()
  开始监听主题变化()
})

watch(() => props.modelValue, (value) => {
  if (value) {
    同步主题样式变量()
  }
})

onMounted(() => {
  更新抽屉顶部偏移()
  同步主题样式变量()
  开始监听主题变化()
  window.addEventListener('keydown', 处理抽屉键盘事件)
  window.addEventListener('resize', 更新抽屉顶部偏移)
  window.addEventListener('scroll', 更新抽屉顶部偏移, { passive: true })
})

onBeforeUnmount(() => {
  停止监听主题变化()
  window.removeEventListener('keydown', 处理抽屉键盘事件)
  window.removeEventListener('resize', 更新抽屉顶部偏移)
  window.removeEventListener('scroll', 更新抽屉顶部偏移)
})
</script>

<template>
  <Teleport to="body">
    <Transition name="base-drawer-layer" @after-leave="emit('after-leave')">
      <div
        v-show="modelValue"
        class="base-drawer-layer"
        :class="抽屉层类名"
        :style="抽屉层样式"
        @click="关闭抽屉"
      >
        <aside
          class="base-drawer"
          :class="抽屉类名"
          :style="{ width: 抽屉宽度 }"
          role="dialog"
          aria-modal="true"
          :aria-label="ariaLabel"
          @click.stop
        >
          <div class="base-drawer__header">
            <slot name="header">
              <h2 class="base-drawer__title">{{ title }}</h2>
              <button
                type="button"
                class="base-drawer__close"
                aria-label="关闭抽屉"
                @click="关闭抽屉"
              >
                ×
              </button>
            </slot>
          </div>

          <div class="base-drawer__body">
            <slot />
          </div>
        </aside>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.base-drawer-layer {
  position: fixed;
  inset: 0;
  z-index: 90;
  display: flex;
  justify-content: flex-end;
  padding-top: var(--base-drawer-top-offset);
  padding-bottom: 16px;
  background: var(--theme-overlay, rgba(17, 24, 39, 0.4));
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  transition: background-color var(--transition-base, 0.2s) ease;
}

.base-drawer-layer--plain {
  backdrop-filter: none;
  -webkit-backdrop-filter: none;
}

.base-drawer {
  display: flex;
  flex-direction: column;
  height: 100%;
  margin: 0;
  border-left: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: var(--radius-large, 1rem) 0 0 var(--radius-large, 1rem);
  background: var(--card-bg, #ffffff);
  overflow: hidden;
  transition:
    background-color var(--transition-base, 0.2s) ease,
    border-color var(--transition-base, 0.2s) ease,
    box-shadow var(--transition-base, 0.2s) ease,
    backdrop-filter var(--transition-base, 0.2s) ease;
}

:global(.dark) .base-drawer-layer {
  background: var(--theme-overlay, rgba(2, 6, 23, 0.68));
}

:global(.dark) .base-drawer {
  border-left-color: rgba(255, 255, 255, 0.08);
}

.base-drawer--banner,
.base-drawer--plain {
  box-shadow: none;
}

.base-drawer--overlay {
  border-left-color: rgba(255, 255, 255, 0.45);
  background: var(--card-bg-transparent, rgba(255, 255, 255, 0.68));
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  box-shadow: 0 14px 34px rgba(148, 163, 184, 0.14);
}

:global(.dark) .base-drawer--overlay {
  border-left-color: rgba(148, 163, 184, 0.16);
  box-shadow: 0 14px 32px rgba(2, 6, 23, 0.3);
}

.base-drawer__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 20px 20px 16px;
}

.base-drawer__title {
  margin: 0;
  color: var(--text-primary);
  font-size: 20px;
  font-weight: 700;
  line-height: 1.4;
}

.base-drawer__close {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  padding: 0;
  border: none;
  border-radius: 999px;
  background: transparent;
  color: var(--text-secondary);
  font-size: 22px;
  line-height: 1;
  cursor: pointer;
  transition: background-color 0.2s ease, color 0.2s ease;
}

.base-drawer__close:hover {
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
}

.base-drawer__body {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.base-drawer-layer-enter-active,
.base-drawer-layer-leave-active {
  transition: opacity 0.28s ease;
}

.base-drawer-layer-enter-from,
.base-drawer-layer-leave-to {
  opacity: 0;
}

.base-drawer-layer-enter-active .base-drawer,
.base-drawer-layer-leave-active .base-drawer {
  transition: transform 0.32s cubic-bezier(0.22, 1, 0.36, 1), opacity 0.28s ease;
}

.base-drawer-layer-enter-from .base-drawer,
.base-drawer-layer-leave-to .base-drawer {
  opacity: 0;
  transform: translateX(48px);
}

@media (max-width: 768px) {
  .base-drawer-layer {
    padding-bottom: 12px;
  }

  .base-drawer__header {
    padding: 18px 16px 14px;
  }

  .base-drawer__body {
    padding: 16px;
  }
}
</style>
