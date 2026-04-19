<script setup lang="ts">
/* global Blob, DragEvent, Event, File, HTMLImageElement, HTMLInputElement, Image, URL, crypto */
import { Delete, Download, Grid, List, Picture, Switch, UploadFilled } from '@element-plus/icons-vue'
import { ElButton, ElCard, ElEmpty, ElMessage, ElOption, ElSelect, ElSlider } from 'element-plus'
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'

type 导出格式 = 'image/png' | 'image/jpeg' | 'image/webp' | 'image/avif'
type 资源视图 = 'list' | 'cards'

type 图片信息 = {
  name: string
  size: number
  type: string
  width: number
  height: number
}

type 图片资源 = {
  id: string
  key: string
  previewUrl: string
  image: HTMLImageElement
  meta: 图片信息
}

type 导出格式选项 = {
  label: string
  value: 导出格式
  描述: string
}

type 导出能力表 = Record<导出格式, boolean>
type 图片预览项 = {
  src: string
  thumbSrc: string
  type: 'image'
  caption: string
}
type 图片预览实例 = {
  close: () => void
  show: (items: 图片预览项[], options?: Record<string, unknown>) => void
}

const 图片预览选项 = {
  groupAll: true,
  Thumbs: { autoStart: true, showOnStart: 'yes' },
  Toolbar: {
    display: {
      left: ['infobar'],
      middle: ['zoomIn', 'zoomOut', 'toggle1to1', 'rotateCCW', 'rotateCW', 'flipX', 'flipY'],
      right: ['slideshow', 'thumbs', 'close'],
    },
  },
  animated: true,
  dragToClose: true,
  keyboard: {
    Escape: 'close',
    Delete: 'close',
    Backspace: 'close',
    PageUp: 'next',
    PageDown: 'prev',
    ArrowUp: 'next',
    ArrowDown: 'prev',
    ArrowRight: 'next',
    ArrowLeft: 'prev',
  },
  fitToView: true,
  preload: 3,
  infinite: true,
  Panzoom: { maxScale: 3, minScale: 1 },
  caption: false,
  Carousel: { transition: 'slide' },
} as const

const fileInputRef = ref<HTMLInputElement | null>(null)
const isDragOver = ref(false)
const isConverting = ref(false)
const browserView = ref<资源视图>('list')
const imageList = ref<图片资源[]>([])
const activeImageId = ref<string | null>(null)
const hoverImageId = ref<string | null>(null)
const exportSupport = ref<导出能力表>({
  'image/png': true,
  'image/jpeg': false,
  'image/webp': false,
  'image/avif': false,
})

const exportOptions = reactive({
  format: 'image/png' as 导出格式,
  quality: 92,
  name: 'image',
})

const 导出格式列表: 导出格式选项[] = [
  { label: 'PNG', value: 'image/png', 描述: '无损，适合透明背景' },
  { label: 'JPG', value: 'image/jpeg', 描述: '有损压缩，体积通常更小' },
  { label: 'WEBP', value: 'image/webp', 描述: '兼顾透明与压缩率' },
  { label: 'AVIF', value: 'image/avif', 描述: '压缩率高，但依赖浏览器编码支持' },
]

const 资源视图列表 = [
  { value: 'list', title: '列表视图', icon: List },
  { value: 'cards', title: '卡片视图', icon: Grid },
] as const

