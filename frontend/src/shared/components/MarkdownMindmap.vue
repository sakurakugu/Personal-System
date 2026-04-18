<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import type { Transformer } from 'markmap-lib'
import type { Markmap, IMarkmapOptions } from 'markmap-view'
import { useThemeStore } from '../stores/theme'

const props = withDefaults(defineProps<{
  content: string
  title?: string
  height?: string | number
  emptyText?: string
}>(), {
  title: '',
  height: 560,
  emptyText: '暂无可展示的结构化内容',
})

const themeStore = useThemeStore()
const 容器引用 = ref<globalThis.HTMLDivElement | null>(null)
const SVG引用 = ref<globalThis.SVGSVGElement | null>(null)
const 正在渲染 = ref(false)
const 渲染错误 = ref('')
const 已渲染 = ref(false)

let 脑图实例: Markmap | null = null
let 尺寸观察器: globalThis.ResizeObserver | null = null
let 动画帧标识 = 0
let 最新渲染序号 = 0
let transformer: Transformer | null = null
let 脑图库任务: Promise<{
  Transformer: typeof import('markmap-lib').Transformer
  Markmap: typeof import('markmap-view').Markmap
  loadCSS: typeof import('markmap-view').loadCSS
  loadJS: typeof import('markmap-view').loadJS
}> | null = null

function 读取主题颜色(name: string, fallback: string) {
  if (typeof window === 'undefined') {
    return fallback
  }

  return window.getComputedStyle(document.documentElement).getPropertyValue(name).trim() || fallback
}

const 主题色板 = computed(() => {
  const 当前色相 = themeStore.hue
  const 浅色主色 = 读取主题颜色('--el-color-primary', '#18a058')
  const 深色主色 = 读取主题颜色('--el-color-primary-light-5', '#4ade80')
  return themeStore.isDark
    ? [当前色相 >= 0 ? 深色主色 : '#4ade80', '#60a5fa', '#fbbf24', '#f87171', '#a78bfa', '#22d3ee']
    : [当前色相 >= 0 ? 浅色主色 : '#18a058', '#2563eb', '#d97706', '#dc2626', '#7c3aed', '#0f766e']
})

const 容器样式 = computed(() => ({
  '--markdown-mindmap-height': 格式化高度(props.height),
}))

const 脑图源码 = computed(() => 构建脑图源码(props.title, props.content))

function 格式化高度(height: string | number) {
  return typeof height === 'number' ? `${height}px` : height
}

function 构建脑图源码(title: string, content: string) {
  const 标题 = title.trim()
  if (!标题) {
    return content
  }

  const Frontmatter匹配结果 = content.match(/^---\r?\n[\s\S]*?\r?\n---(?:\r?\n|$)/)
  if (Frontmatter匹配结果) {
    const frontmatter = Frontmatter匹配结果[0]
    const body = content.slice(frontmatter.length)
    if (/^\s*#\s+/.test(body)) {
      return content
    }

    const 片段 = [frontmatter.trimEnd(), '', `# ${标题}`]
    if (body.trim()) {
      片段.push('', body.trimStart())
    }
    return 片段.join('\n')
  }

  if (/^\s*#\s+/.test(content)) {
    return content
  }

  if (!content.trim()) {
    return `# ${标题}`
  }

  return `# ${标题}\n\n${content.trimStart()}`
}

function 创建脑图配置(): Partial<IMarkmapOptions> {
  return {
    autoFit: true,
    duration: 180,
    fitRatio: 0.92,
    initialExpandLevel: -1,
    maxInitialScale: 2,
    maxWidth: 280,
    nodeMinHeight: 20,
    paddingX: 18,
    pan: true,
    scrollForPan: false,
    spacingHorizontal: 110,
    spacingVertical: 14,
    toggleRecursively: false,
    zoom: true,
    color: (node) => 主题色板.value[node.state.depth % 主题色板.value.length] || 主题色板.value[0],
    lineWidth: (node) => Math.max(2, 4 - node.state.depth * 0.45),
  }
}

function 获取脑图库() {
  if (!脑图库任务) {
    脑图库任务 = Promise.all([
      import('markmap-lib'),
      import('markmap-view'),
    ]).then(([markmapLib, markmapView]) => ({
      Transformer: markmapLib.Transformer,
      Markmap: markmapView.Markmap,
      loadCSS: markmapView.loadCSS,
      loadJS: markmapView.loadJS,
    }))
  }

  return 脑图库任务
}

function 清理脑图实例() {
  脑图实例?.destroy()
  脑图实例 = null
  if (SVG引用.value) {
    SVG引用.value.innerHTML = ''
  }
}

function 安排适应画布() {
  if (!脑图实例) {
    return
  }

  if (动画帧标识) {
    window.cancelAnimationFrame(动画帧标识)
  }

  动画帧标识 = window.requestAnimationFrame(() => {
    动画帧标识 = 0
    void 脑图实例?.fit()
  })
}

