<script setup lang="ts">
/* global getComputedStyle, HTMLImageElement, Image, CanvasRenderingContext2D, KeyboardEvent */
import { Icon } from '@iconify/vue'
import { ElButton, ElMessage } from 'element-plus'
import QRCode from 'qrcode'
import { nextTick, ref, watch } from 'vue'

const props = defineProps<{
  title: string
  author: string
  description?: string
  pubDate: string
  coverImage?: string | null
  url: string
  siteTitle: string
  avatar?: string | null
}>()

const showDialog = ref(false)
const posterImage = ref<string | null>(null)
const generating = ref(false)
const themeColor = ref('#e3769b')
const 通用头像字体 = `'Noto Sans SC', 'Microsoft YaHei', 'PingFang SC', 'Avenir Next', 'Hiragino Sans GB', sans-serif`

interface 海报资源 {
  qrImg: HTMLImageElement | null
  coverImg: HTMLImageElement | null
  avatarImg: HTMLImageElement | null
}

interface 日期信息 {
  day: string
  month: string
  year: string
}

interface 海报布局 {
  scale: number
  width: number
  padding: number
  contentWidth: number
  coverHeight: number
  titleLines: string[]
  titleLineHeight: number
  descLines: string[]
  descLineHeight: number
  descHeight: number
  canvasHeight: number
}

function getThemeColor(): string {
  const el = document.createElement('div')
  el.style.color = 'var(--el-color-primary)'
  el.style.display = 'none'
  document.body.appendChild(el)
  const computed = getComputedStyle(el).color
  document.body.removeChild(el)
  return computed || themeColor.value
}

function loadImage(src: string): Promise<HTMLImageElement | null> {
  return new Promise((resolve) => {
    const img = new Image()
    img.crossOrigin = 'anonymous'
    img.onload = () => resolve(img)
    img.onerror = () => {
      if (!src.includes('images.weserv.nl')) {
        const proxyUrl = `https://images.weserv.nl/?url=${encodeURIComponent(src)}&output=png`
        const proxyImg = new Image()
        proxyImg.crossOrigin = 'anonymous'
        proxyImg.onload = () => resolve(proxyImg)
        proxyImg.onerror = () => resolve(null)
        proxyImg.src = proxyUrl
      } else {
        resolve(null)
      }
    }
    img.src = src
  })
}

function getLines(ctx: CanvasRenderingContext2D, text: string, maxWidth: number): string[] {
  const chars = text.split('')
  const lines: string[] = []
  let currentLine = ''
  for (const char of chars) {
    const width = ctx.measureText(currentLine + char).width
    if (width < maxWidth) {
      currentLine += char
    } else {
      lines.push(currentLine)
      currentLine = char
    }
  }
  if (currentLine) {
    lines.push(currentLine)
  }
  return lines
}

function 获取头像回退文字(text: string) {
  return text.trim().slice(0, 1).toUpperCase() || 'U'
}

function hexToRgb(color: string) {
  const value = color.trim()
  const match = value.match(/^#([0-9a-f]{3}|[0-9a-f]{6})$/i)
  if (!match) return null
  const hex = match[1].length === 3
    ? match[1].split('').map((char) => char + char).join('')
    : match[1]

  return {
    r: Number.parseInt(hex.slice(0, 2), 16),
    g: Number.parseInt(hex.slice(2, 4), 16),
    b: Number.parseInt(hex.slice(4, 6), 16),
  }
}

function 生成头像渐变色(primaryColor: string) {
  const rgb = hexToRgb(primaryColor)
  if (!rgb) {
    return {
      start: '#ec4899',
      end: '#f472b6',
    }
  }

  const 提亮 = (value: number, amount: number) => Math.min(255, Math.round(value + (255 - value) * amount))

  return {
    start: `rgb(${rgb.r} ${rgb.g} ${rgb.b})`,
    end: `rgb(${提亮(rgb.r, 0.24)} ${提亮(rgb.g, 0.24)} ${提亮(rgb.b, 0.24)})`,
  }
}

function drawRoundedRect(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  width: number,
  height: number,
  radius: number,
) {
  ctx.beginPath()
  ctx.moveTo(x + radius, y)
  ctx.lineTo(x + width - radius, y)
  ctx.quadraticCurveTo(x + width, y, x + width, y + radius)
  ctx.lineTo(x + width, y + height - radius)
  ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height)
  ctx.lineTo(x + radius, y + height)
  ctx.quadraticCurveTo(x, y + height, x, y + height - radius)
  ctx.lineTo(x, y + radius)
  ctx.quadraticCurveTo(x, y, x + radius, y)
  ctx.closePath()
}