const activeImage = computed(() => imageList.value.find((item) => item.id === activeImageId.value) ?? null)
const sourceImage = computed(() => activeImage.value?.image ?? null)
const sourceMeta = computed(() => activeImage.value?.meta ?? null)
const hasImages = computed(() => imageList.value.length > 0)
const hasActiveImage = computed(() => sourceImage.value !== null && sourceMeta.value !== null)
const activeImageIndex = computed(() => imageList.value.findIndex((item) => item.id === activeImageId.value))
const shouldShowQuality = computed(() => exportOptions.format !== 'image/png')
const outputExtension = computed(() => {
  switch (exportOptions.format) {
    case 'image/jpeg':
      return 'jpg'
    case 'image/webp':
      return 'webp'
    case 'image/avif':
      return 'avif'
    default:
      return 'png'
  }
})
const 当前导出格式描述 = computed(() => 导出格式列表.find((item) => item.value === exportOptions.format)?.描述 ?? '')
const 当前限制提示 = computed(() => {
  if (!sourceMeta.value) {
    return ''
  }

  if (sourceMeta.value.type === 'image/gif') {
    return '当前实现只处理静态位图，上传 GIF 时会取首帧导出，不保留动画。'
  }

  if (exportOptions.format === 'image/jpeg') {
    return '导出为 JPG 时透明区域会被填充为白底。'
  }

  return '当前转换不会保留 EXIF、ICC 和拍摄信息。'
})
const 浏览摘要 = computed(() => {
  if (!imageList.value.length) {
    return ''
  }
  if (activeImageIndex.value < 0) {
    return `共 ${imageList.value.length} 张`
  }
  return `当前第 ${activeImageIndex.value + 1} 张，共 ${imageList.value.length} 张`
})

let Fancybox实例: 图片预览实例 | null = null

function formatFileSize(size: number) {
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / 1024 / 1024).toFixed(1)} MB`
}

function buildDefaultName(fileName: string) {
  const normalized = fileName.replace(/\.[^.]+$/, '').trim()
  return normalized || 'image'
}

function buildFileKey(file: File) {
  return [file.name, file.size, file.lastModified, file.type].join('__')
}

function createImageId() {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID()
  }
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`
}

function revokeImageResource(resource: 图片资源) {
  URL.revokeObjectURL(resource.previewUrl)
}

function revokeImageResources(resources: 图片资源[]) {
  for (const resource of resources) {
    revokeImageResource(resource)
  }
}

async function 获取图片预览实例() {
  if (Fancybox实例) {
    return Fancybox实例
  }

  const [{ Fancybox }] = await Promise.all([
    import('@fancyapps/ui'),
    import('@fancyapps/ui/dist/fancybox/fancybox.css'),
  ])

  Fancybox实例 = Fancybox as unknown as 图片预览实例
  return Fancybox实例
}

function 关闭图片预览() {
  Fancybox实例?.close()
}

function resetState() {
  关闭图片预览()
  revokeImageResources(imageList.value)
  imageList.value = []
  activeImageId.value = null
  exportOptions.name = 'image'
}

function triggerFileDialog() {
  fileInputRef.value?.click()
}

async function probeExportSupport(format: 导出格式) {
  const canvas = document.createElement('canvas')
  canvas.width = 1
  canvas.height = 1
  const context = canvas.getContext('2d')
  if (!context) {
    return false
  }

  context.fillStyle = '#ffffff'
  context.fillRect(0, 0, 1, 1)

  const blob = await new Promise<Blob | null>((resolve) => {
    canvas.toBlob(resolve, format, 0.9)
  })

  return blob?.type === format
}

async function detectExportSupport() {
  const results = await Promise.all(导出格式列表.map(async (item) => [item.value, await probeExportSupport(item.value)] as const))
  const nextSupport: 导出能力表 = {
    'image/png': true,
    'image/jpeg': false,
    'image/webp': false,
    'image/avif': false,
  }

  for (const [format, supported] of results) {
    nextSupport[format] = supported
  }

  exportSupport.value = nextSupport
}

async function createImageResource(file: File) {
  const objectUrl = URL.createObjectURL(file)
  const image = new Image()
  image.decoding = 'async'
  image.src = objectUrl

  try {
    await image.decode()
  } catch {
    URL.revokeObjectURL(objectUrl)
    throw new Error('图片读取失败')
  }

  return {
    id: createImageId(),
    key: buildFileKey(file),
    previewUrl: objectUrl,
    image,
    meta: {
      name: file.name,
      size: file.size,
      type: file.type,
      width: image.naturalWidth,
      height: image.naturalHeight,
    },
  } satisfies 图片资源
}

