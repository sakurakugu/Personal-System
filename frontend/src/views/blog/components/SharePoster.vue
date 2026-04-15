<script setup lang="ts">
/* global getComputedStyle, HTMLImageElement, Image, CanvasRenderingContext2D */
import { Icon } from '@iconify/vue'
import { ElButton, ElDialog } from 'element-plus'
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
const copied = ref(false)
const themeColor = ref('#558e88')

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

    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')
    if (!ctx) throw new Error('Canvas context not available')

    canvas.width = width
    canvas.height = 1000 * scale

    const contentWidth = width - padding * 2
    let currentY = 0

    const coverHeight = (coverImg ? 200 : 120) * scale
    currentY += coverHeight
    currentY += padding

    ctx.font = `700 ${24 * scale}px 'Roboto', sans-serif`
    const titleLines = getLines(ctx, props.title, contentWidth)
    const titleLineHeight = 30 * scale
    const titleHeight = titleLines.length * titleLineHeight
    currentY += titleHeight
    currentY += 16 * scale

    let descHeight = 0
    if (props.description) {
      ctx.font = `${14 * scale}px 'Roboto', sans-serif`
      const descLines = getLines(ctx, props.description, contentWidth - 16 * scale)
      const maxDescLines = 6
      const displayDescLines = descLines.slice(0, maxDescLines)
      const descLineHeight = 25 * scale
      descHeight = displayDescLines.length * descLineHeight
      currentY += descHeight
    } else {
      currentY += 8 * scale
    }

    currentY += 24 * scale
    const footerHeight = 64 * scale
    currentY += footerHeight
    currentY += padding

    canvas.height = currentY

    ctx.fillStyle = '#ffffff'
    ctx.fillRect(0, 0, canvas.width, canvas.height)

    ctx.save()
    ctx.globalAlpha = 0.1
    ctx.fillStyle = themeColor.value
    ctx.beginPath()
    ctx.arc(width - 25 * scale, 25 * scale, 75 * scale, 0, Math.PI * 2)
    ctx.fill()
    ctx.beginPath()
    ctx.arc(10 * scale, canvas.height - 10 * scale, 50 * scale, 0, Math.PI * 2)
    ctx.fill()
    ctx.restore()

    let dateObj: { day: string; month: string; year: string } | null = null
    try {
      const d = new Date(props.pubDate)
      if (!Number.isNaN(d.getTime())) {
        dateObj = {
          day: d.getDate().toString().padStart(2, '0'),
          month: (d.getMonth() + 1).toString().padStart(2, '0'),
          year: d.getFullYear().toString(),
        }
      }
    } catch {
      dateObj = null
    }

    if (coverImg) {
      const imgRatio = coverImg.width / coverImg.height
      const targetRatio = width / coverHeight
      let sx: number, sy: number, sWidth: number, sHeight: number
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
      ctx.drawImage(coverImg, sx, sy, sWidth, sHeight, 0, 0, width, coverHeight)
    } else {
      ctx.save()
      ctx.fillStyle = themeColor.value
      ctx.globalAlpha = 0.2
      ctx.fillRect(0, 0, width, coverHeight)
      ctx.restore()
    }

    if (dateObj) {
      const dateBoxW = 60 * scale
      const dateBoxH = 60 * scale
      const dateBoxX = padding
      const dateBoxY = coverHeight - dateBoxH

      ctx.fillStyle = 'rgba(0, 0, 0, 0.3)'
      drawRoundedRect(ctx, dateBoxX, dateBoxY, dateBoxW, dateBoxH, 4 * scale)
      ctx.fill()

      ctx.fillStyle = '#ffffff'
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.font = `700 ${30 * scale}px 'Roboto', sans-serif`
      ctx.fillText(dateObj.day, dateBoxX + dateBoxW / 2, dateBoxY + 24 * scale)

      ctx.beginPath()
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.6)'
      ctx.lineWidth = 1 * scale
      ctx.moveTo(dateBoxX + 10 * scale, dateBoxY + 42 * scale)
      ctx.lineTo(dateBoxX + dateBoxW - 10 * scale, dateBoxY + 42 * scale)
      ctx.stroke()

      ctx.font = `${10 * scale}px 'Roboto', sans-serif`
      ctx.fillText(`${dateObj.year} ${dateObj.month}`, dateBoxX + dateBoxW / 2, dateBoxY + 51 * scale)
    }

    let drawY = coverHeight + padding

    ctx.textBaseline = 'top'
    ctx.textAlign = 'left'
    ctx.font = `700 ${24 * scale}px 'Roboto', sans-serif`
    ctx.fillStyle = '#111827'
    titleLines.forEach((line) => {
      ctx.fillText(line, padding, drawY)
      drawY += titleLineHeight
    })
    drawY += 16 * scale - (titleLineHeight - 24 * scale)

    if (props.description) {
      ctx.fillStyle = '#e5e7eb'
      drawRoundedRect(ctx, padding, drawY - 8 * scale, 4 * scale, descHeight + 8 * scale, 2 * scale)
      ctx.fill()

      ctx.font = `${14 * scale}px 'Roboto', sans-serif`
      ctx.fillStyle = '#4b5563'
      const descLines = getLines(ctx, props.description, contentWidth - 16 * scale)
      const maxDescLines = 6
      descLines.slice(0, maxDescLines).forEach((line) => {
        ctx.fillText(line, padding + 16 * scale, drawY)
        drawY += 25 * scale
      })
    } else {
      drawY += 8 * scale
    }

    drawY += 24 * scale
    ctx.beginPath()
    ctx.strokeStyle = '#f3f4f6'
    ctx.lineWidth = 1 * scale
    ctx.moveTo(padding, drawY)
    ctx.lineTo(width - padding, drawY)
    ctx.stroke()
    drawY += 24 * scale

    const footerY = drawY

    if (avatarImg) {
      ctx.save()
      const avatarSize = 64 * scale
      const avatarX = padding
      ctx.beginPath()
      ctx.arc(avatarX + avatarSize / 2, footerY + avatarSize / 2, avatarSize / 2, 0, Math.PI * 2)
      ctx.closePath()
      ctx.clip()
      ctx.drawImage(avatarImg, avatarX, footerY, avatarSize, avatarSize)
      ctx.restore()

      ctx.beginPath()
      ctx.arc(avatarX + (64 * scale) / 2, footerY + (64 * scale) / 2, (64 * scale) / 2, 0, Math.PI * 2)
      ctx.strokeStyle = '#ffffff'
      ctx.lineWidth = 2 * scale
      ctx.stroke()
    }

    const authorTextX = padding + (avatarImg ? 64 * scale + 16 * scale : 0)
    const textCenterY = footerY + 32 * scale

    ctx.fillStyle = '#9ca3af'
    ctx.font = `${12 * scale}px 'Roboto', sans-serif`
    ctx.textAlign = 'left'
    ctx.fillText('作者', authorTextX, textCenterY - 20 * scale)

    ctx.fillStyle = '#1f2937'
    ctx.font = `700 ${20 * scale}px 'Roboto', sans-serif`
    ctx.fillText(props.author, authorTextX, textCenterY + 4 * scale)

    const qrSize = 64 * scale
    const qrX = width - padding - qrSize

    ctx.fillStyle = '#ffffff'
    ctx.shadowColor = 'rgba(0, 0, 0, 0.05)'
    ctx.shadowBlur = 4 * scale
    ctx.shadowOffsetY = 2 * scale
    drawRoundedRect(ctx, qrX, footerY, qrSize, qrSize, 4 * scale)
    ctx.fill()
    ctx.shadowColor = 'transparent'

    const qrInnerSize = 56 * scale
    const qrPadding = (qrSize - qrInnerSize) / 2
    if (qrImg) {
      ctx.drawImage(qrImg, qrX + qrPadding, footerY + qrPadding, qrInnerSize, qrInnerSize)
    }

    const siteInfoX = qrX - 16 * scale
    ctx.textAlign = 'right'

    ctx.fillStyle = '#9ca3af'
    ctx.font = `${12 * scale}px 'Roboto', sans-serif`
    ctx.fillText('扫码阅读', siteInfoX, textCenterY - 20 * scale)

    ctx.fillStyle = '#1f2937'
    ctx.font = `700 ${20 * scale}px 'Roboto', sans-serif`
    ctx.fillText(props.siteTitle, siteInfoX, textCenterY + 4 * scale)

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

