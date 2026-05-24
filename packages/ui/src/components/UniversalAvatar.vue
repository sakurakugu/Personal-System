<script setup lang="ts">
import { computed } from 'vue';

const props = withDefaults(defineProps<{
  src?: string | null
  text?: string
  alt?: string
  size?: number | string
  background?: string
  color?: string
  border?: string
  fontSize?: number | string
  fontWeight?: number | string
}>(), {
  src: '',
  text: '',
  alt: '头像',
  size: 40,
  background: 'var(--theme-accent-gradient, linear-gradient(135deg, var(--el-color-primary), var(--el-color-primary-light-3)))',
  color: '#ffffff',
  border: 'none',
  fontSize: '',
  fontWeight: 700,
})

function 规范化尺寸(value: number | string) {
  return typeof value === 'number' ? `${value}px` : value
}

const 头像文本 = computed(() => props.text.trim().slice(0, 1).toUpperCase() || 'U')
const 是否有图片 = computed(() => Boolean(props.src?.trim()))
const 根样式 = computed(() => {
  const 尺寸 = 规范化尺寸(props.size)
  const 字号 = props.fontSize
    ? 规范化尺寸(props.fontSize)
    : `calc(${尺寸} * 0.4)`

  return {
    width: 尺寸,
    height: 尺寸,
    minWidth: 尺寸,
    minHeight: 尺寸,
    borderRadius: '50%',
    background: props.background,
    color: props.color,
    border: props.border,
    fontSize: 字号,
    fontWeight: String(props.fontWeight),
  }
})
</script>

<template>
  <div
    class="ps-universal-avatar"
    data-ps-avatar
    :style="根样式"
  >
    <img
      v-if="是否有图片"
      class="ps-universal-avatar__image"
      :src="src || undefined"
      :alt="alt"
      draggable="false"
      referrerpolicy="no-referrer"
    >
    <span v-else class="ps-universal-avatar__text">{{ 头像文本 }}</span>
  </div>
</template>

<style scoped>
.ps-universal-avatar[data-ps-avatar] {
  box-sizing: border-box !important;
  position: relative !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  overflow: hidden !important;
  flex-shrink: 0 !important;
  line-height: 1 !important;
  text-align: center !important;
  vertical-align: middle !important;
  user-select: none !important;
  isolation: isolate !important;
  font-family: var(
    --ps-avatar-font-family,
    "Noto Sans SC",
    "Microsoft YaHei",
    "PingFang SC",
    "Avenir Next",
    "Hiragino Sans GB",
    sans-serif
  ) !important;
  font-variant-ligatures: none !important;
  text-transform: uppercase !important;
  text-rendering: geometricPrecision !important;
  -webkit-font-smoothing: antialiased !important;
  -moz-osx-font-smoothing: grayscale !important;
}

.ps-universal-avatar[data-ps-avatar] > .ps-universal-avatar__image {
  width: 100% !important;
  height: 100% !important;
  display: block !important;
  object-fit: cover !important;
  border-radius: inherit !important;
  flex: none !important;
}

.ps-universal-avatar[data-ps-avatar] > .ps-universal-avatar__text {
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  width: 100% !important;
  height: 100% !important;
  padding: 0 !important;
  margin: 0 !important;
  line-height: 1 !important;
  font: inherit !important;
  letter-spacing: 0.02em !important;
}
</style>