async function loadImageFiles(files: File[]) {
  if (!files.length) {
    return
  }

  const existedKeys = new Set(imageList.value.map((item) => item.key))
  const nextFiles: File[] = []
  let invalidCount = 0
  let duplicateCount = 0

  for (const file of files) {
    if (!file.type.startsWith('image/')) {
      invalidCount += 1
      continue
    }

    const key = buildFileKey(file)
    if (existedKeys.has(key)) {
      duplicateCount += 1
      continue
    }

    existedKeys.add(key)
    nextFiles.push(file)
  }

  if (!nextFiles.length) {
    if (invalidCount > 0) {
      ElMessage.warning(`已跳过 ${invalidCount} 个非图片文件`)
    }
    if (duplicateCount > 0) {
      ElMessage.warning(`已跳过 ${duplicateCount} 个重复文件`)
    }
    return
  }

  const results = await Promise.allSettled(nextFiles.map((file) => createImageResource(file)))
  const nextResources: 图片资源[] = []
  let failedCount = 0

  for (const result of results) {
    if (result.status === 'fulfilled') {
      nextResources.push(result.value)
      continue
    }
    failedCount += 1
  }

  if (nextResources.length) {
    imageList.value = [...imageList.value, ...nextResources]
    activeImageId.value = nextResources[0].id
    ElMessage.success(`已载入 ${nextResources.length} 张图片`)
  }

  if (invalidCount > 0) {
    ElMessage.warning(`已跳过 ${invalidCount} 个非图片文件`)
  }
  if (duplicateCount > 0) {
    ElMessage.warning(`已跳过 ${duplicateCount} 个重复文件`)
  }
  if (failedCount > 0) {
    ElMessage.error(`有 ${failedCount} 张图片读取失败，请换一张试试`)
  }
}

function handleFileInputChange(event: Event) {
  const input = event.target as HTMLInputElement | null
  const files = input?.files ? Array.from(input.files) : []
  if (files.length) {
    void loadImageFiles(files)
  }
  if (input) {
    input.value = ''
  }
}

function handleDrop(event: DragEvent) {
  event.preventDefault()
  isDragOver.value = false
  const files = event.dataTransfer?.files ? Array.from(event.dataTransfer.files) : []
  if (files.length) {
    void loadImageFiles(files)
  }
}

function setActiveImage(id: string) {
  activeImageId.value = id
}

function getBrowserItemBackground(id: string) {
  if (id === activeImageId.value) {
    return 'rgba(var(--el-color-primary-rgb), 0.18)'
  }

  if (id === hoverImageId.value) {
    return 'rgba(var(--el-color-primary-rgb), 0.1)'
  }

  return 'var(--bg-card)'
}

async function openImagePreview(id: string, index: number) {
  setActiveImage(id)

  if (!imageList.value.length) {
    return
  }

  const Fancybox = await 获取图片预览实例()
  const items: 图片预览项[] = imageList.value.map((item) => ({
    src: item.previewUrl,
    thumbSrc: item.previewUrl,
    type: 'image',
    caption: item.meta.name,
  }))

  Fancybox.show(items, {
    ...图片预览选项,
    startIndex: index,
  })
}

function clearSource() {
  resetState()
}

function removeActiveImage() {
  if (!activeImageId.value) {
    return
  }

  关闭图片预览()

  const index = imageList.value.findIndex((item) => item.id === activeImageId.value)
  if (index < 0) {
    return
  }

  const current = imageList.value[index]
  revokeImageResource(current)

  const nextList = imageList.value.filter((item) => item.id !== current.id)
  imageList.value = nextList

  if (!nextList.length) {
    activeImageId.value = null
    return
  }

  activeImageId.value = nextList[Math.min(index, nextList.length - 1)].id
}

function downloadBlob(blob: Blob, fileName: string) {
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = fileName
  anchor.click()
  window.setTimeout(() => URL.revokeObjectURL(url), 1000)
}