function 创建画布(width: number, height: number) {
  const canvas = document.createElement('canvas')
  const ctx = canvas.getContext('2d')
  if (!ctx) {
    throw new Error('Canvas context not available')
  }

  canvas.width = width
  canvas.height = height
  return { canvas, ctx }
}

async function 加载海报资源(scale: number): Promise<海报资源> {
  const qrCodeUrl = await QRCode.toDataURL(props.url, {
    margin: 1,
    width: 100 * scale,
    color: { dark: '#000000', light: '#ffffff' },
  })

  const [qrImg, coverImg, avatarImg] = await Promise.all([
    loadImage(qrCodeUrl),
    props.coverImage ? loadImage(props.coverImage) : Promise.resolve(null),
    props.avatar ? loadImage(props.avatar) : Promise.resolve(null),
  ])

  return { qrImg, coverImg, avatarImg }
}

function 解析发布日期(pubDate: string): 日期信息 | null {
  try {
    const d = new Date(pubDate)
    if (Number.isNaN(d.getTime())) {
      return null
    }

    return {
      day: d.getDate().toString().padStart(2, '0'),
      month: (d.getMonth() + 1).toString().padStart(2, '0'),
      year: d.getFullYear().toString(),
    }
  } catch {
    return null
  }
}

function 创建海报布局(
  ctx: CanvasRenderingContext2D,
  options: { scale: number; width: number; padding: number; hasCover: boolean },
): 海报布局 {
  const { scale, width, padding, hasCover } = options
  const contentWidth = width - padding * 2
  const coverHeight = (hasCover ? 200 : 120) * scale

  ctx.font = `700 ${24 * scale}px 'Roboto', sans-serif`
  const titleLines = getLines(ctx, props.title, contentWidth)
  const titleLineHeight = 30 * scale

  let descLines: string[] = []
  const descLineHeight = 25 * scale
  if (props.description) {
    ctx.font = `${14 * scale}px 'Roboto', sans-serif`
    descLines = getLines(ctx, props.description, contentWidth - 16 * scale).slice(0, 6)
  }

  const titleHeight = titleLines.length * titleLineHeight
  const descHeight = descLines.length > 0 ? descLines.length * descLineHeight : 0
  const footerHeight = 64 * scale
  const canvasHeight = (
    coverHeight
    + padding
    + titleHeight
    + 16 * scale
    + (descHeight || 8 * scale)
    + 24 * scale
    + footerHeight
    + padding
  )

  return {
    scale,
    width,
    padding,
    contentWidth,
    coverHeight,
    titleLines,
    titleLineHeight,
    descLines,
    descLineHeight,
    descHeight,
    canvasHeight,
  }
}

function 绘制海报背景(ctx: CanvasRenderingContext2D, layout: 海报布局) {
  ctx.fillStyle = '#ffffff'
  ctx.fillRect(0, 0, layout.width, layout.canvasHeight)

  ctx.save()
  ctx.globalAlpha = 0.1
  ctx.fillStyle = themeColor.value
  ctx.beginPath()
  ctx.arc(layout.width - 25 * layout.scale, 25 * layout.scale, 75 * layout.scale, 0, Math.PI * 2)
  ctx.fill()
  ctx.beginPath()
  ctx.arc(10 * layout.scale, layout.canvasHeight - 10 * layout.scale, 50 * layout.scale, 0, Math.PI * 2)
  ctx.fill()
  ctx.restore()
}