function copyLink() {
  navigator.clipboard.writeText(props.url)
  copied.value = true
  setTimeout(() => {
    copied.value = false
  }, 2000)
}

watch(showDialog, (val) => {
  if (!val) {
    posterImage.value = null
    copied.value = false
  }
})
</script>

<template>
  <ElButton
    class="share-poster-btn"
    size="small"
    @click="generatePoster"
  >
    <Icon icon="material-symbols:share" class="share-poster-btn-icon" />
    <span>分享文章</span>
  </ElButton>

  <ElDialog
    v-model="showDialog"
    title="分享海报"
    width="420px"
    align-center
    :close-on-click-modal="true"
  >
    <div class="poster-dialog-body">
      <div class="poster-preview">
        <img v-if="posterImage" :src="posterImage" alt="分享海报" class="poster-img">
        <div v-else class="poster-loading">
          <div class="poster-spinner" :style="{ borderTopColor: themeColor }" />
          <span class="poster-loading-text">正在生成海报...</span>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="poster-dialog-footer">
        <ElButton
          :type="copied ? 'success' : 'default'"
          class="poster-action-btn"
          @click="copyLink"
        >
          <Icon v-if="copied" icon="material-symbols:check" class="poster-action-icon" />
          <Icon v-else icon="material-symbols:link" class="poster-action-icon" />
          <span>{{ copied ? '已复制' : '复制链接' }}</span>
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
    </template>
  </ElDialog>
</template>

<style scoped>
.share-poster-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.share-poster-btn-icon {
  font-size: 1rem;
}

.poster-dialog-body {
  padding: 8px 0;
}

.poster-preview {
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
  border-radius: 12px;
  overflow: hidden;
}

.dark .poster-preview {
  background: #1e293b;
}

.poster-img {
  max-width: 100%;
  height: auto;
  display: block;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.poster-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 40px;
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
  color: #6b7280;
}

.poster-dialog-footer {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.poster-action-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.poster-action-icon {
  font-size: 1rem;
}
</style>