async function exportConvertedImage() {
  if (!sourceImage.value || !sourceMeta.value) {
    ElMessage.warning('请先选择图片')
    return
  }

  if (!exportSupport.value[exportOptions.format]) {
    ElMessage.error('当前浏览器不支持导出该格式')
    return
  }

  isConverting.value = true
  try {
    const canvas = document.createElement('canvas')
    canvas.width = sourceMeta.value.width
    canvas.height = sourceMeta.value.height
    const context = canvas.getContext('2d')
    if (!context) {
      throw new Error('canvas 上下文创建失败')
    }

    context.imageSmoothingEnabled = true
    context.imageSmoothingQuality = 'high'
    if (exportOptions.format === 'image/jpeg') {
      context.fillStyle = '#ffffff'
      context.fillRect(0, 0, canvas.width, canvas.height)
    }
    context.drawImage(sourceImage.value, 0, 0, canvas.width, canvas.height)

    const quality = exportOptions.format === 'image/png' ? undefined : exportOptions.quality / 100
    const blob = await new Promise<Blob | null>((resolve) => {
      canvas.toBlob(resolve, exportOptions.format, quality)
    })

    if (!blob || blob.type !== exportOptions.format) {
      throw new Error('浏览器未返回目标格式数据')
    }

    const fileName = `${(exportOptions.name || 'image').trim() || 'image'}.${outputExtension.value}`
    downloadBlob(blob, fileName)
    ElMessage.success('图片已开始下载')
  } catch {
    ElMessage.error('转换失败，请稍后重试')
  } finally {
    isConverting.value = false
  }
}

async function exportAllImages() {
  if (!imageList.value.length) {
    ElMessage.warning('没有待转换的图片')
    return
  }

  if (!exportSupport.value[exportOptions.format]) {
    ElMessage.error('当前浏览器不支持导出该格式')
    return
  }

  isConverting.value = true
  try {
    for (const item of imageList.value) {
      const canvas = document.createElement('canvas')
      canvas.width = item.meta.width
      canvas.height = item.meta.height
      const context = canvas.getContext('2d')
      if (!context) {
        continue
      }

      context.imageSmoothingEnabled = true
      context.imageSmoothingQuality = 'high'
      if (exportOptions.format === 'image/jpeg') {
        context.fillStyle = '#ffffff'
        context.fillRect(0, 0, canvas.width, canvas.height)
      }
      context.drawImage(item.image, 0, 0, canvas.width, canvas.height)

      const quality = exportOptions.format === 'image/png' ? undefined : exportOptions.quality / 100
      const blob = await new Promise<Blob | null>((resolve) => {
        canvas.toBlob(resolve, exportOptions.format, quality)
      })

      if (!blob || blob.type !== exportOptions.format) {
        continue
      }

      const baseName = buildDefaultName(item.meta.name)
      const fileName = `${baseName}.${outputExtension.value}`
      downloadBlob(blob, fileName)

      await new Promise((resolve) => setTimeout(resolve, 180))
    }
    ElMessage.success('全部转换已开始下载')
  } catch {
    ElMessage.error('批量转换失败，请稍后重试')
  } finally {
    isConverting.value = false
  }
}

watch(
  () => exportSupport.value,
  (support) => {
    if (support[exportOptions.format]) {
      return
    }

    const fallback = 导出格式列表.find((item) => support[item.value])
    if (fallback) {
      exportOptions.format = fallback.value
    }
  },
  { deep: true, immediate: true },
)

watch(activeImage, (nextImage) => {
  exportOptions.name = nextImage ? buildDefaultName(nextImage.meta.name) : 'image'
}, { immediate: true })

onMounted(() => {
  void detectExportSupport()
})

onBeforeUnmount(() => {
  关闭图片预览()
  revokeImageResources(imageList.value)
})
</script>

