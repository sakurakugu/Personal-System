<script setup lang="ts">
/* global Blob, CanvasRenderingContext2D, DragEvent, Event, File, HTMLCanvasElement, HTMLDivElement, HTMLImageElement, HTMLInputElement, Image, PointerEvent, ResizeObserver, URL */
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, shallowRef, watch } from 'vue'
import { ElButton, ElEmpty, ElIcon, ElMessage, ElRadioGroup, ElRadioButton, ElSelect, ElOption, ElSlider, ElTag } from 'element-plus'
import { UploadFilled, RefreshLeft, RefreshRight, Download, Delete, Crop, Refresh, Switch, MagicStick, Picture, View } from '@element-plus/icons-vue'
import WorkbenchSectionCard from './工作台卡片.vue'
import { 获取图片预览实例, type 图片预览实例 } from '../lib/fancybox'

type AspectPreset = 'free' | '1:1' | '4:3' | '16:9' | '3:4'
type ResizeHandle = 'nw' | 'ne' | 'sw' | 'se'
type DragMode = 'move' | ResizeHandle
type ExportFormat = 'image/png' | 'image/jpeg' | 'image/webp'

type CropRect = {
  x: number
  y: number
  width: number
  height: number
}

type ImageMeta = {
  name: string
  size: number
  type: string
  width: number
  height: number
}

type DisplayRect = {
  x: number
  y: number
  width: number
  height: number
}

