<script setup lang="ts">
/* global Blob, CanvasRenderingContext2D, DragEvent, Event, File, HTMLCanvasElement, HTMLDivElement, HTMLImageElement, HTMLInputElement, Image, ResizeObserver, URL, crypto */
import {
  ArrowDown,
  ArrowUp,
  Delete,
  Download,
  Grid,
  Picture,
  UploadFilled,
} from '@element-plus/icons-vue'
import {
  ElButton,
  ElColorPicker,
  ElEmpty,
  ElInputNumber,
  ElMessage,
  ElOption,
  ElRadioButton,
  ElRadioGroup,
  ElSelect,
  ElSlider,
  ElSwitch,
  ElTag,
} from 'element-plus'
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import WorkbenchSectionCard from './WorkbenchSectionCard.vue'

type 拼接模式 = 'horizontal' | 'vertical' | 'grid' | 'subtitle'
type 导出格式 = 'image/png' | 'image/jpeg' | 'image/webp'
type 宫格填充模式 = 'contain' | 'cover'
type 宫格比例 = '1:1' | '4:3' | '3:4' | '16:9'

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

type 绘制项 = {
  id: string
  image: HTMLImageElement
  sourceX: number
  sourceY: number
  sourceWidth: number
  sourceHeight: number
  cellX: number
  cellY: number
  cellWidth: number
  cellHeight: number
  drawX: number
  drawY: number
  drawWidth: number
  drawHeight: number
  needsClip: boolean
}

type 拼接布局 = {
  width: number
  height: number
  items: 绘制项[]
}

type 拼接选项 = {
  layout: 拼接模式
  targetSize: number
  columns: number
  gap: number
  padding: number
  subtitleCropRatio: number
  gridAspect: 宫格比例
  gridFit: 宫格填充模式
  transparentBackground: boolean
  backgroundColor: string
}

type 导出设置 = {
  format: 导出格式
  quality: number
  name: string
}

const fileInputRef = ref<HTMLInputElement | null>(null)
const previewStageRef = ref<HTMLDivElement | null>(null)
const previewCanvasRef = ref<HTMLCanvasElement | null>(null)

const isDragOver = ref(false)
const isExporting = ref(false)
const imageList = ref<图片资源[]>([])
const activeImageId = ref<string | null>(null)

const stitchOptions = reactive<拼接选项>({
  layout: 'horizontal',
  targetSize: 480,
  columns: 3,
  gap: 24,
  padding: 24,
  subtitleCropRatio: 15,
  gridAspect: '1:1',
  gridFit: 'contain',
  transparentBackground: false,
  backgroundColor: '#f4f7f5',
})

const exportOptions = reactive<导出设置>({
  format: 'image/png',
  quality: 92,
  name: 'stitched-image',
})

const 拼接模式列表 = [
  { value: 'horizontal', label: '横向拼接' },
  { value: 'vertical', label: '纵向拼接' },
  { value: 'subtitle', label: '字幕拼接' },
  { value: 'grid', label: '宫格排版' },
] as const

const 宫格比例列表 = [
  { value: '1:1', label: '1:1' },
  { value: '4:3', label: '4:3' },
  { value: '3:4', label: '3:4' },
  { value: '16:9', label: '16:9' },
] as const

const 宫格填充列表 = [
  { value: 'contain', label: '完整显示', 描述: '保留完整图片，可能留白' },
  { value: 'cover', label: '铺满单元', 描述: '填满单元格，可能裁掉边缘' },
] as const

const 导出格式列表 = [
  { value: 'image/png', label: 'PNG', 描述: '适合透明背景和无损导出' },
  { value: 'image/jpeg', label: 'JPG', 描述: '体积较小，不支持透明' },
  { value: 'image/webp', label: 'WEBP', 描述: '压缩率更高，兼顾画质与体积' },
] as const

const 背景预设色 = ['#f4f7f5', '#ffffff', '#f5efe6', '#eff6ff', '#111827', '#1f2937']

