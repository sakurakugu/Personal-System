<script setup lang="ts">
/* global Blob, DragEvent, Event, File, HTMLImageElement, HTMLInputElement, Image, URL */
import { computed, onBeforeUnmount, onMounted, reactive, ref, shallowRef, watch } from 'vue'
import { ElButton, ElCard, ElEmpty, ElMessage, ElOption, ElSelect, ElSlider, ElTag } from 'element-plus'
import { Download, Picture, Switch, Delete, UploadFilled } from '@element-plus/icons-vue'

type 导出格式 = 'image/png' | 'image/jpeg' | 'image/webp' | 'image/avif'

type 图片信息 = {
  name: string
  size: number
  type: string
  width: number
  height: number
}

type 导出格式选项 = {
  label: string
  value: 导出格式
  描述: string
}

type 导出能力表 = Record<导出格式, boolean>

const fileInputRef = ref<HTMLInputElement | null>(null)
const isDragOver = ref(false)
const isConverting = ref(false)
const currentObjectUrl = ref<string | null>(null)
const sourcePreviewUrl = ref<string | null>(null)
const sourceImage = shallowRef<HTMLImageElement | null>(null)
const sourceMeta = ref<图片信息 | null>(null)
const exportSupport = ref<导出能力表>({
  'image/png': true,
  'image/jpeg': false,
  'image/webp': false,
  'image/avif': false,
})

const exportOptions = reactive({
  format: 'image/png' as 导出格式,
  quality: 92,
  name: 'converted-image',
})

const 导出格式列表: 导出格式选项[] = [
  { label: 'PNG', value: 'image/png', 描述: '无损，适合透明背景' },
  { label: 'JPG', value: 'image/jpeg', 描述: '有损压缩，体积通常更小' },
  { label: 'WEBP', value: 'image/webp', 描述: '兼顾透明与压缩率' },
  { label: 'AVIF', value: 'image/avif', 描述: '压缩率高，但依赖浏览器编码支持' },
]

const hasImage = computed(() => sourceImage.value !== null && sourceMeta.value !== null)
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
const 源图尺寸文本 = computed(() => {
  if (!sourceMeta.value) return '未选择图片'
  return `${sourceMeta.value.width} × ${sourceMeta.value.height}`
})
const 源图体积文本 = computed(() => {
  if (!sourceMeta.value) return '0 B'
  return formatFileSize(sourceMeta.value.size)
})
const 支持导出的格式数量 = computed(() => 导出格式列表.filter((item) => exportSupport.value[item.value]).length)
const 当前限制提示 = computed(() => {
  if (!sourceMeta.value) {
    return '纯前端转换基于浏览器原生解码和编码能力，不会上传图片到服务器。'
  }

  if (sourceMeta.value.type === 'image/gif') {
    return '当前实现只处理静态位图，上传 GIF 时会取首帧导出，不保留动画。'
  }

  if (exportOptions.format === 'image/jpeg') {
    return '导出为 JPG 时透明区域会被填充为白底。'
  }

  return '当前转换不会保留 EXIF、ICC 和拍摄信息，如需保留元数据应走后端或专门编解码库。'
})