<template>
  <div class="convert-workbench">
    <div class="convert-grid">
      <aside class="convert-sidebar">
        <ElCard class="convert-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span class="card-header__title">
                <Picture class="card-header__icon" />
                选择图片
              </span>
            </div>
          </template>

          <input
            ref="fileInputRef"
            class="file-input"
            type="file"
            accept="image/*"
            multiple
            @change="handleFileInputChange"
          >

          <div
            class="upload-dropzone"
            :class="{ 'is-dragover': isDragOver }"
            @click="triggerFileDialog"
            @dragenter.prevent="isDragOver = true"
            @dragover.prevent="isDragOver = true"
            @dragleave.prevent="isDragOver = false"
            @drop="handleDrop"
          >
            <UploadFilled class="upload-dropzone__icon" />
            <strong>点击选择，或把图片拖到这里</strong>
            <p>支持一次加入多张图片，浏览器本地完成格式转换，不走后端接口。</p>
          </div>

          <div class="upload-actions">
            <ElButton :disabled="!hasActiveImage" @click="removeActiveImage">
              <Delete />
              移除当前
            </ElButton>
            <ElButton :disabled="!hasImages" @click="clearSource">
              清空全部
            </ElButton>
          </div>
        </ElCard>

        <ElCard class="convert-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span class="card-header__title">
                <Switch class="card-header__icon" />
                导出设置
              </span>
            </div>
          </template>

          <label class="export-field">
            <span>文件名</span>
            <input v-model="exportOptions.name" class="export-input" type="text" :disabled="!hasActiveImage">
          </label>

          <label class="export-field">
            <span>目标格式</span>
            <ElSelect v-model="exportOptions.format" :disabled="!hasActiveImage">
              <ElOption
                v-for="item in 导出格式列表"
                :key="item.value"
                :label="`${item.label} · ${item.描述}`"
                :value="item.value"
                :disabled="!exportSupport[item.value]"
              />
            </ElSelect>
          </label>

          <label v-if="shouldShowQuality" class="export-field">
            <span>质量 {{ exportOptions.quality }}%</span>
            <ElSlider v-model="exportOptions.quality" :disabled="!hasActiveImage" :min="60" :max="100" />
          </label>

          <div class="export-actions">
            <ElButton
              type="primary"
              size="large"
              :loading="isConverting"
              :disabled="!hasActiveImage"
              @click="exportConvertedImage"
            >
              <Download />
              转换选中
            </ElButton>
            <ElButton
              type="primary"
              size="large"
              :loading="isConverting"
              :disabled="!hasImages"
              @click="exportAllImages"
            >
              <Download />
              转换全部
            </ElButton>
          </div>
        </ElCard>
      </aside>

      <section class="convert-main">
        <ElCard class="convert-card browser-card" shadow="never">
          <template #header>
            <div class="card-header">
              <div class="browser-card__header-main">
                <div class="browser-card__summary">
                  <strong>{{ browserView === 'list' ? '图片列表' : '图片卡片' }}</strong>
                  <span class="browser-card__count">{{ 浏览摘要 }}</span>
                </div>
              </div>
              <div class="view-switch" aria-label="资源视图切换">
                <button
                  v-for="item in 资源视图列表"
                  :key="item.value"
                  type="button"
                  class="view-switch__button"
                  :class="{ 'is-active': browserView === item.value }"
                  :title="item.title"
                  @click="browserView = item.value"
                >
                  <component :is="item.icon" class="view-switch__icon" />
                </button>
              </div>
            </div>
          </template>

          <div
            class="browser-panel"
            :class="{ 'is-empty': !hasImages, 'is-dragover': isDragOver }"
            @dragenter.prevent="isDragOver = true"
            @dragover.prevent="isDragOver = true"
            @dragleave.prevent="isDragOver = false"
            @drop="handleDrop"
          >
            <div
              v-if="hasImages"
              class="browser-collection"
              :class="browserView === 'cards' ? 'is-cards' : 'is-list'"
            >
              <div
                v-for="(item, index) in imageList"
                :key="item.id"
                class="browser-item"
                :class="[browserView === 'cards' ? 'is-card' : 'is-row', { 'is-active': item.id === activeImageId }]"
                :style="{ background: getBrowserItemBackground(item.id) }"
                role="button"
                tabindex="0"
                @click="setActiveImage(item.id)"
                @mouseenter="hoverImageId = item.id"
                @mouseleave="hoverImageId = null"
                @keydown.enter.prevent="setActiveImage(item.id)"
                @keydown.space.prevent="setActiveImage(item.id)"
              >
                <button
                  type="button"
                  class="browser-item__preview"
                  :aria-label="`预览 ${item.meta.name}`"
                  @click.stop="openImagePreview(item.id, index)"
                >
                  <img class="browser-item__thumb" :src="item.previewUrl" :alt="item.meta.name">
                </button>
                <div class="browser-item__content">
                  <strong>{{ item.meta.name }}</strong>
                  <span>{{ item.meta.width }} × {{ item.meta.height }}</span>
                  <span>{{ formatFileSize(item.meta.size) }} · {{ item.meta.type || '未知' }}</span>
                </div>
              </div>
            </div>

            <div v-else class="browser-empty">
              <ElEmpty description="还没有待转换图片" />
            </div>
          </div>

          <p class="hint-text">
            {{ 当前限制提示 }}
          </p>
        </ElCard>
      </section>
    </div>
  </div>