const 当前图片 = computed(() => imageList.value.find((item) => item.id === activeImageId.value) ?? null)
const 是否有图片 = computed(() => imageList.value.length > 0)
const 是否展示质量 = computed(() => exportOptions.format !== 'image/png')
const 输出扩展名 = computed(() => {
  switch (exportOptions.format) {
    case 'image/jpeg':
      return 'jpg'
    case 'image/webp':
      return 'webp'
    default:
      return 'png'
  }
})
const 当前尺寸标签 = computed(() => {
  if (stitchOptions.layout === 'horizontal') {
    return '统一高度'
  }
  if (stitchOptions.layout === 'vertical') {
    return '统一宽度'
  }
  if (stitchOptions.layout === 'subtitle') {
    return '统一宽度'
  }
  return '单元宽度'
})
const 当前尺寸提示 = computed(() => {
  if (stitchOptions.layout === 'horizontal') {
    return '所有图片会按统一高度缩放后横向拼接。'
  }
  if (stitchOptions.layout === 'vertical') {
    return '所有图片会按统一宽度缩放后纵向拼接。'
  }
  if (stitchOptions.layout === 'subtitle') {
    return '第一张完整保留，后续图片只截取底部指定比例后再纵向拼接。'
  }
  return '宫格会以这个宽度生成单元格，高度由单元比例决定。'
})
const 尺寸滑块最大值 = computed(() => {
  if (!imageList.value.length) {
    return 1600
  }

  const maxSize = stitchOptions.layout === 'horizontal'
    ? Math.max(...imageList.value.map((item) => item.meta.height))
    : Math.max(...imageList.value.map((item) => item.meta.width))
  return Math.max(120, Math.round(maxSize))
})
const 当前背景提示 = computed(() => {
  if (stitchOptions.transparentBackground && exportOptions.format === 'image/jpeg') {
    return 'JPG 不支持透明背景，导出时会自动填充为白色。'
  }
  if (stitchOptions.transparentBackground) {
    return '当前使用透明背景，预览区会以棋盘格显示透明区域。'
  }
  return '当前导出会使用你设置的背景色。'
})
const 列表摘要 = computed(() => {
  if (!imageList.value.length) {
    return ''
  }
  return `共 ${imageList.value.length} 张，当前第 ${Math.max(1, imageList.value.findIndex((item) => item.id === activeImageId.value) + 1)} 张`
})

