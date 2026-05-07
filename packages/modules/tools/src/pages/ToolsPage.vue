<script setup lang="ts">
import { Crop, Grid, Switch } from '@element-plus/icons-vue'
import { ElCard, ElEmpty, ElTag } from 'element-plus'
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ImageConvertWorkbench from '../components/ImageConvertWorkbench.vue'
import ImageEditorWorkbench from '../components/ImageEditorWorkbench.vue'
import ImageStitchWorkbench from '../components/ImageStitchWorkbench.vue'

type 图片工具值 = 'editor' | 'convert' | 'stitch'

const route = useRoute()
const router = useRouter()

const 工具选项 = [
  { label: '图片编辑', value: 'editor', icon: Crop },
  { label: '格式转换', value: 'convert', icon: Switch },
  { label: '图片拼接', value: 'stitch', icon: Grid },
] as const

const 占位配置: Record<Exclude<图片工具值, 'editor' | 'convert'>, {
  标题: string
  描述: string
  标签: string[]
}> = {
  stitch: {
    标题: '图片拼接',
    描述: '这里预留给图片拼接，后面可以补横向、纵向、宫格拼图和间距背景配置。',
    标签: ['横向拼接', '纵向拼接', '宫格排版'],
  },
}

const 当前工具 = computed<图片工具值>(() => {
  const queryValue = Array.isArray(route.query.imageTool)
    ? route.query.imageTool[0]
    : route.query.imageTool

  if (queryValue === 'convert' || queryValue === 'stitch' || queryValue === 'editor') {
    return queryValue
  }

  return 'editor'
})

const 当前占位配置 = computed(() => {
  if (当前工具.value === 'editor' || 当前工具.value === 'convert') {
    return null
  }

  return 占位配置[当前工具.value]
})

function 切换工具(value: string | number) {
  if (value !== 'editor' && value !== 'convert' && value !== 'stitch') {
    return
  }

  void router.replace({
    path: route.path,
    query: {
      ...route.query,
      imageTool: value === 'editor' ? undefined : value,
    },
  })
}
</script>

<template>
  <div class="tools-page">
    <section class="tools-hero">
      <nav class="tools-top-nav" aria-label="图片工具切换">
        <button
          v-for="item in 工具选项"
          :key="item.value"
          type="button"
          class="tools-top-nav__item"
          :class="{ 'is-active': 当前工具 === item.value }"
          :aria-pressed="当前工具 === item.value"
          @click="切换工具(item.value)"
        >
          <span class="tools-top-nav__icon">
            <component :is="item.icon" />
          </span>
          <span class="tools-top-nav__label">{{ item.label }}</span>
        </button>
      </nav>
    </section>

    <section class="tools-content">
      <ImageEditorWorkbench v-if="当前工具 === 'editor'" />
      <ImageConvertWorkbench v-else-if="当前工具 === 'convert'" />
      <ImageStitchWorkbench v-else-if="当前工具 === 'stitch'" />

      <ElCard v-else class="tool-placeholder" shadow="never">
        <div class="tool-placeholder__header">
          <div>
            <span class="tool-placeholder__eyebrow">规划中</span>
            <h2>{{ 当前占位配置?.标题 }}</h2>
            <p>{{ 当前占位配置?.描述 }}</p>
          </div>
        </div>

        <div class="tool-placeholder__tags">
          <ElTag
            v-for="tag in 当前占位配置?.标签 ?? []"
            :key="tag"
            effect="plain"
            round
          >
            {{ tag }}
          </ElTag>
        </div>

        <ElEmpty description="入口和切换结构已经留好，后续直接往这里补功能即可。" />
      </ElCard>
    </section>

    <slot name="footer" />
  </div>
</template>

<style scoped>
.tools-page {
  height: 100%;
  overflow-y: auto;
  padding: 18px;
  box-sizing: border-box;
  background:
    radial-gradient(circle at top left, rgb(var(--el-color-primary-rgb) / 0.1), transparent 28%),
    linear-gradient(180deg, #f6fbf8 0%, #f3f7f5 100%);
}

.tools-hero {
  margin-bottom: 18px;
  padding: 12px;
  border: 1px solid rgb(var(--el-color-primary-rgb) / 0.14);
  border-radius: 22px;
  background:
    linear-gradient(135deg, rgb(var(--el-color-primary-rgb) / 0.12), rgb(var(--el-color-primary-rgb) / 0.03)),
    linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(255, 255, 255, 0.99));
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.06);
}

.tools-top-nav {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
}

.tools-top-nav__item {
  min-width: 0;
  min-height: 48px;
  padding: 0 18px;
  border: 1px solid rgb(var(--el-color-primary-rgb) / 0.12);
  border-radius: 14px;
  background-color: rgba(255, 255, 255, 0.82);
  color: #475569;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  text-align: center;
  cursor: pointer;
  transition:
    transform 0.18s ease,
    border-color 0.18s ease,
    background-color 0.18s ease,
    box-shadow 0.18s ease,
    color 0.18s ease;
}