</template>

<style scoped>
.convert-workbench {
  --convert-surface: color-mix(in srgb, var(--bg-card) 88%, white);
  --convert-surface-soft: color-mix(in srgb, var(--el-color-primary) 4%, var(--bg-card));
  --convert-border-soft: color-mix(in srgb, var(--el-color-primary) 10%, var(--border-color));
  --convert-border-strong: color-mix(in srgb, var(--el-color-primary) 22%, var(--border-color));
  --convert-title: var(--text-primary);
  --convert-text: var(--text-secondary);
  --convert-text-soft: color-mix(in srgb, var(--text-secondary) 88%, var(--el-color-primary));
  display: grid;
}

.convert-grid {
  display: grid;
  grid-template-columns: 340px minmax(0, 1fr);
  gap: 18px;
  align-items: start;
}

.convert-sidebar,
.convert-main {
  display: grid;
  gap: 16px;
  min-width: 0;
}

.convert-card {
  border-radius: 24px;
  border-color: var(--convert-border-soft);
  background: color-mix(in srgb, var(--convert-surface) 92%, transparent);
  box-shadow: 0 12px 30px rgba(15, 23, 42, 0.05);
  backdrop-filter: blur(14px);
}

.convert-card :deep(.el-card__header) {
  border-bottom-color: var(--convert-border-soft);
  padding: 18px 20px 12px;
}

.convert-card :deep(.el-card__body) {
  padding: 18px 20px 20px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.card-header__title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 700;
  color: var(--convert-title);
}

.card-header__icon {
  width: 16px;
  height: 16px;
}

.file-input {
  display: none;
}

.upload-dropzone {
  min-height: 196px;
  padding: 20px;
  border: 1.5px dashed var(--convert-border-strong);
  border-radius: 22px;
  background:
    radial-gradient(circle at top, rgb(var(--el-color-primary-rgb) / 0.1), transparent 54%),
    var(--convert-surface-soft);
  display: grid;
  place-items: center;
  text-align: center;
  gap: 8px;
  cursor: pointer;
  transition:
    border-color 0.18s ease,
    transform 0.18s ease,
    background-color 0.18s ease;
}

.upload-dropzone:hover,
.upload-dropzone.is-dragover {
  transform: translateY(-1px);
  border-color: rgb(var(--el-color-primary-rgb) / 0.32);
  background:
    radial-gradient(circle at top, rgb(var(--el-color-primary-rgb) / 0.16), transparent 54%),
    rgba(244, 250, 246, 0.98);
}

.upload-dropzone__icon {
  width: 28px;
  height: 28px;
  color: var(--el-color-primary);
}

.upload-dropzone strong {
  color: var(--convert-title);
  font-size: 16px;
}

.upload-dropzone p {
  color: var(--convert-text);
  line-height: 1.7;
}

.upload-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 10px;
  margin-top: 14px;
}

.meta-stack {
  display: grid;
  gap: 10px;
  margin-top: 16px;
}

.meta-stack--two-column {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.meta-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  border-radius: 16px;
  background: var(--convert-surface-soft);
}

.meta-row span {
  color: var(--convert-text);
  font-size: 13px;
  white-space: nowrap;
}