function 绘制封面与日期(
  ctx: CanvasRenderingContext2D,
  layout: 海报布局,
  coverImg: HTMLImageElement | null,
  dateInfo: 日期信息 | null,
) {
  if (coverImg) {
    const imgRatio = coverImg.width / coverImg.height
    const targetRatio = layout.width / layout.coverHeight
    let sx: number
    let sy: number
    let sWidth: number
    let sHeight: number

    if (imgRatio > targetRatio) {
      sHeight = coverImg.height
      sWidth = sHeight * targetRatio
      sx = (coverImg.width - sWidth) / 2
      sy = 0
    } else {
      sWidth = coverImg.width
      sHeight = sWidth / targetRatio
      sx = 0
      sy = (coverImg.height - sHeight) / 2
    }
    ctx.drawImage(coverImg, sx, sy, sWidth, sHeight, 0, 0, layout.width, layout.coverHeight)
  } else {
    ctx.save()
    ctx.fillStyle = themeColor.value
    ctx.globalAlpha = 0.2
    ctx.fillRect(0, 0, layout.width, layout.coverHeight)
    ctx.restore()
  }

  if (!dateInfo) {
    return
  }

  const dateBoxW = 60 * layout.scale
  const dateBoxH = 60 * layout.scale
  const dateBoxX = layout.padding
  const dateBoxY = layout.coverHeight - dateBoxH

  ctx.fillStyle = 'rgba(0, 0, 0, 0.3)'
  drawRoundedRect(ctx, dateBoxX, dateBoxY, dateBoxW, dateBoxH, 4 * layout.scale)
  ctx.fill()

  ctx.fillStyle = '#ffffff'
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  ctx.font = `700 ${30 * layout.scale}px 'Roboto', sans-serif`
  ctx.fillText(dateInfo.day, dateBoxX + dateBoxW / 2, dateBoxY + 24 * layout.scale)

  ctx.beginPath()
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.6)'
  ctx.lineWidth = 1 * layout.scale
  ctx.moveTo(dateBoxX + 10 * layout.scale, dateBoxY + 42 * layout.scale)
  ctx.lineTo(dateBoxX + dateBoxW - 10 * layout.scale, dateBoxY + 42 * layout.scale)
  ctx.stroke()

  ctx.font = `${10 * layout.scale}px 'Roboto', sans-serif`
  ctx.fillText(`${dateInfo.year} ${dateInfo.month}`, dateBoxX + dateBoxW / 2, dateBoxY + 51 * layout.scale)
}

function 绘制正文(ctx: CanvasRenderingContext2D, layout: 海报布局) {
  let drawY = layout.coverHeight + layout.padding

  ctx.textBaseline = 'top'
  ctx.textAlign = 'left'
  ctx.font = `700 ${24 * layout.scale}px 'Roboto', sans-serif`
  ctx.fillStyle = '#111827'
  layout.titleLines.forEach((line) => {
    ctx.fillText(line, layout.padding, drawY)
    drawY += layout.titleLineHeight
  })
  drawY += 16 * layout.scale - (layout.titleLineHeight - 24 * layout.scale)

  if (layout.descLines.length > 0) {
    ctx.fillStyle = '#e5e7eb'
    drawRoundedRect(ctx, layout.padding, drawY - 8 * layout.scale, 4 * layout.scale, layout.descHeight + 8 * layout.scale, 2 * layout.scale)
    ctx.fill()

    ctx.font = `${14 * layout.scale}px 'Roboto', sans-serif`
    ctx.fillStyle = '#4b5563'
    layout.descLines.forEach((line) => {
      ctx.fillText(line, layout.padding + 16 * layout.scale, drawY)
      drawY += layout.descLineHeight
    })
  } else {
    drawY += 8 * layout.scale
  }

  drawY += 24 * layout.scale
  ctx.beginPath()
  ctx.strokeStyle = '#f3f4f6'
  ctx.lineWidth = 1 * layout.scale
  ctx.moveTo(layout.padding, drawY)
  ctx.lineTo(layout.width - layout.padding, drawY)
  ctx.stroke()

  return drawY + 24 * layout.scale
}

function 生成头像画布(options: {
  size: number
  image: HTMLImageElement | null
  text: string
  primaryColor: string
  scale: number
}) {
  const { size, image, text, primaryColor, scale } = options
  const { canvas, ctx } = 创建画布(size, size)
  const center = size / 2

  if (image) {
    ctx.save()
    ctx.beginPath()
    ctx.arc(center, center, size / 2, 0, Math.PI * 2)
    ctx.closePath()
    ctx.clip()
    ctx.drawImage(image, 0, 0, size, size)
    ctx.restore()
  } else {
    const 渐变色 = 生成头像渐变色(primaryColor)
    const 渐变 = ctx.createLinearGradient(0, 0, size, size)
    渐变.addColorStop(0, 渐变色.start)
    渐变.addColorStop(1, 渐变色.end)
    ctx.fillStyle = 渐变
    ctx.beginPath()
    ctx.arc(center, center, size / 2, 0, Math.PI * 2)
    ctx.fill()

    ctx.fillStyle = '#ffffff'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.font = `700 ${26 * scale}px ${通用头像字体}`
    ctx.fillText(获取头像回退文字(text), center, center + 1 * scale)
  }

  ctx.beginPath()
  ctx.arc(center, center, size / 2, 0, Math.PI * 2)
  ctx.strokeStyle = '#ffffff'
  ctx.lineWidth = 2 * scale
  ctx.stroke()

  return canvas
}