.tools-top-nav__item:hover {
  transform: translateY(-1px);
  border-color: rgb(var(--el-color-primary-rgb) / 0.24);
  background-color: rgba(var(--el-color-primary-rgb), 0.16);
  color: var(--el-color-primary);
  box-shadow: 0 10px 20px rgb(var(--el-color-primary-rgb) / 0.12);
}

.tools-top-nav__item:hover .tools-top-nav__icon {
  color: var(--el-color-primary);
}

.tools-top-nav__item:focus-visible {
  outline: 2px solid rgb(var(--el-color-primary-rgb) / 0.42);
  outline-offset: 2px;
}

.tools-top-nav__item.is-active {
  border-color: rgb(var(--el-color-primary-rgb) / 0.28);
  background-color: rgba(var(--el-color-primary-rgb), 0.22);
  color: var(--el-color-primary);
  box-shadow: 0 12px 24px rgb(var(--el-color-primary-rgb) / 0.16);
}

.tools-top-nav__item.is-active .tools-top-nav__icon {
  color: var(--el-color-primary);
}

.tools-top-nav__item.is-active:hover {
  background-color: rgba(var(--el-color-primary-rgb), 0.28);
}

.tools-top-nav__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 12px;
  color: #64748b;
  flex-shrink: 0;
}

.tools-top-nav__icon :deep(svg) {
  width: 18px;
  height: 18px;
}

.tools-top-nav__label {
  font-size: 14px;
  font-weight: 700;
  line-height: 1;
}

.tools-content {
  min-width: 0;
}

.tool-placeholder {
  border-radius: 24px;
  border: 1px solid rgb(var(--el-color-primary-rgb) / 0.12);
  background:
    linear-gradient(160deg, rgba(255, 255, 255, 0.96), rgba(248, 251, 249, 0.98)),
    linear-gradient(135deg, rgb(var(--el-color-primary-rgb) / 0.06), transparent 46%);
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.06);
}

.tool-placeholder__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.tool-placeholder h2 {
  margin: 0 0 10px;
  font-size: 28px;
  line-height: 1.15;
  color: #102418;
}

.tool-placeholder p {
  margin: 0;
  max-width: 720px;
  color: var(--el-text-color-secondary);
  line-height: 1.8;
}

.tool-placeholder__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 24px 0 12px;
}

.dark .tools-page {
  background:
    radial-gradient(circle at top left, color-mix(in srgb, var(--el-color-primary-light-5) 12%, transparent), transparent 28%),
    linear-gradient(180deg, #111916 0%, #0f1513 100%);
}

.dark .tools-hero,
.dark .tool-placeholder {
  border-color: color-mix(in srgb, var(--el-color-primary-light-5) 14%, transparent);
  background:
    linear-gradient(135deg, color-mix(in srgb, var(--el-color-primary-light-5) 14%, transparent), color-mix(in srgb, var(--el-color-primary-light-5) 5%, transparent)),
    rgba(18, 25, 22, 0.9);
  box-shadow: 0 18px 40px rgba(2, 6, 23, 0.24);
}

.dark .tools-top-nav__item {
  border-color: color-mix(in srgb, var(--el-color-primary-light-5) 12%, transparent);
  background-color: rgba(16, 24, 22, 0.72);
  color: #d7dee7;
}

.dark .tools-top-nav__item:hover {
  border-color: color-mix(in srgb, var(--el-color-primary-light-5) 22%, transparent);
  background-color: rgba(var(--el-color-primary-rgb), 0.2);
  color: var(--el-color-primary-light-3);
  box-shadow: 0 12px 24px rgba(2, 6, 23, 0.2);
}

.dark .tools-top-nav__item:hover .tools-top-nav__icon {
  color: var(--el-color-primary-light-3);
}

.dark .tools-top-nav__item.is-active {
  border-color: color-mix(in srgb, var(--el-color-primary-light-5) 28%, transparent);
  background-color: rgba(var(--el-color-primary-rgb), 0.26);
  color: var(--el-color-primary-light-3);
  box-shadow: 0 16px 30px rgba(2, 6, 23, 0.24);
}

.dark .tools-top-nav__item.is-active .tools-top-nav__icon {
  color: var(--el-color-primary-light-3);
}

.dark .tools-top-nav__item.is-active:hover {
  background-color: rgba(var(--el-color-primary-rgb), 0.32);
}

.dark .tools-top-nav__icon {
  color: #94a3b8;
}

.dark .tool-placeholder h2 {
  color: #eef8f1;
}

@media (max-width: 1080px) {
  .tools-top-nav__item {
    flex: 1 1 0;
  }
}

@media (max-width: 767px) {
  .tools-page {
    padding: 14px;
  }

  .tools-hero {
    padding: 10px;
  }

  .tools-top-nav {
    display: grid;
    grid-template-columns: 1fr;
  }

  .tools-top-nav__item {
    min-height: 52px;
    padding: 0 16px;
    justify-content: flex-start;
  }

  .tool-placeholder h2 {
    font-size: 24px;
  }
}
</style>