.meta-row strong {
  color: var(--convert-title);
  line-height: 1.6;
  word-break: break-word;
  text-align: right;
}

.export-field {
  display: grid;
  gap: 8px;
  margin-bottom: 14px;
}

.export-field > span {
  color: var(--convert-text-soft);
  font-size: 13px;
  font-weight: 600;
}

.export-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 10px;
}

.export-input {
  min-height: 42px;
  padding: 0 14px;
  border: 1px solid var(--convert-border-soft);
  border-radius: 14px;
  background: color-mix(in srgb, var(--convert-surface-soft) 88%, white);
  color: var(--convert-title);
  outline: none;
  transition:
    border-color 0.18s ease,
    background-color 0.18s ease;
}

.export-input:focus {
  border-color: rgb(var(--el-color-primary-rgb) / 0.26);
  background: rgba(250, 253, 251, 0.98);
}

.export-input:disabled {
  cursor: not-allowed;
  opacity: 0.7;
}

.browser-card {
  min-width: 0;
  overflow: hidden;
}

.browser-card :deep(.el-card__header) {
  padding: 10px 20px;
}

.browser-card__header-main {
  display: flex;
  align-items: center;
  min-width: 0;
}

.browser-card__summary {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 12px;
  min-width: 0;
}

.browser-card__summary strong {
  color: var(--convert-title);
  font-size: 16px;
  line-height: 1.4;
}

.browser-card__count {
  color: var(--convert-text);
  font-size: 13px;
  white-space: nowrap;
}

.view-switch {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px;
  border-radius: 10px;
  border: 1px solid color-mix(in srgb, var(--el-color-primary) 14%, var(--border-color));
  background: color-mix(in srgb, var(--convert-surface-soft) 92%, white);
}

.view-switch__button {
  width: 34px;
  height: 24px;
  border: none;
  border-radius: 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  color: var(--convert-text);
  cursor: pointer;
  transition:
    background-color 0.18s ease,
    color 0.18s ease,
    transform 0.18s ease;
}

.view-switch__button:hover {
  color: var(--convert-title);
  transform: translateY(-1px);
}

.view-switch__button.is-active {
  background: rgb(var(--el-color-primary-rgb) / 0.14);
  color: var(--el-color-primary);
}

.view-switch__icon {
  width: 16px;
  height: 16px;
}

.browser-panel {
  min-width: 0;
  min-height: 760px;
  padding: 0;
  border-radius: 24px;
  border: none;
  background: transparent;
  display: grid;
  gap: 12px;
  transition:
    box-shadow 0.18s ease,
    background-color 0.18s ease;
}

.browser-panel.is-dragover {
  background: rgb(var(--el-color-primary-rgb) / 0.04);
  box-shadow: inset 0 0 0 1.5px rgb(var(--el-color-primary-rgb) / 0.26);
}

.browser-collection {
  min-height: 0;
  overflow: auto;
  padding-right: 4px;
  align-content: start;
}

.browser-collection.is-list {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  grid-auto-rows: max-content;
  gap: 10px;
  align-items: start;
}

.browser-collection.is-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 220px));
  gap: 10px 18px;
  justify-content: flex-start;
  align-content: flex-start;
  align-items: start;
}

.browser-item {
  width: 100%;
  height: auto;
  padding: 0;
  border: 1px solid color-mix(in srgb, var(--el-color-primary) 12%, var(--border-color));
  border-radius: 18px;
  background: var(--bg-card);
  text-align: left;
  cursor: pointer;
  transition:
    border-color 0.18s ease,
    background 0.18s ease,
    transform 0.18s ease,
    box-shadow 0.18s ease;
  align-self: start;
  outline: none;
}

.browser-item:hover {
  border-color: color-mix(in srgb, var(--el-color-primary) 30%, transparent);
  box-shadow: 0 8px 18px rgb(var(--el-color-primary-rgb) / 0.08);
}

.browser-item:focus-visible {
  border-color: color-mix(in srgb, var(--el-color-primary) 34%, transparent);
  box-shadow: 0 0 0 3px rgb(var(--el-color-primary-rgb) / 0.12);
}

