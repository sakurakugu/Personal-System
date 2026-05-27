<script setup lang="ts">
import {
  获取文娱状态标签,
  MediaRating,
  获取评分展示,
  type MediaRecord,
} from '@personal-system/module-media';
import { ElSpace, ElTag } from 'element-plus';
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { 使用视口 } from '../../../shared/composables/使用视口';

const props = defineProps<{
  modelValue: boolean
  条目: MediaRecord | null
  分类标签映射: Record<string, string>
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'after-leave': []
}>()

const 文娱抽屉默认顶部间距 = {
  桌面端安全间距: 16,
  移动端安全间距: 12,
  桌面端默认顶部: 64,
  移动端默认顶部: 58,
}

const { width } = 使用视口()
const 顶部偏移 = ref(72)
const 主题样式变量 = ref<Record<string, string>>({})
const 主题模式 = ref<'overlay' | 'none' | 'banner'>('banner')
let 主题观察器: globalThis.MutationObserver | null = null

const 抽屉标题 = '作品详情'
const 条目标题 = computed(() => props.条目?.title || '')
const 是否存在原名 = computed(() => Boolean(props.条目?.original_title))
const 原名悬停显示 = ref(false)
const 原名手动锁定显示 = ref(false)
const 是否显示原名 = computed(() => 是否存在原名.value && (原名悬停显示.value || 原名手动锁定显示.value))
const 评分说明文本 = computed(() => {
  const rating = props.条目?.rating
  if (!rating) {
    return '未评分'
  }
  const 展示 = 获取评分展示(rating)
  if (rating === 1) {
    return '有毒点/雷区'
  }
  if (rating === 2) {
    return '粪作'
  }
  if (rating === 3) {
    return `一般·${展示.starValue}星`
  }
  if (rating <= 5) {
    return `中等·${展示.starValue}星`
  }
  if (rating <= 7) {
    return `推荐·${展示.starValue}星`
  }
  if (rating <= 9) {
    return `佳作·${展示.starValue}星`
  }
  if (rating <= 11) {
    return `强推·${展示.starValue}星`
  }
  if (rating <= 13) {
    return `必看·${展示.starValue}星`
  }
  return `神作·${展示.starValue}星`
})
const 抽屉无障碍标题 = computed(() => 条目标题.value ? `${抽屉标题}：${条目标题.value}` : 抽屉标题)
const 抽屉宽度 = computed(() => width.value <= 768
  ? 'min(560px, calc(100vw - 12px))'
  : 'min(560px, calc(100vw - 16px))')
const 抽屉层样式 = computed(() => ({
  ...主题样式变量.value,
  '--base-drawer-top-offset': `${顶部偏移.value}px`,
}))
const 抽屉层类名 = computed(() => ({
  'base-drawer-layer--overlay': 主题模式.value === 'overlay',
  'base-drawer-layer--none': 主题模式.value === 'none',
  'base-drawer-layer--banner': 主题模式.value === 'banner',
}))
const 抽屉类名 = computed(() => ({
  'base-drawer--overlay': 主题模式.value === 'overlay',
  'base-drawer--none': 主题模式.value === 'none',
  'base-drawer--banner': 主题模式.value === 'banner',
}))

const 需要同步的主题变量 = [
  '--card-bg',
  '--card-bg-transparent',
  '--radius-large',
  '--transition-base',
  '--text-primary',
  '--text-secondary',
  '--line-divider',
  '--theme-overlay',
  '--primary',
] as const

function 关闭抽屉() {
  重置原名显示状态()
  emit('update:modelValue', false)
}

function 重置原名显示状态() {
  原名悬停显示.value = false
  原名手动锁定显示.value = false
}

function 处理标题鼠标进入() {
  if (!是否存在原名.value) {
    return
  }
  原名悬停显示.value = true
}

function 处理标题鼠标离开() {
  if (原名手动锁定显示.value) {
    return
  }
  原名悬停显示.value = false
}

function 切换原名固定显示() {
  if (!是否存在原名.value) {
    return
  }
  原名手动锁定显示.value = !原名手动锁定显示.value
  原名悬停显示.value = 原名手动锁定显示.value
}

function 获取主题源元素() {
  return document.querySelector<globalThis.HTMLElement>('.blog-home') || document.documentElement
}

function 同步主题样式变量() {
  const 主题源元素 = 获取主题源元素()
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
    主题模式.value = 'none'
    return
  }
  主题模式.value = 'banner'
}