async function 渲染脑图() {
  const source = 脑图源码.value.trim()
  if (!SVG引用.value) {
    return
  }

  if (!source) {
    清理脑图实例()
    已渲染.value = false
    渲染错误.value = ''
    return
  }

  const 当前渲染序号 = ++最新渲染序号
  正在渲染.value = true
  渲染错误.value = ''

  try {
    const 脑图库 = await 获取脑图库()
    transformer ||= new 脑图库.Transformer()

    const 转换结果 = transformer.transform(source)
    const 资源 = transformer.getUsedAssets(转换结果.features)

    await Promise.all([
      脑图库.loadCSS(资源.styles || []),
      脑图库.loadJS(资源.scripts || []),
    ])

    if (当前渲染序号 !== 最新渲染序号 || !SVG引用.value) {
      return
    }

    if (!脑图实例) {
      脑图实例 = 脑图库.Markmap.create(SVG引用.value, 创建脑图配置())
    }

    await 脑图实例.setData(转换结果.root, 创建脑图配置())
    已渲染.value = true
    安排适应画布()
  } catch (error) {
    console.error(error)
    渲染错误.value = '思维导图渲染失败'
    已渲染.value = false
    清理脑图实例()
  } finally {
    if (当前渲染序号 === 最新渲染序号) {
      正在渲染.value = false
    }
  }
}

function 初始化尺寸观察() {
  if (!容器引用.value || typeof window.ResizeObserver === 'undefined') {
    return
  }

  尺寸观察器 = new window.ResizeObserver(() => {
    安排适应画布()
  })
  尺寸观察器.observe(容器引用.value)
}

onMounted(() => {
  初始化尺寸观察()
  void 渲染脑图()
})

watch(
  [脑图源码, () => themeStore.isDark],
  () => {
    void 渲染脑图()
  },
  { flush: 'post' },
)

onBeforeUnmount(() => {
  if (动画帧标识) {
    window.cancelAnimationFrame(动画帧标识)
  }
  尺寸观察器?.disconnect()
  清理脑图实例()
})
</script>

<template>
  <div ref="容器引用" class="markdown-mindmap" :style="容器样式">
    <svg
      v-show="已渲染"
      ref="SVG引用"
      class="markdown-mindmap__svg"
      aria-label="Markdown 思维导图"
    />
    <div v-if="!脑图源码.trim() && !正在渲染" class="markdown-mindmap__placeholder">
      {{ emptyText }}
    </div>
    <div v-else-if="渲染错误" class="markdown-mindmap__placeholder markdown-mindmap__placeholder--error">
      {{ 渲染错误 }}
    </div>
    <div v-else-if="正在渲染 && !已渲染" class="markdown-mindmap__placeholder">
      正在生成思维导图...
    </div>
  </div>
</template>

<style scoped>
.markdown-mindmap {
  position: relative;
  min-height: var(--markdown-mindmap-height);
  height: var(--markdown-mindmap-height);
  overflow: hidden;
  border: 1px solid var(--el-border-color, var(--border-color));
  border-radius: 12px;
  background:
    radial-gradient(circle at top left, rgb(var(--el-color-primary-rgb) / 0.08), transparent 42%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(247, 249, 251, 0.98));
}

.markdown-mindmap__svg {
  width: 100%;
  height: 100%;
}

.markdown-mindmap__placeholder {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  color: var(--el-text-color-secondary, var(--text-secondary));
  font-size: 14px;
  text-align: center;
}

.markdown-mindmap__placeholder--error {
  color: var(--el-color-danger, #dc2626);
}

.markdown-mindmap :deep(.markmap-node > circle) {
  stroke: rgba(15, 23, 42, 0.08);
  stroke-width: 1.5px;
}

.markdown-mindmap :deep(.markmap-link) {
  stroke-opacity: 0.42;
}

.markdown-mindmap :deep(.markmap-foreign) {
  overflow: visible;
}

.markdown-mindmap :deep(.markmap-foreign div) {
  color: var(--el-text-color-primary, var(--text-primary));
  font-size: 14px;
  line-height: 1.45;
  font-weight: 500;
  white-space: nowrap;
}

:global(.dark .markdown-mindmap) {
  background:
    radial-gradient(circle at top left, rgba(74, 222, 128, 0.14), transparent 40%),
    linear-gradient(180deg, rgba(15, 23, 42, 0.96), rgba(20, 28, 40, 0.98));
  border-color: rgba(148, 163, 184, 0.18);
}

:global(.dark .markdown-mindmap .markmap-node > circle) {
  stroke: rgba(148, 163, 184, 0.2);
}

:global(.dark .markdown-mindmap .markmap-link) {
  stroke-opacity: 0.54;
}

:global(.dark .markdown-mindmap .markmap-foreign div) {
  color: var(--text-primary);
}
</style>