.browser-item.is-active {
  border-color: color-mix(in srgb, var(--el-color-primary) 38%, transparent);
  box-shadow: 0 10px 22px rgb(var(--el-color-primary-rgb) / 0.1);
}

.browser-item.is-row {
  display: grid;
  grid-template-columns: 88px minmax(0, 1fr);
  gap: 12px;
  align-items: center;
  padding: 10px;
}

.browser-item.is-card {
  display: grid;
  gap: 10px;
  padding: 10px;
  width: 220px;
  max-width: 100%;
}

.browser-item__preview {
  padding: 0;
  border: none;
  border-radius: 14px;
  background: transparent;
  cursor: zoom-in;
  overflow: hidden;
}

.browser-item__thumb {
  display: block;
  width: 100%;
  aspect-ratio: 1;
  border-radius: 14px;
  object-fit: cover;
  background: rgba(255, 255, 255, 0.72);
  transition: transform 0.18s ease;
}

.browser-item__preview:hover .browser-item__thumb {
  transform: scale(1.02);
}

.browser-item__content {
  display: grid;
  gap: 4px;
  min-width: 0;
}

.browser-item__content strong {
  color: var(--convert-title);
  line-height: 1.5;
  word-break: break-word;
}

.browser-item__content span {
  color: var(--convert-text);
  font-size: 12px;
  line-height: 1.5;
  word-break: break-word;
}

.browser-empty {
  display: grid;
  place-items: center;
  min-height: 260px;
}

.hint-text {
  margin-top: 14px;
  color: var(--convert-text);
  line-height: 1.8;
}

.dark .convert-card {
  --convert-surface: color-mix(in srgb, var(--bg-card) 92%, transparent);
  --convert-surface-soft: color-mix(in srgb, var(--el-color-primary-light-5) 8%, var(--bg-card));
  --convert-border-soft: color-mix(in srgb, var(--el-color-primary-light-5) 10%, var(--border-color));
  --convert-border-strong: color-mix(in srgb, var(--el-color-primary-light-5) 18%, var(--border-color));
  --convert-title: var(--text-primary);
  --convert-text: var(--text-secondary);
  --convert-text-soft: color-mix(in srgb, var(--text-secondary) 86%, var(--el-color-primary-light-5));
  background:
    linear-gradient(145deg, color-mix(in srgb, var(--el-color-primary-light-5) 10%, transparent), rgba(16, 24, 22, 0.92)),
    var(--convert-surface);
  border-color: var(--convert-border-soft);
  box-shadow: 0 18px 40px rgba(2, 6, 23, 0.26);
}

.dark .meta-row,
.dark .upload-dropzone,
.dark .export-input,
.dark .browser-item,
.dark .view-switch {
  background: var(--convert-surface-soft);
  border-color: var(--convert-border-soft);
}

.dark .upload-dropzone:hover,
.dark .upload-dropzone.is-dragover {
  background: color-mix(in srgb, var(--el-color-primary-light-5) 12%, var(--bg-card));
}

.dark .view-switch__button.is-active {
  background: rgb(var(--el-color-primary-rgb) / 0.22);
  color: #f3fbf6;
}

@media (max-width: 1280px) {
  .convert-grid {
    grid-template-columns: 1fr;
  }

  .browser-panel {
    min-height: 560px;
  }
}

@media (max-width: 900px) {
  .card-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .view-switch {
    order: 2;
    align-self: flex-start;
    margin-top: 2px;
  }
}

@media (max-width: 767px) {
  .convert-card :deep(.el-card__header),
  .convert-card :deep(.el-card__body) {
    padding-left: 16px;
    padding-right: 16px;
  }

  .meta-stack--two-column,
  .browser-collection.is-cards {
    grid-template-columns: 1fr;
  }

  .browser-item.is-row {
    grid-template-columns: 64px minmax(0, 1fr);
  }

  .browser-item.is-card {
    width: 100%;
  }

  .browser-panel {
    min-height: 420px;
    padding: 12px;
  }
}
</style>