function 绘制页脚(
  ctx: CanvasRenderingContext2D,
  layout: 海报布局,
  footerY: number,
  avatarCanvas: HTMLCanvasElement,
  qrImg: HTMLImageElement | null,
) {
  const avatarSize = avatarCanvas.width
  const avatarX = layout.padding
  const textCenterY = footerY + 32 * layout.scale
  ctx.drawImage(avatarCanvas, avatarX, footerY, avatarSize, avatarSize)

  const authorTextX = avatarX + avatarSize + 16 * layout.scale
  ctx.fillStyle = '#9ca3af'
  ctx.font = `${12 * layout.scale}px 'Roboto', sans-serif`
  ctx.textAlign = 'left'
  ctx.fillText('作者', authorTextX, textCenterY - 20 * layout.scale)

  ctx.fillStyle = '#1f2937'
  ctx.font = `700 ${20 * layout.scale}px 'Roboto', sans-serif`
  ctx.fillText(props.author, authorTextX, textCenterY + 4 * layout.scale)

  const qrSize = 64 * layout.scale
  const qrX = layout.width - layout.padding - qrSize
  ctx.fillStyle = '#ffffff'
  ctx.shadowColor = 'rgba(0, 0, 0, 0.05)'
  ctx.shadowBlur = 4 * layout.scale
  ctx.shadowOffsetY = 2 * layout.scale
  drawRoundedRect(ctx, qrX, footerY, qrSize, qrSize, 4 * layout.scale)
  ctx.fill()
  ctx.shadowColor = 'transparent'

  const qrInnerSize = 56 * layout.scale
  const qrPadding = (qrSize - qrInnerSize) / 2
  if (qrImg) {
    ctx.drawImage(qrImg, qrX + qrPadding, footerY + qrPadding, qrInnerSize, qrInnerSize)
  }

  const siteInfoX = qrX - 16 * layout.scale
  ctx.textAlign = 'right'
  ctx.fillStyle = '#9ca3af'
  ctx.font = `${12 * layout.scale}px 'Roboto', sans-serif`
  ctx.fillText('扫码阅读', siteInfoX, textCenterY - 20 * layout.scale)

  ctx.fillStyle = '#1f2937'
  ctx.font = `700 ${20 * layout.scale}px 'Roboto', sans-serif`
  ctx.fillText(props.siteTitle, siteInfoX, textCenterY + 4 * layout.scale)
}

async function generatePoster() {
  showDialog.value = true
  generating.value = true
  posterImage.value = null
  await nextTick()

  themeColor.value = getThemeColor()

  try {
    const scale = 2
    const width = 425 * scale
    const padding = 24 * scale

    const 资源 = await 加载海报资源(scale)
    const { canvas, ctx } = 创建画布(width, 1000 * scale)
    const 布局 = 创建海报布局(ctx, {
      scale,
      width,
      padding,
      hasCover: Boolean(资源.coverImg),
    })
    canvas.height = 布局.canvasHeight

    绘制海报背景(ctx, 布局)
    绘制封面与日期(ctx, 布局, 资源.coverImg, 解析发布日期(props.pubDate))
    const footerY = 绘制正文(ctx, 布局)
    const 头像画布 = 生成头像画布({
      size: 64 * scale,
      image: 资源.avatarImg,
      text: props.author,
      primaryColor: themeColor.value,
      scale,
    })
    绘制页脚(ctx, 布局, footerY, 头像画布, 资源.qrImg)

    posterImage.value = canvas.toDataURL('image/png')
  } catch (error) {
    console.error('Failed to generate poster:', error)
  } finally {
    generating.value = false
  }
}

function downloadPoster() {
  if (!posterImage.value) return
  const a = document.createElement('a')
  a.href = posterImage.value
  a.download = `poster-${props.title.replace(/\s+/g, '-')}.png`
  a.click()
}

async function copyLink() {
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(props.url)
    } else {
      const textarea = document.createElement('textarea')
      textarea.value = props.url
      textarea.style.position = 'fixed'
      textarea.style.left = '-9999px'
      document.body.appendChild(textarea)
      textarea.focus()
      textarea.select()
      const successful = document.execCommand('copy')
      document.body.removeChild(textarea)
      if (!successful) throw new Error('execCommand copy failed')
    }
    ElMessage.success('链接已复制到剪贴板！')
  } catch {
    ElMessage.error('复制失败，请手动复制链接')
  }
}