function formatFileSize(size: number) {
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / 1024 / 1024).toFixed(1)} MB`
}

function formatPixelCount(size: number) {
  if (size < 10000) return `${size.toLocaleString()} px`
  if (size < 1000000) return `${(size / 1000).toFixed(1)} Kpx`
  return `${(size / 1000000).toFixed(2)} Mpx`
}

function buildDefaultName(fileName: string) {
  const normalized = fileName.replace(/\.[^.]+$/, '').trim()
  return normalized ? `${normalized}-stitched` : 'stitched-image'
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

function getGridAspectRatio(aspect: 宫格比例) {
  switch (aspect) {
    case '4:3':
      return 4 / 3
    case '3:4':
      return 3 / 4
    case '16:9':
      return 16 / 9
    default:
      return 1
  }
}

function clamp(value: number, min: number, max: number) {
  return Math.min(Math.max(value, min), max)
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
    const wasEmpty = imageList.value.length === 0
    imageList.value = [...imageList.value, ...nextResources]
    if (wasEmpty) {
      activeImageId.value = nextResources[0].id
      exportOptions.name = buildDefaultName(nextResources[0].meta.name)
    }
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

function triggerFileDialog() {
  fileInputRef.value?.click()
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

function clearImages() {
  revokeImageResources(imageList.value)
  imageList.value = []
  activeImageId.value = null
  exportOptions.name = 'stitched-image'
}

function setActiveImage(id: string) {
  activeImageId.value = id
}

function moveImage(index: number, delta: number) {
  const targetIndex = index + delta
  if (index < 0 || targetIndex < 0 || targetIndex >= imageList.value.length) {
    return
  }

  const nextList = [...imageList.value]
  const [current] = nextList.splice(index, 1)
  nextList.splice(targetIndex, 0, current)
  imageList.value = nextList
}

function removeImage(id: string) {
  const index = imageList.value.findIndex((item) => item.id === id)
  if (index < 0) {
    return
  }

  const current = imageList.value[index]
  revokeImageResource(current)

  const nextList = imageList.value.filter((item) => item.id !== id)
  imageList.value = nextList

  if (!nextList.length) {
    activeImageId.value = null
    exportOptions.name = 'stitched-image'
    return
  }

  if (activeImageId.value === id) {
    activeImageId.value = nextList[Math.min(index, nextList.length - 1)].id
  }
}

function buildLayout(resources: 图片资源[], options: 拼接选项): 拼接布局 | null {
  if (!resources.length) {
    return null
  }

  const gap = Math.max(0, options.gap)
  const padding = Math.max(0, options.padding)
  const targetSize = Math.max(40, options.targetSize)

  if (options.layout === 'horizontal') {
    let currentX = padding
    const items: 绘制项[] = []

    for (const resource of resources) {
      const ratio = resource.meta.width / resource.meta.height
      const drawWidth = targetSize * ratio
      const drawHeight = targetSize
      items.push({
        id: resource.id,
        image: resource.image,
        sourceX: 0,
        sourceY: 0,
        sourceWidth: resource.meta.width,
        sourceHeight: resource.meta.height,
        cellX: currentX,
        cellY: padding,
        cellWidth: drawWidth,
        cellHeight: drawHeight,
        drawX: currentX,
        drawY: padding,
        drawWidth,
        drawHeight,
        needsClip: false,
      })
      currentX += drawWidth + gap
    }

    const width = currentX - gap + padding
    const height = targetSize + padding * 2
    return { width, height, items }
  }

  if (options.layout === 'vertical') {
    let currentY = padding
    const items: 绘制项[] = []

    for (const resource of resources) {
      const ratio = resource.meta.height / resource.meta.width
      const drawWidth = targetSize
      const drawHeight = targetSize * ratio
      items.push({
        id: resource.id,
        image: resource.image,
        sourceX: 0,
        sourceY: 0,
        sourceWidth: resource.meta.width,
        sourceHeight: resource.meta.height,
        cellX: padding,
        cellY: currentY,
        cellWidth: drawWidth,
        cellHeight: drawHeight,
        drawX: padding,
        drawY: currentY,
        drawWidth,
        drawHeight,
        needsClip: false,
      })
      currentY += drawHeight + gap
    }

    const width = targetSize + padding * 2
    const height = currentY - gap + padding
    return { width, height, items }
  }

  if (options.layout === 'subtitle') {
    let currentY = padding
    const items: 绘制项[] = []
    const keepRatio = clamp(options.subtitleCropRatio, 0, 100) / 100

    for (const [index, resource] of resources.entries()) {
      const sourceWidth = resource.meta.width
      const sourceHeight = index === 0
        ? resource.meta.height
        : Math.max(1, Math.round(resource.meta.height * keepRatio))
      const sourceY = index === 0 ? 0 : resource.meta.height - sourceHeight
      const drawWidth = targetSize
      const drawHeight = targetSize * (sourceHeight / sourceWidth)

      items.push({
        id: resource.id,
        image: resource.image,
        sourceX: 0,
        sourceY,
        sourceWidth,
        sourceHeight,
        cellX: padding,
        cellY: currentY,
        cellWidth: drawWidth,
        cellHeight: drawHeight,
        drawX: padding,
        drawY: currentY,
        drawWidth,
        drawHeight,
        needsClip: false,
      })
      currentY += drawHeight + gap
    }

    const width = targetSize + padding * 2
    const height = currentY - gap + padding
    return { width, height, items }
  }

  const columns = clamp(Math.round(options.columns), 1, 8)
  const aspectRatio = getGridAspectRatio(options.gridAspect)
  const cellWidth = targetSize
  const cellHeight = targetSize / aspectRatio
  const rows = Math.ceil(resources.length / columns)
  const width = padding * 2 + columns * cellWidth + Math.max(columns - 1, 0) * gap
  const height = padding * 2 + rows * cellHeight + Math.max(rows - 1, 0) * gap
  const items: 绘制项[] = []

  for (const [index, resource] of resources.entries()) {
    const row = Math.floor(index / columns)
    const column = index % columns
    const cellX = padding + column * (cellWidth + gap)
    const cellY = padding + row * (cellHeight + gap)
    const scale = options.gridFit === 'cover'
      ? Math.max(cellWidth / resource.meta.width, cellHeight / resource.meta.height)
      : Math.min(cellWidth / resource.meta.width, cellHeight / resource.meta.height)
    const drawWidth = resource.meta.width * scale
    const drawHeight = resource.meta.height * scale
    const drawX = cellX + (cellWidth - drawWidth) / 2
    const drawY = cellY + (cellHeight - drawHeight) / 2

    items.push({
      id: resource.id,
      image: resource.image,
      sourceX: 0,
      sourceY: 0,
      sourceWidth: resource.meta.width,
      sourceHeight: resource.meta.height,
      cellX,
      cellY,
      cellWidth,
      cellHeight,
      drawX,
      drawY,
      drawWidth,
      drawHeight,
      needsClip: options.gridFit === 'cover',
    })
  }

  return { width, height, items }
}

const 布局结果 = computed(() => buildLayout(imageList.value, stitchOptions))
const 输出尺寸标签 = computed(() => {
  if (!布局结果.value) {
    return '未生成'
  }
  return `${Math.max(1, Math.round(布局结果.value.width))} × ${Math.max(1, Math.round(布局结果.value.height))}`
})
const 输出像素标签 = computed(() => {
  if (!布局结果.value) {
    return '0 px'
  }
  const pixelCount = Math.max(1, Math.round(布局结果.value.width)) * Math.max(1, Math.round(布局结果.value.height))
  return formatPixelCount(pixelCount)
})

function drawCheckerboard(context: CanvasRenderingContext2D, width: number, height: number) {
  context.fillStyle = '#f2f4f3'
  context.fillRect(0, 0, width, height)

  const blockSize = 18
  for (let row = 0; row * blockSize < height; row += 1) {
    for (let col = 0; col * blockSize < width; col += 1) {
      const isEven = (row + col) % 2 === 0
      context.fillStyle = isEven ? 'rgba(255, 255, 255, 0.92)' : 'rgba(214, 223, 218, 0.7)'
      context.fillRect(col * blockSize, row * blockSize, blockSize, blockSize)
    }
  }
}

function fillOutputBackground(
  context: CanvasRenderingContext2D,
  width: number,
  height: number,
  options: 拼接选项,
  format?: 导出格式,
) {
  if (options.transparentBackground && format !== 'image/jpeg') {
    return
  }

  context.fillStyle = options.transparentBackground && format === 'image/jpeg'
    ? '#ffffff'
    : options.backgroundColor
  context.fillRect(0, 0, width, height)
}

function drawLayout(
  context: CanvasRenderingContext2D,
  layout: 拼接布局,
  options: 拼接选项,
  drawOptions?: {
    format?: 导出格式
    scale?: number
    offsetX?: number
    offsetY?: number
  },
) {
  const scale = drawOptions?.scale ?? 1
  const offsetX = drawOptions?.offsetX ?? 0
  const offsetY = drawOptions?.offsetY ?? 0

  context.save()
  context.translate(offsetX, offsetY)
  context.scale(scale, scale)
  fillOutputBackground(context, layout.width, layout.height, options, drawOptions?.format)

  for (const item of layout.items) {
    context.save()
    if (item.needsClip) {
      context.beginPath()
      context.rect(item.cellX, item.cellY, item.cellWidth, item.cellHeight)
      context.clip()
    }
    context.imageSmoothingEnabled = true
    context.imageSmoothingQuality = 'high'
    context.drawImage(
      item.image,
      item.sourceX,
      item.sourceY,
      item.sourceWidth,
      item.sourceHeight,
      item.drawX,
      item.drawY,
      item.drawWidth,
      item.drawHeight,
    )
    context.restore()
  }

  context.restore()
}

let resizeObserver: ResizeObserver | null = null
let renderFrame = 0

function schedulePreviewRender() {
  if (renderFrame) {
    window.cancelAnimationFrame(renderFrame)
  }
  renderFrame = window.requestAnimationFrame(() => {
    renderFrame = 0
    renderPreview()
  })
}

function renderPreview() {
  const stage = previewStageRef.value
  const canvas = previewCanvasRef.value
  if (!stage || !canvas) {
    return
  }

  const stageWidth = Math.max(1, stage.clientWidth)
  const stageHeight = Math.max(1, stage.clientHeight)
  const dpr = window.devicePixelRatio || 1

  canvas.width = Math.round(stageWidth * dpr)
  canvas.height = Math.round(stageHeight * dpr)

  const context = canvas.getContext('2d')
  if (!context) {
    return
  }

  context.setTransform(1, 0, 0, 1, 0, 0)
  context.clearRect(0, 0, canvas.width, canvas.height)
  context.scale(dpr, dpr)
  drawCheckerboard(context, stageWidth, stageHeight)

  const layout = 布局结果.value
  if (!layout) {
    return
  }

  const maxWidth = Math.max(1, stageWidth - 32)
  const maxHeight = Math.max(1, stageHeight - 32)
  const scale = Math.min(maxWidth / layout.width, maxHeight / layout.height)
  const drawWidth = layout.width * scale
  const drawHeight = layout.height * scale
  const offsetX = (stageWidth - drawWidth) / 2
  const offsetY = (stageHeight - drawHeight) / 2

  if (!stitchOptions.transparentBackground) {
    context.save()
    context.shadowColor = 'rgba(15, 23, 42, 0.14)'
    context.shadowBlur = 22
    context.fillStyle = 'rgba(255, 255, 255, 0.8)'
    context.fillRect(offsetX, offsetY, drawWidth, drawHeight)
    context.restore()
  }

  drawLayout(context, layout, stitchOptions, { scale, offsetX, offsetY })

  context.save()
  context.strokeStyle = 'rgba(15, 23, 42, 0.08)'
  context.lineWidth = 1
  context.strokeRect(offsetX + 0.5, offsetY + 0.5, Math.max(0, drawWidth - 1), Math.max(0, drawHeight - 1))
  context.restore()
}

function downloadBlob(blob: Blob, fileName: string) {
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = fileName
  anchor.click()
  window.setTimeout(() => URL.revokeObjectURL(url), 1000)
}

async function exportStitchedImage() {
  const layout = 布局结果.value
  if (!layout) {
    ElMessage.warning('请先选择图片')
    return
  }

  isExporting.value = true
  try {
    const canvas = document.createElement('canvas')
    canvas.width = Math.max(1, Math.round(layout.width))
    canvas.height = Math.max(1, Math.round(layout.height))
    const context = canvas.getContext('2d')
    if (!context) {
      throw new Error('canvas 上下文创建失败')
    }

    drawLayout(context, layout, stitchOptions, { format: exportOptions.format })

    const quality = exportOptions.format === 'image/png' ? undefined : exportOptions.quality / 100
    const blob = await new Promise<Blob | null>((resolve) => {
      canvas.toBlob(resolve, exportOptions.format, quality)
    })

    if (!blob) {
      throw new Error('导出结果为空')
    }

    const fileName = `${(exportOptions.name || 'stitched-image').trim() || 'stitched-image'}.${输出扩展名.value}`
    downloadBlob(blob, fileName)
    ElMessage.success('拼接图片已开始下载')
  } catch {
    ElMessage.error('拼接导出失败，请稍后重试')
  } finally {
    isExporting.value = false
  }
}

watch(
  [imageList, () => stitchOptions.layout, 尺寸滑块最大值],
  () => {
    if (stitchOptions.targetSize > 尺寸滑块最大值.value) {
      stitchOptions.targetSize = 尺寸滑块最大值.value
    }
  },
  { deep: true, immediate: true },
)

watch(
  [
    imageList,
    () => stitchOptions.layout,
    () => stitchOptions.targetSize,
    () => stitchOptions.columns,
    () => stitchOptions.gap,
    () => stitchOptions.padding,
    () => stitchOptions.subtitleCropRatio,
    () => stitchOptions.gridAspect,
    () => stitchOptions.gridFit,
    () => stitchOptions.transparentBackground,
    () => stitchOptions.backgroundColor,
  ],
  () => {
    schedulePreviewRender()
  },
  { deep: true },
)

watch(
  imageList,
  (nextList) => {
    if (!nextList.length) {
      activeImageId.value = null
      return
    }

    if (!nextList.some((item) => item.id === activeImageId.value)) {
      activeImageId.value = nextList[0].id
    }
  },
  { deep: true },
)

onMounted(() => {
  if (typeof window.ResizeObserver !== 'undefined' && previewStageRef.value) {
    resizeObserver = new window.ResizeObserver(() => {
      schedulePreviewRender()
    })
    resizeObserver.observe(previewStageRef.value)
  }
  schedulePreviewRender()
})

async function handlePreviewCardToggle(expanded: boolean) {
  if (!expanded) {
    return
  }
  await nextTick()
  schedulePreviewRender()
}

onBeforeUnmount(() => {
  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
  }
  if (renderFrame) {
    window.cancelAnimationFrame(renderFrame)
    renderFrame = 0
  }
  revokeImageResources(imageList.value)
})
</script>

<template>
  <div class="stitch-workbench">
    <div class="stitch-grid">
      <aside class="stitch-sidebar">
        <WorkbenchSectionCard class="stitch-card" shadow="never" title="选择图片" :icon="Picture">
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
            <p>支持多张图片本地拼接，不会上传到服务器。</p>
          </div>

          <div class="upload-actions">
            <ElButton type="primary" @click="triggerFileDialog">继续添加</ElButton>
            <ElButton :disabled="!是否有图片" @click="clearImages">
              <Delete />
              清空全部
            </ElButton>
          </div>

          <div v-if="当前图片" class="meta-stack">
            <div class="meta-row">
              <span>当前文件</span>
              <strong>{{ 当前图片.meta.name }}</strong>
            </div>
            <div class="meta-row meta-row--inline">
              <span>当前尺寸</span>
              <strong>{{ 当前图片.meta.width }} × {{ 当前图片.meta.height }}</strong>
            </div>
            <div class="meta-row meta-row--inline">
              <span>当前体积</span>
              <strong>{{ formatFileSize(当前图片.meta.size) }}</strong>
            </div>
          </div>
        </WorkbenchSectionCard>

        <WorkbenchSectionCard class="stitch-card" shadow="never" title="拼接设置" :icon="Grid" :disabled="!是否有图片">
          <ElRadioGroup v-model="stitchOptions.layout" class="layout-group" size="small" :disabled="!是否有图片">
            <ElRadioButton v-for="item in 拼接模式列表" :key="item.value" :value="item.value">
              {{ item.label }}
            </ElRadioButton>
          </ElRadioGroup>

          <label class="form-field">
            <span>{{ 当前尺寸标签 }} {{ stitchOptions.targetSize }} px</span>
            <ElSlider
              v-model="stitchOptions.targetSize"
              :disabled="!是否有图片"
              :min="120"
              :max="尺寸滑块最大值"
              :step="10"
            />
            <small>{{ 当前尺寸提示 }} 当前可选上限会按已上传图片的最大尺寸自动调整。</small>
          </label>

          <div v-if="stitchOptions.layout === 'grid'" class="grid-options">
            <label class="form-field">
              <span>每行列数</span>
              <ElInputNumber v-model="stitchOptions.columns" :disabled="!是否有图片" :min="1" :max="8" />
            </label>

            <label class="form-field">
              <span>单元比例</span>
              <ElSelect v-model="stitchOptions.gridAspect" :disabled="!是否有图片">
                <ElOption v-for="item in 宫格比例列表" :key="item.value" :label="item.label" :value="item.value" />
              </ElSelect>
            </label>

            <label class="form-field">
              <span>填充方式</span>
              <ElSelect v-model="stitchOptions.gridFit" :disabled="!是否有图片">
                <ElOption
                  v-for="item in 宫格填充列表"
                  :key="item.value"
                  :label="`${item.label} · ${item.描述}`"
                  :value="item.value"
                />
              </ElSelect>
            </label>
          </div>

          <label v-if="stitchOptions.layout === 'subtitle'" class="form-field">
            <span>后续图片保留底部 {{ stitchOptions.subtitleCropRatio }}%</span>
            <ElSlider v-model="stitchOptions.subtitleCropRatio" :disabled="!是否有图片" :min="0" :max="100" />
            <small>首张图片始终完整保留，第二张开始只取底部这部分高度。</small>
          </label>

          <label class="form-field">
            <span>图片间距 {{ stitchOptions.gap }} px</span>
            <ElSlider v-model="stitchOptions.gap" :disabled="!是否有图片" :min="0" :max="120" />
          </label>

          <label class="form-field">
            <span>画布边框 {{ stitchOptions.padding }} px</span>
            <ElSlider v-model="stitchOptions.padding" :disabled="!是否有图片" :min="0" :max="180" />
          </label>

          <div class="background-row">
            <span>透明背景</span>
            <ElSwitch v-model="stitchOptions.transparentBackground" :disabled="!是否有图片" />
          </div>

          <label class="form-field" :class="{ 'is-muted': stitchOptions.transparentBackground }">
            <span>背景颜色</span>
            <ElColorPicker
              v-model="stitchOptions.backgroundColor"
              :disabled="!是否有图片 || stitchOptions.transparentBackground"
              :predefine="背景预设色"
            />
            <small>{{ 当前背景提示 }}</small>
          </label>
        </WorkbenchSectionCard>

        <WorkbenchSectionCard class="stitch-card" shadow="never" title="导出" :icon="Download" :disabled="!是否有图片">
          <label class="form-field">
            <span>文件名</span>
            <input v-model="exportOptions.name" class="export-input" type="text" :disabled="!是否有图片">
          </label>

          <label class="form-field">
            <span>格式</span>
            <ElSelect v-model="exportOptions.format" :disabled="!是否有图片">
              <ElOption
                v-for="item in 导出格式列表"
                :key="item.value"
                :label="`${item.label} · ${item.描述}`"
                :value="item.value"
              />
            </ElSelect>
          </label>

          <label v-if="是否展示质量" class="form-field">
            <span>质量 {{ exportOptions.quality }}%</span>
            <ElSlider v-model="exportOptions.quality" :disabled="!是否有图片" :min="60" :max="100" />
          </label>

          <div class="meta-stack meta-stack--two-column">
            <div class="meta-row meta-row--inline">
              <span>输出尺寸</span>
              <strong>{{ 输出尺寸标签 }}</strong>
            </div>
            <div class="meta-row meta-row--inline">
              <span>像素规模</span>
              <strong>{{ 输出像素标签 }}</strong>
            </div>
          </div>

          <ElButton
            type="primary"
            size="large"
            :loading="isExporting"
            :disabled="!是否有图片"
            @click="exportStitchedImage"
          >
            <Download />
            下载拼接结果
          </ElButton>
        </WorkbenchSectionCard>
      </aside>

      <section class="stitch-main">
        <WorkbenchSectionCard class="stitch-card preview-card" shadow="never" title="预览画布" @toggle="handlePreviewCardToggle">
          <template #actions>
            <div class="preview-tags">
              <ElTag round effect="plain">纯前端</ElTag>
              <ElTag round effect="plain">本地拼接</ElTag>
            </div>
          </template>

          <div
            ref="previewStageRef"
            class="preview-stage"
            :class="{ 'is-empty': !是否有图片, 'is-dragover': isDragOver }"
            @dragenter.prevent="isDragOver = true"
            @dragover.prevent="isDragOver = true"
            @dragleave.prevent="isDragOver = false"
            @drop="handleDrop"
          >
            <canvas ref="previewCanvasRef" class="preview-canvas" />

            <div v-if="!是否有图片" class="preview-empty">
              <ElEmpty description="先选择多张图片开始拼接" />
            </div>
          </div>

          <p class="preview-hint">
            预览会根据当前窗口缩放显示，导出时会按上面的真实输出尺寸生成完整图片。
          </p>
        </WorkbenchSectionCard>

        <WorkbenchSectionCard class="stitch-card list-card" shadow="never" title="图片顺序" :subtitle="列表摘要">
          <div v-if="是否有图片" class="image-list">
            <div
              v-for="(item, index) in imageList"
              :key="item.id"
              class="image-row"
              :class="{ 'is-active': item.id === activeImageId }"
              role="button"
              tabindex="0"
              @click="setActiveImage(item.id)"
              @keydown.enter.prevent="setActiveImage(item.id)"
              @keydown.space.prevent="setActiveImage(item.id)"
            >
              <span class="image-row__index">{{ index + 1 }}</span>
              <img class="image-row__thumb" :src="item.previewUrl" :alt="item.meta.name">

              <span class="image-row__content">
                <strong>{{ item.meta.name }}</strong>
                <small>{{ item.meta.width }} × {{ item.meta.height }}</small>
                <small>{{ formatFileSize(item.meta.size) }}</small>
              </span>

              <span class="image-row__actions">
                <ElButton circle :disabled="index === 0" @click.stop="moveImage(index, -1)">
                  <ArrowUp />
                </ElButton>
                <ElButton circle :disabled="index === imageList.length - 1" @click.stop="moveImage(index, 1)">
                  <ArrowDown />
                </ElButton>
                <ElButton circle @click.stop="removeImage(item.id)">
                  <Delete />
                </ElButton>
              </span>
            </div>
          </div>

          <div v-else class="list-empty">
            <ElEmpty description="图片列表为空" />
          </div>
        </WorkbenchSectionCard>
      </section>
    </div>
  </div>
</template>

<style scoped>
.stitch-workbench {
  --stitch-surface: color-mix(in srgb, var(--bg-card) 90%, white);
  --stitch-surface-soft: color-mix(in srgb, var(--el-color-primary) 4%, var(--bg-card));
  --stitch-surface-strong: color-mix(in srgb, var(--el-color-primary) 8%, var(--bg-card));
  --stitch-border-soft: color-mix(in srgb, var(--el-color-primary) 10%, var(--border-color));
  --stitch-border-strong: color-mix(in srgb, var(--el-color-primary) 22%, var(--border-color));
  --stitch-title: var(--text-primary);
  --stitch-text: var(--text-secondary);
  --stitch-text-soft: color-mix(in srgb, var(--text-secondary) 88%, var(--el-color-primary));
  --stitch-canvas-bg: color-mix(in srgb, var(--bg-primary) 94%, var(--el-color-primary) 6%);
  display: grid;
}

.stitch-grid {
  display: grid;
  grid-template-columns: 340px minmax(0, 1fr);
  gap: 18px;
  align-items: start;
}

.stitch-sidebar,
.stitch-main {
  display: grid;
  gap: 16px;
  min-width: 0;
}

.stitch-card {
  border-radius: 24px;
  border-color: var(--stitch-border-soft);
  background: color-mix(in srgb, var(--stitch-surface) 92%, transparent);
  box-shadow: 0 12px 30px rgba(15, 23, 42, 0.05);
  backdrop-filter: blur(14px);
}

.stitch-card :deep(.el-card__header) {
  border-bottom-color: var(--stitch-border-soft);
  padding: 8px 20px 6px;
}

.stitch-card :deep(.el-card__body) {
  padding: 18px 20px 20px;
}

.file-input {
  display: none;
}

.upload-dropzone {
  min-height: 196px;
  padding: 20px;
  border: 1.5px dashed var(--stitch-border-strong);
  border-radius: 22px;
  background:
    radial-gradient(circle at top, rgb(var(--el-color-primary-rgb) / 0.1), transparent 54%),
    var(--stitch-surface-soft);
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
  color: var(--stitch-title);
  font-size: 16px;
}

.upload-dropzone p {
  color: var(--stitch-text);
  line-height: 1.7;
}

.upload-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 14px;
}

.layout-group {
  display: flex;
  flex-wrap: wrap;
  margin-bottom: 16px;
}

.grid-options,
.meta-stack {
  display: grid;
  gap: 12px;
}

.meta-stack {
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
  background: var(--stitch-surface-soft);
}

.meta-row--inline {
  grid-template-columns: auto 1fr;
  align-items: center;
  gap: 10px;
}

.meta-row span {
  color: var(--stitch-text);
  font-size: 13px;
}

.meta-row strong {
  color: var(--stitch-title);
  line-height: 1.6;
  word-break: break-word;
}

.form-field {
  display: grid;
  gap: 8px;
  margin-bottom: 14px;
}

.form-field > span {
  color: var(--stitch-text-soft);
  font-size: 13px;
  font-weight: 600;
}

.form-field small {
  color: var(--stitch-text);
  line-height: 1.6;
}

.form-field.is-muted {
  opacity: 0.72;
}

.background-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin: 8px 0 14px;
  color: var(--stitch-text-soft);
  font-size: 13px;
  font-weight: 600;
}

.export-input {
  min-height: 42px;
  padding: 0 14px;
  border: 1px solid var(--stitch-border-soft);
  border-radius: 14px;
  background: color-mix(in srgb, var(--stitch-surface-soft) 88%, white);
  color: var(--stitch-title);
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
.list-card {
  min-width: 0;
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
  border: 1px solid var(--stitch-border-soft);
  background: var(--stitch-canvas-bg);
}

.preview-stage.is-empty {
  display: grid;
  place-items: center;
}

.preview-stage.is-dragover {
  box-shadow: inset 0 0 0 1.5px rgb(var(--el-color-primary-rgb) / 0.26);
}

.preview-canvas {
  display: block;
  width: 100%;
  height: 100%;
}

.preview-empty {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  pointer-events: none;
}

.preview-hint {
  margin-top: 14px;
  color: var(--stitch-text);
  line-height: 1.8;
}

.image-list {
  display: grid;
  gap: 10px;
}

.image-row {
  width: 100%;
  padding: 10px;
  border: 1px solid color-mix(in srgb, var(--el-color-primary) 12%, var(--border-color));
  border-radius: 18px;
  background: var(--bg-card);
  display: grid;
  grid-template-columns: 34px 72px minmax(0, 1fr) auto;
  align-items: center;
  gap: 12px;
  text-align: left;
  cursor: pointer;
  transition:
    border-color 0.18s ease,
    background-color 0.18s ease,
    box-shadow 0.18s ease,
    transform 0.18s ease;
}

.image-row:hover {
  transform: translateY(-1px);
  border-color: color-mix(in srgb, var(--el-color-primary) 30%, transparent);
  box-shadow: 0 8px 18px rgb(var(--el-color-primary-rgb) / 0.08);
}

.image-row.is-active {
  border-color: color-mix(in srgb, var(--el-color-primary) 36%, transparent);
  background: rgb(var(--el-color-primary-rgb) / 0.08);
}

.image-row__index {
  width: 34px;
  height: 34px;
  border-radius: 12px;
  background: rgb(var(--el-color-primary-rgb) / 0.1);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--el-color-primary);
  font-size: 13px;
  font-weight: 700;
}

.image-row__thumb {
  width: 72px;
  height: 72px;
  border-radius: 16px;
  object-fit: cover;
  background: rgba(255, 255, 255, 0.72);
}

.image-row__content {
  display: grid;
  gap: 4px;
  min-width: 0;
}

.image-row__content strong {
  color: var(--stitch-title);
  line-height: 1.5;
  word-break: break-word;
}

.image-row__content small {
  color: var(--stitch-text);
  line-height: 1.5;
}

.image-row__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.list-empty {
  min-height: 220px;
  display: grid;
  place-items: center;
}

.dark .stitch-card {
  --stitch-surface: color-mix(in srgb, var(--bg-card) 92%, transparent);
  --stitch-surface-soft: color-mix(in srgb, var(--el-color-primary-light-5) 8%, var(--bg-card));
  --stitch-surface-strong: color-mix(in srgb, var(--el-color-primary-light-5) 12%, var(--bg-card));
  --stitch-border-soft: color-mix(in srgb, var(--el-color-primary-light-5) 10%, var(--border-color));
  --stitch-border-strong: color-mix(in srgb, var(--el-color-primary-light-5) 18%, var(--border-color));
  --stitch-title: var(--text-primary);
  --stitch-text: var(--text-secondary);
  --stitch-text-soft: color-mix(in srgb, var(--text-secondary) 86%, var(--el-color-primary-light-5));
  --stitch-canvas-bg: color-mix(in srgb, var(--bg-primary) 88%, var(--el-color-primary-light-5) 12%);
  background:
    linear-gradient(145deg, color-mix(in srgb, var(--el-color-primary-light-5) 10%, transparent), rgba(16, 24, 22, 0.92)),
    var(--stitch-surface);
  border-color: var(--stitch-border-soft);
  box-shadow: 0 18px 40px rgba(2, 6, 23, 0.26);
}

.dark .meta-row,
.dark .upload-dropzone,
.dark .export-input,
.dark .image-row {
  background: var(--stitch-surface-soft);
  border-color: var(--stitch-border-soft);
}

.dark .upload-dropzone:hover,
.dark .upload-dropzone.is-dragover {
  background: color-mix(in srgb, var(--el-color-primary-light-5) 12%, var(--bg-card));
}

@media (max-width: 1280px) {
  .stitch-grid {
    grid-template-columns: 1fr;
  }

  .preview-stage {
    min-height: 520px;
  }
}

@media (max-width: 767px) {
  .stitch-card :deep(.el-card__header),
  .stitch-card :deep(.el-card__body) {
    padding-left: 16px;
    padding-right: 16px;
  }

  .preview-stage {
    min-height: 360px;
  }

  .meta-stack--two-column {
    grid-template-columns: 1fr;
  }

  .image-row {
    grid-template-columns: 30px 64px minmax(0, 1fr);
  }

  .image-row__actions {
    grid-column: 1 / -1;
    justify-content: flex-end;
  }
}
</style>