function formatFileSize(size: number) {
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / 1024 / 1024).toFixed(1)} MB`
}

function revokeCurrentObjectUrl() {
  if (!currentObjectUrl.value) {
    return
  }
  URL.revokeObjectURL(currentObjectUrl.value)
  currentObjectUrl.value = null
}

function clearSource() {
  revokeCurrentObjectUrl()
  sourcePreviewUrl.value = null
  sourceImage.value = null
  sourceMeta.value = null
  exportOptions.name = 'converted-image'
}

function buildDefaultName(fileName: string) {
  const normalized = fileName.replace(/\.[^.]+$/, '').trim()
  return normalized ? `${normalized}-converted` : 'converted-image'
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

async function loadImageFile(file: File) {
  if (!file.type.startsWith('image/')) {
    ElMessage.warning('请选择图片文件')
    return
  }

  revokeCurrentObjectUrl()
  const objectUrl = URL.createObjectURL(file)
  const image = new Image()
  image.decoding = 'async'
  image.src = objectUrl

  try {
    await image.decode()
  } catch {
    URL.revokeObjectURL(objectUrl)
    ElMessage.error('图片读取失败，请换一张试试')
    return
  }

  currentObjectUrl.value = objectUrl
  sourcePreviewUrl.value = objectUrl
  sourceImage.value = image
  sourceMeta.value = {
    name: file.name,
    size: file.size,
    type: file.type,
    width: image.naturalWidth,
    height: image.naturalHeight,
  }
  exportOptions.name = buildDefaultName(file.name)
}

function handleFileInputChange(event: Event) {
  const input = event.target as HTMLInputElement | null
  const file = input?.files?.[0]
  if (file) {
    void loadImageFile(file)
  }
  if (input) {
    input.value = ''
  }
}

function handleDrop(event: DragEvent) {
  event.preventDefault()
  isDragOver.value = false
  const file = event.dataTransfer?.files?.[0]
  if (file) {
    void loadImageFile(file)
  }
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

    const fileName = `${(exportOptions.name || 'converted-image').trim() || 'converted-image'}.${outputExtension.value}`
    downloadBlob(blob, fileName)
    ElMessage.success('图片已开始下载')
  } catch {
    ElMessage.error('转换失败，请稍后重试')
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

onMounted(() => {
  void detectExportSupport()
})

onBeforeUnmount(() => {
  revokeCurrentObjectUrl()
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
            <p>浏览器本地完成格式转换，不走后端接口。</p>
          </div>

          <div class="upload-actions">
            <ElButton type="primary" @click="triggerFileDialog">选择图片</ElButton>
            <ElButton :disabled="!hasImage" @click="clearSource">
              <Delete />
              清空
            </ElButton>
          </div>

          <div v-if="sourceMeta" class="meta-stack">
            <div class="meta-row">
              <span>文件名</span>
              <strong>{{ sourceMeta.name }}</strong>
            </div>
            <div class="meta-row">
              <span>原始格式</span>
              <strong>{{ sourceMeta.type || '未知' }}</strong>
            </div>
            <div class="meta-row">
              <span>源图尺寸</span>
              <strong>{{ 源图尺寸文本 }}</strong>
            </div>
            <div class="meta-row">
              <span>文件体积</span>
              <strong>{{ 源图体积文本 }}</strong>
            </div>
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
            <input v-model="exportOptions.name" class="export-input" type="text" :disabled="!hasImage">
          </label>

          <label class="export-field">
            <span>目标格式</span>
            <ElSelect v-model="exportOptions.format" :disabled="!hasImage">
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
            <ElSlider v-model="exportOptions.quality" :disabled="!hasImage" :min="60" :max="100" />
          </label>

          <div class="meta-stack meta-stack--two-column">
            <div class="meta-row">
              <span>扩展名</span>
              <strong>.{{ outputExtension }}</strong>
            </div>
            <div class="meta-row">
              <span>可用编码</span>
              <strong>{{ 支持导出的格式数量 }} 种</strong>
            </div>
          </div>

          <p class="hint-text">{{ 当前导出格式描述 }}</p>

          <ElButton
            type="primary"
            size="large"
            :loading="isConverting"
            :disabled="!hasImage"
            @click="exportConvertedImage"
          >
            <Download />
            下载转换结果
          </ElButton>
        </ElCard>
      </aside>

      <section class="convert-main">
        <ElCard class="convert-card preview-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span class="card-header__title">源图预览</span>
              <div class="preview-tags">
                <ElTag round effect="plain">纯前端</ElTag>
                <ElTag round effect="plain">本地处理</ElTag>
              </div>
            </div>
          </template>

          <div
            class="preview-stage"
            :class="{ 'is-empty': !hasImage, 'is-dragover': isDragOver }"
            @dragenter.prevent="isDragOver = true"
            @dragover.prevent="isDragOver = true"
            @dragleave.prevent="isDragOver = false"
            @drop="handleDrop"
          >
            <img v-if="sourcePreviewUrl" class="preview-image" :src="sourcePreviewUrl" alt="待转换图片预览">
            <div v-else class="preview-empty">
              <ElEmpty description="先选择一张图片" />
            </div>
          </div>

          <p class="preview-hint">
            {{ 当前限制提示 }}
          </p>
        </ElCard>

        <ElCard class="convert-card capability-card" shadow="never">
          <template #header>
            <div class="card-header capability-header">
              <span class="card-header__title">浏览器能力</span>
              <div class="capability-header__tags">
                <ElTag class="capability-summary-tag capability-summary-tag--active" round effect="plain">
                  已支持 {{ 支持导出的格式数量 }}
                </ElTag>
                <ElTag class="capability-summary-tag" round effect="plain">
                  共 {{ 导出格式列表.length }} 种
                </ElTag>
              </div>
            </div>
          </template>

          <div class="capability-list">
            <div
              v-for="item in 导出格式列表"
              :key="item.value"
              class="capability-item"
              :class="{ 'is-supported': exportSupport[item.value], 'is-unsupported': !exportSupport[item.value] }"
            >
              <div class="capability-item__main">
                <strong>{{ item.label }}</strong>
                <span>{{ item.描述 }}</span>
              </div>
              <ElTag
                class="capability-state-tag"
                :class="exportSupport[item.value] ? 'is-supported' : 'is-unsupported'"
                round
                effect="plain"
              >
                {{ exportSupport[item.value] ? '可导出' : '当前浏览器不支持' }}
              </ElTag>
            </div>
          </div>

          <p class="hint-text">
            能力检测基于当前浏览器的 `canvas.toBlob` 实测结果，所以同一套前端代码在不同浏览器里可用格式可能不同。
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
  --convert-preview-bg: color-mix(in srgb, var(--bg-primary) 94%, var(--el-color-primary) 6%);
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
  display: grid;
  gap: 6px;
  padding: 12px 14px;
  border-radius: 16px;
  background: var(--convert-surface-soft);
}

.meta-row span {
  color: var(--convert-text);
  font-size: 13px;
}

.meta-row strong {
  color: var(--convert-title);
  line-height: 1.6;
  word-break: break-word;
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

.preview-card,
.capability-card {
  min-width: 0;
}

.capability-header {
  align-items: flex-start;
}

.capability-header__tags {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
}

.capability-summary-tag {
  border-color: color-mix(in srgb, var(--el-color-primary) 24%, transparent);
  background: color-mix(in srgb, var(--el-color-primary) 8%, transparent);
  color: var(--el-color-primary);
}

.capability-summary-tag--active {
  border-color: color-mix(in srgb, var(--el-color-primary) 24%, transparent);
  background:
    linear-gradient(135deg, rgb(var(--el-color-primary-rgb) / 0.18), rgb(var(--el-color-primary-rgb) / 0.08)),
    var(--convert-surface-soft);
  color: color-mix(in srgb, var(--el-color-primary) 88%, black);
}

.preview-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.preview-stage {
  position: relative;
  min-height: 620px;
  overflow: hidden;
  border-radius: 24px;
  border: 1px solid var(--convert-border-soft);
  background:
    radial-gradient(circle at top, rgb(var(--el-color-primary-rgb) / 0.08), transparent 58%),
    var(--convert-preview-bg);
  display: grid;
  place-items: center;
}

.preview-stage.is-dragover {
  border-color: rgb(var(--el-color-primary-rgb) / 0.32);
}

.preview-stage.is-empty {
  display: grid;
  place-items: center;
}

.preview-image {
  display: block;
  width: 100%;
  height: 100%;
  max-width: 100%;
  max-height: 720px;
  object-fit: contain;
}

.preview-empty {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
}

.preview-hint,
.hint-text {
  margin-top: 14px;
  color: var(--convert-text);
  line-height: 1.8;
}

.capability-list {
  display: grid;
  gap: 12px;
}

.capability-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 16px;
  border-radius: 18px;
  background: var(--convert-surface-soft);
  border: 1px solid color-mix(in srgb, var(--el-color-primary) 12%, var(--border-color));
}

.capability-item.is-supported {
  border-color: color-mix(in srgb, var(--el-color-primary) 30%, transparent);
  background:
    linear-gradient(135deg, rgb(var(--el-color-primary-rgb) / 0.12), transparent 55%),
    var(--convert-surface-soft);
  box-shadow: 0 10px 22px rgb(var(--el-color-primary-rgb) / 0.08);
}

.capability-item.is-unsupported {
  border-color: color-mix(in srgb, #94a3b8 24%, var(--border-color));
  background:
    linear-gradient(135deg, rgb(148 163 184 / 0.1), rgb(148 163 184 / 0.03)),
    color-mix(in srgb, var(--bg-card) 92%, #eef2f7);
  box-shadow: none;
}

.capability-item__main {
  display: grid;
  gap: 4px;
}

.capability-item__main strong {
  color: var(--convert-title);
}

.capability-item.is-supported .capability-item__main strong {
  color: color-mix(in srgb, var(--el-color-primary) 72%, var(--convert-title));
}

.capability-item.is-unsupported .capability-item__main strong {
  color: color-mix(in srgb, #64748b 78%, var(--convert-title));
}

.capability-item__main span {
  color: var(--convert-text);
  line-height: 1.7;
}

.capability-item.is-unsupported .capability-item__main span {
  color: color-mix(in srgb, #64748b 72%, var(--convert-text));
}

.capability-state-tag {
  flex-shrink: 0;
}

.capability-state-tag.is-supported {
  border-color: color-mix(in srgb, var(--el-color-primary) 34%, transparent);
  background: rgb(var(--el-color-primary-rgb) / 0.12);
  color: color-mix(in srgb, var(--el-color-primary) 82%, black);
}

.capability-state-tag.is-unsupported {
  border-color: color-mix(in srgb, #94a3b8 28%, var(--border-color));
  background: rgb(148 163 184 / 0.12);
  color: #64748b;
}

.dark .convert-card {
  --convert-surface: color-mix(in srgb, var(--bg-card) 92%, transparent);
  --convert-surface-soft: color-mix(in srgb, var(--el-color-primary-light-5) 8%, var(--bg-card));
  --convert-border-soft: color-mix(in srgb, var(--el-color-primary-light-5) 10%, var(--border-color));
  --convert-border-strong: color-mix(in srgb, var(--el-color-primary-light-5) 18%, var(--border-color));
  --convert-title: var(--text-primary);
  --convert-text: var(--text-secondary);
  --convert-text-soft: color-mix(in srgb, var(--text-secondary) 86%, var(--el-color-primary-light-5));
  --convert-preview-bg: color-mix(in srgb, var(--bg-primary) 88%, var(--el-color-primary-light-5) 12%);
  background:
    linear-gradient(145deg, color-mix(in srgb, var(--el-color-primary-light-5) 10%, transparent), rgba(16, 24, 22, 0.92)),
    var(--convert-surface);
  border-color: var(--convert-border-soft);
  box-shadow: 0 18px 40px rgba(2, 6, 23, 0.26);
}

.dark .meta-row,
.dark .upload-dropzone,
.dark .export-input,
.dark .capability-item {
  background: var(--convert-surface-soft);
  border-color: var(--convert-border-soft);
}

.dark .upload-dropzone:hover,
.dark .upload-dropzone.is-dragover {
  background: color-mix(in srgb, var(--el-color-primary-light-5) 12%, var(--bg-card));
}

.dark .capability-summary-tag {
  border-color: color-mix(in srgb, var(--el-color-primary-light-4) 28%, transparent);
  background: color-mix(in srgb, var(--el-color-primary-light-5) 12%, transparent);
  color: var(--el-color-primary-light-3);
}

.dark .capability-summary-tag--active {
  border-color: color-mix(in srgb, var(--el-color-primary-light-3) 24%, transparent);
  background:
    linear-gradient(135deg, rgb(var(--el-color-primary-rgb) / 0.24), rgb(var(--el-color-primary-rgb) / 0.08)),
    var(--convert-surface-soft);
  color: #f3fbf6;
}

.dark .capability-item.is-unsupported {
  border-color: color-mix(in srgb, #94a3b8 18%, var(--border-color));
  background:
    linear-gradient(135deg, rgb(148 163 184 / 0.12), rgb(148 163 184 / 0.04)),
    color-mix(in srgb, var(--bg-card) 94%, #1f2937);
}

.dark .capability-item.is-unsupported .capability-item__main strong {
  color: #cbd5e1;
}

.dark .capability-item.is-unsupported .capability-item__main span {
  color: #94a3b8;
}

.dark .capability-state-tag.is-unsupported {
  border-color: color-mix(in srgb, #94a3b8 20%, var(--border-color));
  background: rgb(148 163 184 / 0.14);
  color: #cbd5e1;
}

@media (max-width: 900px) {
  .capability-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .capability-header__tags {
    justify-content: flex-start;
  }
}

@media (max-width: 1280px) {
  .convert-grid {
    grid-template-columns: 1fr;
  }

  .preview-stage {
    min-height: 520px;
  }
}

@media (max-width: 767px) {
  .convert-card :deep(.el-card__header),
  .convert-card :deep(.el-card__body) {
    padding-left: 16px;
    padding-right: 16px;
  }

  .preview-stage {
    min-height: 360px;
  }

  .meta-stack--two-column,
  .capability-item {
    grid-template-columns: 1fr;
  }

  .capability-item {
    align-items: flex-start;
    flex-direction: column;
  }

  .capability-state-tag {
    margin-left: 10px;
  }
}
</style>