function closePosterPreview() {
  showDialog.value = false
}

function handleOverlayKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') {
    closePosterPreview()
  }
}

watch(showDialog, (val) => {
  if (!val) {
    posterImage.value = null
  }
})
</script>

<template>
  <ElButton
    class="share-poster-btn"
    size="small"
    aria-label="分享文章"
    title="分享文章"
    @click="generatePoster"
  >
    <Icon icon="material-symbols:share" class="share-poster-btn-icon" />
  </ElButton>

  <Teleport to="body">
    <div
      v-if="showDialog"
      class="poster-overlay"
      tabindex="0"
      @click="closePosterPreview"
      @keydown="handleOverlayKeydown"
    >
      <div class="poster-modal" @click.stop>
        <div class="poster-dialog-body">
          <div class="poster-preview">
            <img v-if="posterImage" :src="posterImage" alt="分享海报" class="poster-img">
            <div v-else class="poster-loading">
              <div class="poster-spinner" :style="{ borderTopColor: themeColor }" />
              <span class="poster-loading-text">正在生成海报...</span>
            </div>
          </div>
        </div>

        <div class="poster-dialog-footer">
          <ElButton
            class="poster-action-btn"
            @click="copyLink"
          >
            <Icon icon="material-symbols:link" class="poster-action-icon" />
            <span>复制链接</span>
          </ElButton>
          <ElButton
            type="primary"
            class="poster-action-btn primary"
            :disabled="!posterImage"
            :style="{ backgroundColor: themeColor, borderColor: themeColor }"
            @click="downloadPoster"
          >
            <Icon icon="material-symbols:download" class="poster-action-icon" />
            <span>保存海报</span>
          </ElButton>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.share-poster-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  padding: 0;
  color: var(--el-color-primary);
  border: none;
  border-radius: 0.375rem;
  background: rgba(var(--el-color-primary-rgb), 0.1);
  transition: color 0.15s ease, background-color 0.15s ease, transform 0.15s ease;
}

.share-poster-btn:hover {
  color: var(--el-color-primary);
  background: rgba(var(--el-color-primary-rgb), 0.16);
}

.dark .share-poster-btn {
  color: rgba(255, 255, 255, 0.92);
  background: rgba(var(--el-color-primary-rgb), 0.16);
}

.dark .share-poster-btn:hover {
  color: #fff;
  background: rgba(var(--el-color-primary-rgb), 0.22);
}

.share-poster-btn-icon {
  font-size: 1.25rem;
  line-height: 1;
}

.poster-overlay {
  position: fixed;
  inset: 0;
  z-index: 3000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
}

.poster-modal {
  display: flex;
  flex-direction: column;
  width: min(100%, 440px);
  max-height: 90vh;
  overflow-y: auto;
  background: #ffffff;
  border-radius: 1rem;
  box-shadow: 0 24px 48px rgba(0, 0, 0, 0.3);
}

.dark .poster-modal {
  background: #1f2937;
}

.poster-dialog-body {
  padding: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  background: #f9fafb;
}

.dark .poster-dialog-body {
  background: #111827;
}

.poster-preview {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  min-height: 200px;
}

.poster-img {
  display: block;
  max-width: 100%;
  height: auto;
  border-radius: 8px;
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.18);
}

.poster-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 40px;
  color: #e5e7eb;
}

.poster-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #e5e7eb;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.dark .poster-spinner {
  border-color: #334155;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.poster-loading-text {
  font-size: 0.875rem;
  color: currentColor;
}

.poster-dialog-footer {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  padding: 16px;
  border-top: 1px solid #f3f4f6;
}

.dark .poster-dialog-footer {
  border-top-color: #374151;
}

.poster-action-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  min-height: 48px;
  margin: 0;
}

.poster-action-btn:not(.primary) {
  color: #374151;
  border-color: transparent;
  background: #f3f4f6;
}

.poster-action-btn:not(.primary):hover {
  color: #111827;
  background: #e5e7eb;
}

.dark .poster-action-btn:not(.primary) {
  color: #e5e7eb;
  background: #374151;
}

.dark .poster-action-btn:not(.primary):hover {
  color: #f9fafb;
  background: #4b5563;
}

.poster-action-icon {
  font-size: 1rem;
  margin-right: 6px;
}
</style>