function 更新抽屉顶部偏移() {
  const 锚点元素 = document.querySelector<globalThis.HTMLElement>('#top-row')
  const 默认顶部 = width.value <= 768
    ? 文娱抽屉默认顶部间距.移动端默认顶部
    : 文娱抽屉默认顶部间距.桌面端默认顶部
  const 顶部安全间距 = width.value <= 768
    ? 文娱抽屉默认顶部间距.移动端安全间距
    : 文娱抽屉默认顶部间距.桌面端安全间距
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
  if (主题源元素 !== document.documentElement) {
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

watch(() => props.modelValue, (value) => {
  if (value) {
    更新抽屉顶部偏移()
    同步主题样式变量()
    return
  }
  重置原名显示状态()
})

watch(() => props.条目?.id, () => {
  重置原名显示状态()
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
          :aria-label="抽屉无障碍标题"
          @click.stop
        >
          <div class="base-drawer__header">
            <div class="media-detail-drawer__heading">
              <h2 class="media-detail-drawer__title">{{ 抽屉标题 }}</h2>
            </div>
            <button
              type="button"
              class="media-detail-drawer__close"
              aria-label="关闭详情"
              @click="关闭抽屉"
            >
              ×
            </button>
          </div>

          <div class="base-drawer__body">
            <div v-if="条目" class="media-detail">
              <section class="media-detail__hero">
                <div class="media-detail__cover-block">
                  <img
                    v-if="条目.primary_cover_asset?.url || 条目.primary_cover_asset?.thumbnail_url"
                    :src="条目.primary_cover_asset?.url || 条目.primary_cover_asset?.thumbnail_url || ''"
                    :alt="条目.title"
                    class="media-detail__cover"
                  >
                  <div v-else class="media-detail__cover media-detail__cover--empty">📖</div>
                </div>

                <div class="media-detail__content">
                  <div v-if="条目标题" class="media-detail__content-heading">
                    <h3 class="media-detail__content-title">
                      <button
                        type="button"
                        class="media-detail__title-trigger"
                        :class="{ 'is-original-visible': 是否显示原名 }"
                        :aria-expanded="是否显示原名"
                        :aria-pressed="原名手动锁定显示"
                        @mouseenter="处理标题鼠标进入"
                        @mouseleave="处理标题鼠标离开"
                        @focus="处理标题鼠标进入"
                        @blur="处理标题鼠标离开"
                        @click="切换原名固定显示"
                      >
                        {{ 条目标题 }}
                      </button>
                    </h3>

                    <div v-if="是否显示原名" class="media-detail__text media-detail__text--muted">
                      {{ 条目.original_title }}
                    </div>
                  </div>

                  <ElSpace wrap class="media-detail__taxonomy">
                    <ElTag>{{ 分类标签映射[条目.media_type] || 条目.media_type }}</ElTag>
                    <ElTag
                      v-for="子分类 in 条目.genres"
                      :key="`genre-${子分类}`"
                      effect="plain"
                    >
                      {{ 子分类 }}
                    </ElTag>
                    <ElTag
                      v-for="标签 in 条目.tags"
                      :key="`tag-${标签}`"
                      type="warning"
                      effect="plain"
                    >
                      {{ 标签 }}
                    </ElTag>
                    <ElTag
                      v-for="标签 in 条目.personal_tags || []"
                      :key="`personal-tag-${标签}`"
                      type="success"
                    >
                      {{ 标签 }}
                    </ElTag>
                  </ElSpace>

                  <div v-if="条目.creator" class="media-detail__meta-item">
                    <h3>创作者</h3>
                    <p>{{ 条目.creator }}</p>
                  </div>

                  <div v-if="条目.rating != null || 条目.status" class="media-detail__meta-item">
                    <h3>评分</h3>
                    <div class="media-detail__rating">
                      <div class="media-detail__rating-main">
                        <MediaRating :rating="条目.rating" />
                        <span v-if="评分说明文本" class="media-detail__rating-text">
                          {{ 评分说明文本 }}
                        </span>
                      </div>
                      <ElTag v-if="条目.status" type="info" class="media-detail__rating-status">
                        {{ 获取文娱状态标签(条目.media_type, 条目.status) }}
                      </ElTag>
                    </div>
                  </div>
                </div>
              </section>

              <section v-if="条目.summary || 条目.description" class="media-detail__details">
                <div v-if="条目.summary" class="media-detail__section">
                  <h3>简介</h3>
                  <p>{{ 条目.summary }}</p>
                </div>
                <div v-if="条目.description" class="media-detail__section">
                  <h3>推荐语</h3>
                  <p>{{ 条目.description }}</p>
                </div>
              </section>
            </div>
          </div>
        </aside>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.base-drawer-layer {
  --base-drawer-bottom-gap: 16px;
  position: fixed;
  inset: 0;
  z-index: 90;
  display: flex;
  justify-content: flex-end;
  padding-top: var(--base-drawer-top-offset);
  padding-bottom: var(--base-drawer-bottom-gap);
  background: var(--theme-overlay, rgba(17, 24, 39, 0.4));
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  transition: background-color var(--transition-base, 0.2s) ease;
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
.base-drawer--none {
  box-shadow: none;
}

.base-drawer--overlay {
  border-left-color: var(--line-divider, rgba(0, 0, 0, 0.08));
  background: var(--card-bg-transparent, rgba(255, 255, 255, 0.68));
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
}

:global(.dark) .base-drawer--overlay {
  border-left-color: var(--line-divider, rgba(255, 255, 255, 0.08));
}

.base-drawer__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 18px 20px 10px;
}

.base-drawer__body {
  flex: 1;
  overflow-y: auto;
  padding: 12px 20px 20px;
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

.media-detail {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.media-detail__hero {
  display: grid;
  grid-template-columns: minmax(180px, 220px) minmax(0, 1fr);
  gap: 20px;
  align-items: start;
}

.media-detail__cover-block {
  display: flex;
}

.media-detail__cover {
  width: 100%;
  border-radius: 12px;
  aspect-ratio: 2 / 3;
  object-fit: cover;
}

.media-detail__cover--empty {
  display: flex;
  align-items: center;
  justify-content: center;
  aspect-ratio: 2 / 3;
  background: #e5e7eb;
  color: #9ca3af;
  font-size: 48px;
}

.dark .media-detail__cover--empty {
  background: #374151;
  color: #d1d5db;
}

.media-detail__content {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-width: 0;
}

.media-detail__taxonomy {
  align-items: flex-start;
}

.media-detail__content-heading {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.media-detail__content-title {
  margin: 0;
  color: var(--text-primary);
  font-size: 1.5rem;
  font-weight: 700;
  line-height: 1.4;
  word-break: break-word;
}

.media-detail__title-trigger {
  width: 100%;
  padding: 0;
  border: none;
  background: transparent;
  color: inherit;
  font: inherit;
  font-weight: inherit;
  line-height: inherit;
  text-align: left;
  word-break: inherit;
  cursor: text;
  user-select: text;
  transition: color var(--transition-base, 0.2s) ease;
}

.media-detail__title-trigger:hover,
.media-detail__title-trigger:focus-visible,
.media-detail__title-trigger.is-original-visible {
  color: var(--primary, var(--el-color-primary, #409eff));
}

.media-detail__title-trigger:focus-visible {
  outline: 2px solid color-mix(in srgb, var(--primary, var(--el-color-primary, #409eff)) 32%, transparent);
  outline-offset: 4px;
  border-radius: 6px;
}

.media-detail__text {
  font-size: 14px;
  line-height: 1.7;
}

.media-detail__text--muted {
  color: var(--el-text-color-secondary);
}

.media-detail__meta-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.media-detail__meta-item h3,
.media-detail__section h3 {
  margin: 0 0 4px;
  font-size: 16px;
}

.media-detail__meta-item p,
.media-detail__section p {
  margin: 0;
  line-height: 1.75;
}

.media-detail__details {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding-top: 20px;
  border-top: 1px solid var(--line-divider, rgba(0, 0, 0, 0.08));
}

.media-detail__rating {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  color: var(--text-primary);
}

.media-detail__rating-main {
  display: inline-flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  min-width: 0;
}

.media-detail__rating-status {
  margin-left: auto;
}

.media-detail__rating-text {
  color: var(--el-text-color-secondary);
  font-size: 14px;
}

.media-detail :deep(.el-tag) {
  border-radius: 4px;
}

.media-detail-drawer__heading {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.media-detail-drawer__title {
  margin: 0;
  padding-left: 16px;
  position: relative;
  color: var(--text-primary);
  font-size: 1.125rem;
  font-weight: 700;
  line-height: 1.4;
}

.media-detail-drawer__title::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  width: 4px;
  height: 16px;
  border-radius: 2px;
  background: var(--primary, var(--el-color-primary, #409eff));
  transform: translateY(-50%);
}

.media-detail-drawer__close {
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

.media-detail-drawer__close:hover {
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
}

@media (max-width: 768px) {
  .base-drawer-layer {
    --base-drawer-bottom-gap: 12px;
  }

  .base-drawer__header {
    padding: 16px 16px 8px;
  }

  .base-drawer__body {
    padding: 10px 16px 16px;
  }

  .media-detail {
    gap: 20px;
  }

  .media-detail__hero {
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .media-detail__cover-block {
    max-width: 220px;
  }

  .media-detail__details {
    padding-top: 16px;
  }

  .media-detail__content-title {
    font-size: 1.25rem;
  }

  .media-detail__rating-status {
    margin-left: 0;
  }
}
</style>