type Point = {
  x: number
  y: number
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
const previewStageRef = ref<HTMLDivElement | null>(null)
const previewCanvasRef = ref<HTMLCanvasElement | null>(null)

const baseImage = shallowRef<HTMLImageElement | null>(null)
const imageMeta = ref<ImageMeta | null>(null)
const cropRect = ref<CropRect | null>(null)
const displayRect = ref<DisplayRect | null>(null)
const isDragOver = ref(false)
const isExporting = ref(false)

const imageTransform = reactive({
  rotation: 0,
  flipX: false,
  flipY: false,
  brightness: 100,
  contrast: 100,
  saturation: 100,
  grayscale: 0,
  blur: 0,
})

const exportOptions = reactive({
  format: 'image/png' as ExportFormat,
  quality: 92,
  name: 'edited-image',
})

const aspectPreset = ref<AspectPreset>('free')

const aspectOptions: Array<{ label: string; value: AspectPreset }> = [
  { label: '自由', value: 'free' },
  { label: '1:1', value: '1:1' },
  { label: '4:3', value: '4:3' },
  { label: '16:9', value: '16:9' },
  { label: '3:4', value: '3:4' },
]

const exportFormatOptions: Array<{ label: string; value: ExportFormat }> = [
  { label: 'PNG', value: 'image/png' },
  { label: 'JPG', value: 'image/jpeg' },
  { label: 'WEBP', value: 'image/webp' },
]

const handleCursorMap: Record<ResizeHandle, string> = {
  nw: 'nwse-resize',
  ne: 'nesw-resize',
  sw: 'nesw-resize',
  se: 'nwse-resize',
}

const currentObjectUrl = ref<string | null>(null)
const normalizedRotation = computed(() => ((imageTransform.rotation % 360) + 360) % 360)
const hasImage = computed(() => baseImage.value !== null && imageMeta.value !== null)
const transformedSize = computed(() => {
  const meta = imageMeta.value
  if (!meta) return null
  if (normalizedRotation.value % 180 === 0) {
    return { width: meta.width, height: meta.height }
  }
  return { width: meta.height, height: meta.width }
})
const sourceSizeLabel = computed(() => {
  if (!imageMeta.value) return '未选择图片'
  return `${imageMeta.value.width} × ${imageMeta.value.height}`
})
const outputSizeLabel = computed(() => {
  if (!cropRect.value) return '未生成'
  return `${Math.max(1, Math.round(cropRect.value.width))} × ${Math.max(1, Math.round(cropRect.value.height))}`
})
const fileSizeLabel = computed(() => {
  if (!imageMeta.value) return '0 B'
  return formatFileSize(imageMeta.value.size)
})
const exportExtension = computed(() => {
  switch (exportOptions.format) {
    case 'image/jpeg':
      return 'jpg'
    case 'image/webp':
      return 'webp'
    default:
      return 'png'
  }
})
const shouldShowQuality = computed(() => exportOptions.format !== 'image/png')
const cropStyle = computed<Record<string, string> | null>(() => {
  const crop = cropRect.value
  const frame = displayRect.value
  const size = transformedSize.value
  if (!crop || !frame || !size || !frame.width || !frame.height) return null

  return {
    left: `${frame.x + crop.x / size.width * frame.width}px`,
    top: `${frame.y + crop.y / size.height * frame.height}px`,
    width: `${crop.width / size.width * frame.width}px`,
    height: `${crop.height / size.height * frame.height}px`,
  }
})
const frameStyle = computed<Record<string, string> | null>(() => {
  const frame = displayRect.value
  if (!frame) return null
  return {
    left: `${frame.x}px`,
    top: `${frame.y}px`,
    width: `${frame.width}px`,
    height: `${frame.height}px`,
  }
})

let resizeObserver: ResizeObserver | null = null
let renderFrame = 0
let Fancybox实例: 图片预览实例 | null = null
let 编辑结果预览Url: string | null = null
let dragSession:
  | {
      mode: DragMode
      startPoint: Point
      startCrop: CropRect
    }
  | null = null

function formatFileSize(size: number) {
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / 1024 / 1024).toFixed(1)} MB`
}

function getAspectRatio(preset: AspectPreset) {
  switch (preset) {
    case '1:1':
      return 1
    case '4:3':
      return 4 / 3
    case '16:9':
      return 16 / 9
    case '3:4':
      return 3 / 4
    default:
      return null
  }
}

function getFilterString() {
  return [
    `brightness(${imageTransform.brightness}%)`,
    `contrast(${imageTransform.contrast}%)`,
    `saturate(${imageTransform.saturation}%)`,
    `grayscale(${imageTransform.grayscale}%)`,
    `blur(${imageTransform.blur}px)`,
  ].join(' ')
}

function cloneCrop(crop: CropRect): CropRect {
  return {
    x: crop.x,
    y: crop.y,
    width: crop.width,
    height: crop.height,
  }
}

function clamp(value: number, min: number, max: number) {
  return Math.min(Math.max(value, min), max)
}

function clampCropToBounds(input: CropRect, size: { width: number; height: number }) {
  const nextWidth = clamp(input.width, 1, size.width)
  const nextHeight = clamp(input.height, 1, size.height)
  const nextX = clamp(input.x, 0, size.width - nextWidth)
  const nextY = clamp(input.y, 0, size.height - nextHeight)
  return {
    x: nextX,
    y: nextY,
    width: nextWidth,
    height: nextHeight,
  }
}

function createMaxCrop(size: { width: number; height: number }, preset: AspectPreset) {
  const ratio = getAspectRatio(preset)
  if (!ratio) {
    return {
      x: 0,
      y: 0,
      width: size.width,
      height: size.height,
    }
  }

  let width = size.width
  let height = width / ratio
  if (height > size.height) {
    height = size.height
    width = height * ratio
  }

  return {
    x: (size.width - width) / 2,
    y: (size.height - height) / 2,
    width,
    height,
  }
}

function schedulePreviewRender() {
  if (renderFrame) {
    window.cancelAnimationFrame(renderFrame)
  }
  renderFrame = window.requestAnimationFrame(() => {
    renderFrame = 0
    renderPreview()
  })
}

async function 获取共享图片预览实例() {
  if (Fancybox实例) {
    return Fancybox实例
  }

  Fancybox实例 = await 获取图片预览实例()
  return Fancybox实例
}

function 关闭图片预览() {
  Fancybox实例?.close()
}

function 释放编辑结果预览链接() {
  if (!编辑结果预览Url) {
    return
  }

  URL.revokeObjectURL(编辑结果预览Url)
  编辑结果预览Url = null
}

function revokeCurrentObjectUrl() {
  if (!currentObjectUrl.value) return
  URL.revokeObjectURL(currentObjectUrl.value)
  currentObjectUrl.value = null
}

function resetEditorOptions() {
  aspectPreset.value = 'free'
  imageTransform.rotation = 0
  imageTransform.flipX = false
  imageTransform.flipY = false
  imageTransform.brightness = 100
  imageTransform.contrast = 100
  imageTransform.saturation = 100
  imageTransform.grayscale = 0
  imageTransform.blur = 0
}

function clearEditor() {
  关闭图片预览()
  释放编辑结果预览链接()
  revokeCurrentObjectUrl()
  baseImage.value = null
  imageMeta.value = null
  cropRect.value = null
  displayRect.value = null
  exportOptions.name = 'edited-image'
  resetEditorOptions()
  schedulePreviewRender()
}

async function loadImageFile(file: File) {
  if (!file.type.startsWith('image/')) {
    ElMessage.warning('请选择图片文件')
    return
  }

  关闭图片预览()
  释放编辑结果预览链接()
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
  baseImage.value = image
  imageMeta.value = {
    name: file.name,
    size: file.size,
    type: file.type,
    width: image.naturalWidth,
    height: image.naturalHeight,
  }
  exportOptions.name = buildDefaultExportName(file.name)
  resetEditorOptions()
  initializeCrop()
  schedulePreviewRender()
}

function buildDefaultExportName(fileName: string) {
  const normalized = fileName.replace(/\.[^.]+$/, '').trim()
  return normalized ? `${normalized}-edited` : 'edited-image'
}

function initializeCrop() {
  const size = transformedSize.value
  if (!size) return
  cropRect.value = createMaxCrop(size, aspectPreset.value)
}

function triggerFileDialog() {
  fileInputRef.value?.click()
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

function buildTransformedCanvas() {
  if (!baseImage.value || !transformedSize.value) return null
  const canvas = document.createElement('canvas')
  canvas.width = transformedSize.value.width
  canvas.height = transformedSize.value.height
  const context = canvas.getContext('2d')
  if (!context) return null

  context.imageSmoothingEnabled = true
  context.imageSmoothingQuality = 'high'
  context.filter = getFilterString()
  context.translate(canvas.width / 2, canvas.height / 2)
  context.scale(imageTransform.flipX ? -1 : 1, imageTransform.flipY ? -1 : 1)
  context.rotate(normalizedRotation.value * Math.PI / 180)
  context.drawImage(baseImage.value, -baseImage.value.naturalWidth / 2, -baseImage.value.naturalHeight / 2)
  return canvas
}

function drawCheckerboard(context: CanvasRenderingContext2D, width: number, height: number) {
  context.fillStyle = '#f3f6f4'
  context.fillRect(0, 0, width, height)

  const blockSize = 20
  for (let row = 0; row * blockSize < height; row += 1) {
    for (let col = 0; col * blockSize < width; col += 1) {
      const isEven = (row + col) % 2 === 0
      context.fillStyle = isEven ? 'rgba(255, 255, 255, 0.88)' : 'rgba(214, 226, 218, 0.5)'
      context.fillRect(col * blockSize, row * blockSize, blockSize, blockSize)
    }
  }
}

function renderPreview() {
  const canvas = previewCanvasRef.value
  const stage = previewStageRef.value
  if (!canvas || !stage) return

  const stageWidth = Math.max(1, stage.clientWidth)
  const stageHeight = Math.max(1, stage.clientHeight)
  const dpr = window.devicePixelRatio || 1

  canvas.width = Math.round(stageWidth * dpr)
  canvas.height = Math.round(stageHeight * dpr)

  const context = canvas.getContext('2d')
  if (!context) return

  context.setTransform(1, 0, 0, 1, 0, 0)
  context.clearRect(0, 0, canvas.width, canvas.height)
  context.scale(dpr, dpr)

  drawCheckerboard(context, stageWidth, stageHeight)

  const transformedCanvas = buildTransformedCanvas()
  if (!transformedCanvas) {
    displayRect.value = null
    return
  }

  const fit = Math.min(stageWidth / transformedCanvas.width, stageHeight / transformedCanvas.height)
  const drawWidth = transformedCanvas.width * fit
  const drawHeight = transformedCanvas.height * fit
  const offsetX = (stageWidth - drawWidth) / 2
  const offsetY = (stageHeight - drawHeight) / 2

  context.drawImage(transformedCanvas, offsetX, offsetY, drawWidth, drawHeight)
  displayRect.value = {
    x: offsetX,
    y: offsetY,
    width: drawWidth,
    height: drawHeight,
  }
}

function resetCrop() {
  const size = transformedSize.value
  if (!size) return
  cropRect.value = {
    x: 0,
    y: 0,
    width: size.width,
    height: size.height,
  }
}

function resetAdjustments() {
  imageTransform.brightness = 100
  imageTransform.contrast = 100
  imageTransform.saturation = 100
  imageTransform.grayscale = 0
  imageTransform.blur = 0
}

function rotate(delta: number) {
  const sizeBefore = transformedSize.value
  const cropBefore = cropRect.value ? cloneCrop(cropRect.value) : null

  imageTransform.rotation = ((imageTransform.rotation + delta) % 360 + 360) % 360

  const sizeAfter = transformedSize.value
  if (!sizeAfter) return

  if (!sizeBefore || !cropBefore) {
    cropRect.value = createMaxCrop(sizeAfter, aspectPreset.value)
    return
  }

  const nextCrop = clampCropToBounds({
    x: cropBefore.x / sizeBefore.width * sizeAfter.width,
    y: cropBefore.y / sizeBefore.height * sizeAfter.height,
    width: cropBefore.width / sizeBefore.width * sizeAfter.width,
    height: cropBefore.height / sizeBefore.height * sizeAfter.height,
  }, sizeAfter)

  cropRect.value = nextCrop
}

function flipHorizontal() {
  imageTransform.flipX = !imageTransform.flipX
}

function flipVertical() {
  imageTransform.flipY = !imageTransform.flipY
}

function getPointFromClient(clientX: number, clientY: number, clampToFrame = false) {
  const stage = previewStageRef.value
  const frame = displayRect.value
  const size = transformedSize.value
  if (!stage || !frame || !size || frame.width <= 0 || frame.height <= 0) return null

  const stageRect = stage.getBoundingClientRect()
  const localX = clientX - stageRect.left - frame.x
  const localY = clientY - stageRect.top - frame.y

  if (!clampToFrame && (localX < 0 || localY < 0 || localX > frame.width || localY > frame.height)) {
    return null
  }

  const safeX = clamp(localX, 0, frame.width)
  const safeY = clamp(localY, 0, frame.height)

  return {
    x: safeX / frame.width * size.width,
    y: safeY / frame.height * size.height,
  }
}

function getMinimumCropSize(ratio: number | null) {
  if (!ratio) {
    return { width: 40, height: 40 }
  }
  if (ratio >= 1) {
    return { width: 80, height: 80 / ratio }
  }
  return { width: 80 * ratio, height: 80 }
}

function resizeCropFreely(mode: ResizeHandle, point: Point, startCrop: CropRect, size: { width: number; height: number }) {
  const left = startCrop.x
  const right = startCrop.x + startCrop.width
  const top = startCrop.y
  const bottom = startCrop.y + startCrop.height
  const minSize = 40

  switch (mode) {
    case 'nw':
      return {
        x: clamp(point.x, 0, right - minSize),
        y: clamp(point.y, 0, bottom - minSize),
        width: right - clamp(point.x, 0, right - minSize),
        height: bottom - clamp(point.y, 0, bottom - minSize),
      }
    case 'ne':
      return {
        x: left,
        y: clamp(point.y, 0, bottom - minSize),
        width: clamp(point.x, left + minSize, size.width) - left,
        height: bottom - clamp(point.y, 0, bottom - minSize),
      }
    case 'sw':
      return {
        x: clamp(point.x, 0, right - minSize),
        y: top,
        width: right - clamp(point.x, 0, right - minSize),
        height: clamp(point.y, top + minSize, size.height) - top,
      }
    case 'se':
      return {
        x: left,
        y: top,
        width: clamp(point.x, left + minSize, size.width) - left,
        height: clamp(point.y, top + minSize, size.height) - top,
      }
  }
}

function resizeCropWithRatio(mode: ResizeHandle, point: Point, startCrop: CropRect, size: { width: number; height: number }, ratio: number) {
  const minimum = getMinimumCropSize(ratio)
  const anchorMap = {
    nw: { x: startCrop.x + startCrop.width, y: startCrop.y + startCrop.height, signX: -1, signY: -1 },
    ne: { x: startCrop.x, y: startCrop.y + startCrop.height, signX: 1, signY: -1 },
    sw: { x: startCrop.x + startCrop.width, y: startCrop.y, signX: -1, signY: 1 },
    se: { x: startCrop.x, y: startCrop.y, signX: 1, signY: 1 },
  } as const

  const anchor = anchorMap[mode]
  const maxWidth = anchor.signX > 0 ? size.width - anchor.x : anchor.x
  const maxHeight = anchor.signY > 0 ? size.height - anchor.y : anchor.y
  const rawWidth = Math.max(Math.abs(point.x - anchor.x), minimum.width)
  const rawHeight = Math.max(Math.abs(point.y - anchor.y), minimum.height)

  let width = rawWidth
  let height = width / ratio
  if (height < rawHeight) {
    height = rawHeight
    width = height * ratio
  }

  width = Math.min(width, maxWidth, maxHeight * ratio)
  height = width / ratio
  if (height > maxHeight) {
    height = maxHeight
    width = height * ratio
  }

  width = Math.max(width, minimum.width)
  height = Math.max(height, minimum.height)

  return clampCropToBounds({
    x: anchor.signX > 0 ? anchor.x : anchor.x - width,
    y: anchor.signY > 0 ? anchor.y : anchor.y - height,
    width,
    height,
  }, size)
}

function startCropDrag(mode: DragMode, event: PointerEvent) {
  if (!cropRect.value || !transformedSize.value) return
  const point = getPointFromClient(event.clientX, event.clientY, true)
  if (!point) return

  dragSession = {
    mode,
    startPoint: point,
    startCrop: cloneCrop(cropRect.value),
  }

  window.addEventListener('pointermove', handlePointerMove)
  window.addEventListener('pointerup', stopCropDrag)
  window.addEventListener('pointercancel', stopCropDrag)
}

function handlePointerMove(event: PointerEvent) {
  if (!dragSession || !transformedSize.value || !cropRect.value) return
  const point = getPointFromClient(event.clientX, event.clientY, true)
  if (!point) return

  if (dragSession.mode === 'move') {
    const deltaX = point.x - dragSession.startPoint.x
    const deltaY = point.y - dragSession.startPoint.y
    cropRect.value = {
      x: clamp(dragSession.startCrop.x + deltaX, 0, transformedSize.value.width - dragSession.startCrop.width),
      y: clamp(dragSession.startCrop.y + deltaY, 0, transformedSize.value.height - dragSession.startCrop.height),
      width: dragSession.startCrop.width,
      height: dragSession.startCrop.height,
    }
    return
  }

  const ratio = getAspectRatio(aspectPreset.value)
  if (ratio) {
    const fixedCrop = resizeCropWithRatio(dragSession.mode, point, dragSession.startCrop, transformedSize.value, ratio)
    cropRect.value = fixedCrop
    return
  }

  const freeCrop = resizeCropFreely(dragSession.mode, point, dragSession.startCrop, transformedSize.value)
  cropRect.value = clampCropToBounds(freeCrop, transformedSize.value)
}

function stopCropDrag() {
  dragSession = null
  window.removeEventListener('pointermove', handlePointerMove)
  window.removeEventListener('pointerup', stopCropDrag)
  window.removeEventListener('pointercancel', stopCropDrag)
}

async function 渲染编辑结果Blob(format: ExportFormat, quality?: number) {
  if (!cropRect.value) {
    throw new Error('当前没有可导出的编辑结果')
  }

  const transformedCanvas = buildTransformedCanvas()
  if (!transformedCanvas) {
    throw new Error('当前图片无法导出')
  }

  const exportCanvas = document.createElement('canvas')
  exportCanvas.width = Math.max(1, Math.round(cropRect.value.width))
  exportCanvas.height = Math.max(1, Math.round(cropRect.value.height))
  const context = exportCanvas.getContext('2d')
  if (!context) {
    throw new Error('canvas 上下文创建失败')
  }

  context.imageSmoothingEnabled = true
  context.imageSmoothingQuality = 'high'
  context.drawImage(
    transformedCanvas,
    Math.round(cropRect.value.x),
    Math.round(cropRect.value.y),
    Math.round(cropRect.value.width),
    Math.round(cropRect.value.height),
    0,
    0,
    exportCanvas.width,
    exportCanvas.height,
  )

  const blob = await new Promise<Blob | null>((resolve) => {
    exportCanvas.toBlob(resolve, format, quality)
  })

  if (!blob) {
    throw new Error('导出 blob 失败')
  }

  return blob
}

async function openEditedPreview() {
  if (!cropRect.value) {
    ElMessage.warning('请先上传图片')
    return
  }

  try {
    关闭图片预览()
    释放编辑结果预览链接()
    const blob = await 渲染编辑结果Blob('image/png')
    编辑结果预览Url = URL.createObjectURL(blob)

  const Fancybox = await 获取共享图片预览实例()
    Fancybox.show([{
      src: 编辑结果预览Url,
      thumbSrc: 编辑结果预览Url,
      type: 'image',
      caption: `${(exportOptions.name || 'edited-image').trim() || 'edited-image'}.png`,
    }], {
      ...图片预览选项,
      startIndex: 0,
    })
  } catch {
    ElMessage.error('大图预览打开失败，请稍后重试')
  }
}

async function exportEditedImage() {
  if (!cropRect.value) {
    ElMessage.warning('请先上传图片')
    return
  }

  isExporting.value = true
  try {
    const quality = exportOptions.format === 'image/png' ? undefined : exportOptions.quality / 100
    const blob = await 渲染编辑结果Blob(exportOptions.format, quality)
    const downloadUrl = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = downloadUrl
    anchor.download = `${exportOptions.name || 'edited-image'}.${exportExtension.value}`
    anchor.click()
    window.setTimeout(() => URL.revokeObjectURL(downloadUrl), 1000)
    ElMessage.success('图片已开始下载')
  } catch {
    ElMessage.error('导出失败，请稍后重试')
  } finally {
    isExporting.value = false
  }
}

function restoreFullSelection() {
  initializeCrop()
}

watch(
  () => [
    hasImage.value,
    normalizedRotation.value,
    imageTransform.flipX,
    imageTransform.flipY,
    imageTransform.brightness,
    imageTransform.contrast,
    imageTransform.saturation,
    imageTransform.grayscale,
    imageTransform.blur,
  ],
  () => {
    schedulePreviewRender()
  },
)

watch(aspectPreset, (next, prev) => {
  if (!hasImage.value || next === prev) return
  if (next === 'free') return
  initializeCrop()
})

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
  关闭图片预览()
  释放编辑结果预览链接()
  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
  }
  if (renderFrame) {
    window.cancelAnimationFrame(renderFrame)
    renderFrame = 0
  }
  stopCropDrag()
  revokeCurrentObjectUrl()
})
</script>

<template>
  <div class="image-editor">
    <div class="editor-grid">
      <aside class="editor-sidebar">
        <WorkbenchSectionCard class="editor-card" shadow="never" title="选择图片" :icon="Picture">
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
            <p>支持本地图片直接编辑</p>
          </div>

          <div class="upload-actions">
            <ElButton type="primary" @click="triggerFileDialog">选择图片</ElButton>
            <ElButton :disabled="!hasImage" @click="clearEditor">
              <Delete />
              清空图片
            </ElButton>
          </div>

          <div v-if="imageMeta" class="meta-stack">
            <div class="meta-row">
              <span>文件名</span>
              <strong>{{ imageMeta.name }}</strong>
            </div>
            <div class="meta-row">
              <span>格式</span>
              <strong>{{ imageMeta.type || '未知' }}</strong>
            </div>
            <div class="meta-row">
              <span>源图尺寸</span>
              <strong>{{ sourceSizeLabel }}</strong>
            </div>
            <div class="meta-row">
              <span>文件体积</span>
              <strong>{{ fileSizeLabel }}</strong>
            </div>
          </div>
        </WorkbenchSectionCard>

        <WorkbenchSectionCard class="editor-card" shadow="never" title="裁剪" :icon="Crop" :disabled="!hasImage">
          <ElRadioGroup v-model="aspectPreset" class="ratio-group" size="small" :disabled="!hasImage">
            <ElRadioButton v-for="item in aspectOptions" :key="item.value" :value="item.value">
              {{ item.label }}
            </ElRadioButton>
          </ElRadioGroup>

          <div class="tool-actions">
            <ElButton :disabled="!hasImage" @click="resetCrop">
              <Refresh />
              整张选中
            </ElButton>
            <ElButton :disabled="!hasImage" @click="restoreFullSelection">
              适配当前比例
            </ElButton>
          </div>

          <p class="hint-text">拖动选框可以移动，拖动四角可以裁剪尺寸。</p>
        </WorkbenchSectionCard>

        <WorkbenchSectionCard class="editor-card" shadow="never" title="变换" :icon="Switch" :disabled="!hasImage">
          <div class="tool-actions">
            <ElButton :disabled="!hasImage" @click="rotate(-90)">
              <RefreshLeft />
              左转 90°
            </ElButton>
            <ElButton :disabled="!hasImage" @click="rotate(90)">
              <RefreshRight />
              右转 90°
            </ElButton>
          </div>

          <div class="tool-actions">
            <ElButton :disabled="!hasImage" @click="flipHorizontal">水平翻转</ElButton>
            <ElButton :disabled="!hasImage" @click="flipVertical">垂直翻转</ElButton>
          </div>
        </WorkbenchSectionCard>

        <WorkbenchSectionCard class="editor-card" shadow="never" title="调整" :icon="MagicStick" :disabled="!hasImage">
          <template #actions>
            <ElButton text :disabled="!hasImage" @click="resetAdjustments">重置</ElButton>
          </template>

          <div class="slider-stack">
            <label class="slider-item">
              <span>亮度 {{ imageTransform.brightness }}%</span>
              <ElSlider v-model="imageTransform.brightness" :disabled="!hasImage" :min="0" :max="200" />
            </label>
            <label class="slider-item">
              <span>对比度 {{ imageTransform.contrast }}%</span>
              <ElSlider v-model="imageTransform.contrast" :disabled="!hasImage" :min="0" :max="200" />
            </label>
            <label class="slider-item">
              <span>饱和度 {{ imageTransform.saturation }}%</span>
              <ElSlider v-model="imageTransform.saturation" :disabled="!hasImage" :min="0" :max="200" />
            </label>
            <label class="slider-item">
              <span>灰度 {{ imageTransform.grayscale }}%</span>
              <ElSlider v-model="imageTransform.grayscale" :disabled="!hasImage" :min="0" :max="100" />
            </label>
            <label class="slider-item">
              <span>模糊 {{ imageTransform.blur.toFixed(1) }}px</span>
              <ElSlider v-model="imageTransform.blur" :disabled="!hasImage" :min="0" :max="12" :step="0.5" />
            </label>
          </div>
        </WorkbenchSectionCard>
      </aside>

      <section class="editor-main">
        <WorkbenchSectionCard class="editor-card preview-card" shadow="never" title="预览画布" @toggle="handlePreviewCardToggle">
          <template #actions>
            <div class="preview-card__actions">
              <div class="preview-card__tags">
                <ElTag round effect="plain">纯前端</ElTag>
                <ElTag round effect="plain">本地处理</ElTag>
              </div>
              <ElButton
                circle
                class="preview-card__preview-button"
                :disabled="!hasImage"
                :aria-label="hasImage ? '打开当前编辑结果大图预览' : undefined"
                @click="void openEditedPreview()"
              >
                <ElIcon><View /></ElIcon>
              </ElButton>
            </div>
          </template>

          <div
            ref="previewStageRef"
            class="preview-stage"
            :class="{ 'is-empty': !hasImage, 'is-dragover': isDragOver }"
            @dragenter.prevent="isDragOver = true"
            @dragover.prevent="isDragOver = true"
            @dragleave.prevent="isDragOver = false"
            @drop="handleDrop"
          >
            <canvas ref="previewCanvasRef" class="preview-canvas" />

            <div v-if="frameStyle" class="preview-frame" :style="frameStyle" />

            <div
              v-if="cropStyle"
              class="crop-selection"
              :style="cropStyle"
              @pointerdown.stop.prevent="startCropDrag('move', $event)"
            >
              <span class="crop-selection__label">{{ outputSizeLabel }}</span>
              <button
                v-for="handle in ['nw', 'ne', 'sw', 'se']"
                :key="handle"
                type="button"
                class="crop-handle"
                :class="`is-${handle}`"
                :style="{ cursor: handleCursorMap[handle as ResizeHandle] }"
                @pointerdown.stop.prevent="startCropDrag(handle as ResizeHandle, $event)"
              />
            </div>

            <div v-if="!hasImage" class="preview-empty">
              <ElEmpty description="先选择一张图片" />
            </div>
          </div>

          <p class="preview-hint">
            预览区会显示当前变换结果。旋转、翻转或调色后，导出内容与这里保持一致，右上角按钮可查看大图预览。
          </p>
        </WorkbenchSectionCard>

        <WorkbenchSectionCard class="editor-card export-card" shadow="never" title="导出" :icon="Download" :disabled="!hasImage">
          <div class="export-grid">
            <label class="export-field">
              <span>文件名</span>
              <input v-model="exportOptions.name" class="export-input" type="text" :disabled="!hasImage">
            </label>

            <label class="export-field">
              <span>格式</span>
              <ElSelect v-model="exportOptions.format" :disabled="!hasImage">
                <ElOption
                  v-for="item in exportFormatOptions"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
                />
              </ElSelect>
            </label>
          </div>

          <label v-if="shouldShowQuality" class="export-field">
            <span>质量 {{ exportOptions.quality }}%</span>
            <ElSlider v-model="exportOptions.quality" :disabled="!hasImage" :min="60" :max="100" />
          </label>

          <div class="meta-stack meta-stack--two-column">
            <div class="meta-row">
              <span>输出尺寸</span>
              <strong>{{ outputSizeLabel }}</strong>
            </div>
            <div class="meta-row">
              <span>扩展名</span>
              <strong>.{{ exportExtension }}</strong>
            </div>
          </div>

          <ElButton type="primary" size="large" :loading="isExporting" :disabled="!hasImage" @click="exportEditedImage">
            <Download />
            下载编辑结果
          </ElButton>
        </WorkbenchSectionCard>
      </section>
    </div>
  </div>
</template>

<style scoped>
.image-editor {
  --editor-surface: color-mix(in srgb, var(--bg-card) 88%, white);
  --editor-surface-soft: color-mix(in srgb, var(--el-color-primary) 4%, var(--bg-card));
  --editor-surface-strong: color-mix(in srgb, var(--el-color-primary) 8%, var(--bg-card));
  --editor-border-soft: color-mix(in srgb, var(--el-color-primary) 10%, var(--border-color));
  --editor-border-strong: color-mix(in srgb, var(--el-color-primary) 22%, var(--border-color));
  --editor-title: var(--text-primary);
  --editor-text: var(--text-secondary);
  --editor-text-soft: color-mix(in srgb, var(--text-secondary) 88%, var(--el-color-primary));
  --editor-canvas-bg: color-mix(in srgb, var(--bg-primary) 94%, var(--el-color-primary) 6%);
  display: grid;
  gap: 18px;
}

.editor-grid {
  display: grid;
  grid-template-columns: 340px minmax(0, 1fr);
  gap: 18px;
  align-items: start;
}

.editor-sidebar,
.editor-main {
  display: grid;
  gap: 16px;
  min-width: 0;
}

.editor-card {
  border-radius: 24px;
  border-color: var(--editor-border-soft);
  background: color-mix(in srgb, var(--editor-surface) 92%, transparent);
  box-shadow: 0 12px 30px rgba(15, 23, 42, 0.05);
  backdrop-filter: blur(14px);
}

.editor-card :deep(.el-card__header) {
  border-bottom-color: var(--editor-border-soft);
  padding: 8px 20px 6px;
}

.editor-card :deep(.el-card__body) {
  padding: 18px 20px 20px;
}

.file-input {
  display: none;
}

.upload-dropzone {
  min-height: 196px;
  padding: 20px;
  border: 1.5px dashed var(--editor-border-strong);
  border-radius: 22px;
  background:
    radial-gradient(circle at top, rgb(var(--el-color-primary-rgb) / 0.1), transparent 54%),
    var(--editor-surface-soft);
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
  color: var(--editor-title);
  font-size: 16px;
}

.upload-dropzone p {
  color: var(--editor-text);
  line-height: 1.7;
}

.upload-actions,
.tool-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.upload-actions {
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
  background: var(--editor-surface-soft);
}

.meta-row span {
  color: var(--editor-text);
  font-size: 13px;
}

.meta-row strong {
  color: var(--editor-title);
  line-height: 1.6;
  word-break: break-word;
}

.ratio-group {
  display: flex;
  flex-wrap: wrap;
  margin-bottom: 14px;
}

.hint-text {
  margin-top: 14px;
  color: var(--editor-text);
  line-height: 1.7;
  font-size: 13px;
}

.slider-stack {
  display: grid;
  gap: 12px;
}

.slider-item {
  display: grid;
  gap: 8px;
}

.slider-item > span {
  color: var(--editor-text-soft);
  font-size: 13px;
  font-weight: 600;
}

.preview-card__actions {
  display: inline-flex;
  align-items: center;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 8px;
}

.preview-card__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.preview-card__preview-button {
  color: var(--editor-text);
  border-color: color-mix(in srgb, var(--el-color-primary) 16%, var(--border-color));
  background: color-mix(in srgb, var(--editor-surface-soft) 92%, white);
}

.preview-card__preview-button:hover {
  color: var(--el-color-primary);
  border-color: color-mix(in srgb, var(--el-color-primary) 28%, var(--border-color));
  background: color-mix(in srgb, var(--el-color-primary) 10%, white);
}

.preview-stage {
  position: relative;
  min-height: 620px;
  overflow: hidden;
  border-radius: 24px;
  border: 1px solid var(--editor-border-soft);
  background: var(--editor-canvas-bg);
}

.preview-stage.is-empty {
  display: grid;
  place-items: center;
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

.preview-frame {
  position: absolute;
  border: 1px solid rgba(255, 255, 255, 0.82);
  box-shadow: 0 0 0 1px var(--editor-border-soft);
  pointer-events: none;
}

.crop-selection {
  position: absolute;
  border: 2px solid rgba(255, 255, 255, 0.96);
  box-shadow:
    0 0 0 1px rgba(16, 36, 24, 0.28),
    0 0 0 9999px rgba(8, 14, 12, 0.32);
  background: rgba(255, 255, 255, 0.04);
  cursor: move;
  touch-action: none;
}

.crop-selection__label {
  position: absolute;
  top: 10px;
  left: 10px;
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  background: rgba(8, 14, 12, 0.72);
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  pointer-events: none;
}

.crop-handle {
  position: absolute;
  width: 14px;
  height: 14px;
  border: none;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 0 0 1px rgba(16, 36, 24, 0.22);
}

.crop-handle.is-nw {
  top: -7px;
  left: -7px;
}

.crop-handle.is-ne {
  top: -7px;
  right: -7px;
}

.crop-handle.is-sw {
  bottom: -7px;
  left: -7px;
}

.crop-handle.is-se {
  right: -7px;
  bottom: -7px;
}

.preview-hint {
  margin-top: 14px;
  color: var(--editor-text);
  line-height: 1.8;
}

.export-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 220px;
  gap: 12px;
}

.export-field {
  display: grid;
  gap: 8px;
  margin-bottom: 14px;
}

.export-field > span {
  color: var(--editor-text-soft);
  font-size: 13px;
  font-weight: 600;
}

.export-input {
  min-height: 42px;
  padding: 0 14px;
  border: 1px solid var(--editor-border-soft);
  border-radius: 14px;
  background: color-mix(in srgb, var(--editor-surface-soft) 88%, white);
  color: var(--editor-title);
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

.dark .editor-card {
  --editor-surface: color-mix(in srgb, var(--bg-card) 92%, transparent);
  --editor-surface-soft: color-mix(in srgb, var(--el-color-primary-light-5) 8%, var(--bg-card));
  --editor-surface-strong: color-mix(in srgb, var(--el-color-primary-light-5) 14%, var(--bg-card));
  --editor-border-soft: color-mix(in srgb, var(--el-color-primary-light-5) 10%, var(--border-color));
  --editor-border-strong: color-mix(in srgb, var(--el-color-primary-light-5) 18%, var(--border-color));
  --editor-title: var(--text-primary);
  --editor-text: var(--text-secondary);
  --editor-text-soft: color-mix(in srgb, var(--text-secondary) 86%, var(--el-color-primary-light-5));
  --editor-canvas-bg: color-mix(in srgb, var(--bg-primary) 88%, var(--el-color-primary-light-5) 12%);
  background:
    linear-gradient(145deg, color-mix(in srgb, var(--el-color-primary-light-5) 10%, transparent), rgba(16, 24, 22, 0.92)),
    var(--editor-surface);
  border-color: var(--editor-border-soft);
  box-shadow: 0 18px 40px rgba(2, 6, 23, 0.26);
}

.dark .meta-row,
.dark .upload-dropzone,
.dark .export-input {
  background: var(--editor-surface-soft);
  border-color: var(--editor-border-soft);
}

.dark .upload-dropzone:hover,
.dark .upload-dropzone.is-dragover {
  background: color-mix(in srgb, var(--el-color-primary-light-5) 12%, var(--bg-card));
}

.dark .crop-selection {
  box-shadow:
    0 0 0 1px rgba(255, 255, 255, 0.12),
    0 0 0 9999px rgba(2, 6, 23, 0.42);
}

.dark .crop-selection__label {
  background: rgba(255, 255, 255, 0.88);
  color: #102418;
}

.dark .crop-handle {
  background: #fff;
}

@media (max-width: 1280px) {
  .editor-grid {
    grid-template-columns: 1fr;
  }

  .preview-stage {
    min-height: 520px;
  }
}

@media (max-width: 767px) {
  .editor-card :deep(.el-card__header),
  .editor-card :deep(.el-card__body) {
    padding-left: 16px;
    padding-right: 16px;
  }

  .preview-stage {
    min-height: 360px;
  }

  .export-grid,
  .meta-stack--two-column {
    grid-template-columns: 1fr;
  }

  .crop-selection__label {
    top: 8px;
    left: 8px;
  }
}
</style>
