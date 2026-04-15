<script setup lang="ts">
import { Icon } from '@iconify/vue'
import { RefreshLeft } from '@element-plus/icons-vue'
import { ElIcon, ElSwitch } from 'element-plus'
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useBlogAppearanceStore } from '../../stores/blog-appearance'
import { useThemeStore } from '../../stores/theme'

const route = useRoute()
const theme = useThemeStore()
const blogAppearance = useBlogAppearanceStore()

const defaultHue = theme.defaultHue
const supportsBlogWallpaperSettings = computed(() => route.path.startsWith('/blog'))
const isExactBlogHome = computed(() => route.path === '/blog' || route.path === '/')

function resetHue() {
  theme.setHue(defaultHue)
}

const defaultClickEffectEnabled = true
function resetClickEffect() {
  theme.setClickEffectEnabled(defaultClickEffectEnabled)
}

function resetWallpaperMode() {
  blogAppearance.setWallpaperMode('banner')
}

function resetBannerContent() {
  blogAppearance.setBannerTitleEnabled(true)
  blogAppearance.setBannerCarouselEnabled(true)
  blogAppearance.setBannerWavesEnabled(true)
}

function resetNavbarStyle() {
  blogAppearance.setNavbarTransparentMode('semi')
  blogAppearance.setNavbarBlurEnabled(true)
  blogAppearance.setNavbarBlur(10)
}

function resetOverlayStyle() {
  blogAppearance.setOverlayOpacity(78)
  blogAppearance.setOverlayBlur(6)
  blogAppearance.setOverlayCardOpacity(68)
}

function setBannerWallpaperMode() {
  blogAppearance.setWallpaperMode('banner')
}

function setOverlayWallpaperMode() {
  blogAppearance.setWallpaperMode('overlay')
}

function setPlainWallpaperMode() {
  blogAppearance.setWallpaperMode('none')
}

function setNavbarModeSemi() {
  blogAppearance.setNavbarTransparentMode('semi')
}

function setNavbarModeFull() {
  blogAppearance.setNavbarTransparentMode('full')
}

function setNavbarModeSemiFull() {
  blogAppearance.setNavbarTransparentMode('semifull')
}

const defaultPostListLayout = 'list'
function resetPostListLayout() {
  blogAppearance.setPostListLayout(defaultPostListLayout)
}

function setListLayout() {
  blogAppearance.setPostListLayout('list')
}

function setGridLayout() {
  blogAppearance.setPostListLayout('grid')
}

function setLightMode() {
  theme.isDark = false
  theme.setFollowSystem(false)
}

function setDarkMode() {
  theme.isDark = true
  theme.setFollowSystem(false)
}
</script>

<template>
  <div class="palette-settings-panel">
    <!-- 主题模式 -->
    <div class="setting-section">
      <div class="setting-title">
        <span>主题模式</span>
        <button
          class="hue-reset"
          :class="{ 'hue-reset-hidden': theme.followSystem }"
          @click="theme.setFollowSystem(true)"
        >
          <ElIcon :size="12"><RefreshLeft /></ElIcon>
        </button>
      </div>
      <div class="theme-mode-options">
        <button
          type="button"
          class="theme-mode-option"
          :class="{ active: !theme.followSystem && !theme.isDark }"
          @click="setLightMode"
        >
          <Icon icon="material-symbols:wb-sunny-outline-rounded" class="option-icon" />
          <span class="option-label">浅色</span>
          <Icon v-if="!theme.followSystem && !theme.isDark" icon="material-symbols:check-circle" class="option-check" />
        </button>
        <button
          type="button"
          class="theme-mode-option"
          :class="{ active: !theme.followSystem && theme.isDark }"
          @click="setDarkMode"
        >
          <Icon icon="material-symbols:dark-mode-outline-rounded" class="option-icon" />
          <span class="option-label">深色</span>
          <Icon v-if="!theme.followSystem && theme.isDark" icon="material-symbols:check-circle" class="option-check" />
        </button>
      </div>
      <div class="follow-system-row">
        <Icon icon="material-symbols:brightness-auto-outline-rounded" class="row-icon" />
        <span class="follow-system-label">跟随系统</span>
        <ElSwitch
          :model-value="theme.followSystem"
          @update:model-value="theme.setFollowSystem"
        />
      </div>
    </div>

    <div class="custom-divider" role="separator" />

    <!-- 主题色相 -->
    <div class="hue-row">
      <div class="hue-header">
        <div class="hue-title">
          <Icon icon="material-symbols:palette" class="title-icon" />
          <span>主题色相</span>
          <button
            class="hue-reset"
            :class="{ 'hue-reset-hidden': theme.hue === defaultHue }"
            @click="resetHue"
          >
            <ElIcon :size="12"><RefreshLeft /></ElIcon>
          </button>
        </div>
        <span class="hue-value">{{ theme.hue }}</span>
      </div>
      <div class="hue-slider-wrapper">
        <div class="hue-slider-track" aria-hidden="true" />
        <input
          type="range"
          min="0"
          max="360"
          step="5"
          :value="theme.hue"
          class="color-slider"
          @input="(event) => theme.setHue(Number((event.target as HTMLInputElement).value))"
        >
      </div>
    </div>

    <div class="custom-divider" role="separator" />

    <!-- 烟花效果 -->
    <div class="click-effect-wrapper">
      <div class="click-effect-header">
        <div class="click-effect-title">
          <Icon icon="material-symbols:celebration" class="title-icon" />
          <span>烟花效果</span>
          <button
            class="hue-reset"
            :class="{ 'hue-reset-hidden': theme.clickEffectEnabled === defaultClickEffectEnabled }"
            @click="resetClickEffect"
          >
            <ElIcon :size="12"><RefreshLeft /></ElIcon>
          </button>
        </div>
      </div>
      <div class="click-effect-switch-row">
        <Icon icon="material-symbols:touch-app" class="row-icon" />
        <span class="click-effect-label">点击特效</span>
        <ElSwitch
          :model-value="theme.clickEffectEnabled"
          @update:model-value="theme.setClickEffectEnabled"
        />
      </div>
    </div>

    <div class="custom-divider" role="separator" />

    <!-- 文章布局 -->
    <div class="setting-section">
      <div class="setting-title">
        <Icon icon="material-symbols:view-quilt" class="title-icon" />
        <span>文章布局</span>
        <button
          class="hue-reset"
          :class="{ 'hue-reset-hidden': blogAppearance.postListLayout === defaultPostListLayout }"
          @click="resetPostListLayout"
        >
          <ElIcon :size="12"><RefreshLeft /></ElIcon>
        </button>
      </div>
      <div class="layout-switch-options">
        <button
          type="button"
          class="layout-switch-option"
          :class="{ active: blogAppearance.postListLayout === 'list' }"
          @click="setListLayout"
        >
          <svg class="layout-icon" fill="currentColor" viewBox="0 0 24 24">
            <path d="M4 6h16v2H4zm0 5h16v2H4zm0 5h16v2H4z" />
          </svg>
          <span class="layout-label">列表</span>
          <Icon v-if="blogAppearance.postListLayout === 'list'" icon="material-symbols:check-circle" class="layout-check" />
        </button>
        <button
          type="button"
          class="layout-switch-option"
          :class="{ active: blogAppearance.postListLayout === 'grid' }"
          @click="setGridLayout"
        >
          <svg class="layout-icon" fill="currentColor" viewBox="0 0 24 24">
            <path d="M3 3h7v7H3V3zm0 11h7v7H3v-7zm11-11h7v7h-7V3zm0 11h7v7h-7v-7z" />
          </svg>
          <span class="layout-label">网格</span>
          <Icon v-if="blogAppearance.postListLayout === 'grid'" icon="material-symbols:check-circle" class="layout-check" />
        </button>
      </div>
    </div>

    <template v-if="supportsBlogWallpaperSettings">
      <div class="custom-divider" role="separator" />
      <div class="setting-section">
        <div class="setting-title">
          <Icon icon="material-symbols:wallpaper" class="title-icon" />
          <span>壁纸模式</span>
          <button
            class="hue-reset"
            :class="{ 'hue-reset-hidden': blogAppearance.wallpaperMode === 'banner' }"
            @click="resetWallpaperMode"
          >
            <ElIcon :size="12"><RefreshLeft /></ElIcon>
          </button>
        </div>
        <div class="wallpaper-mode-options">
          <button
            type="button"
            class="wallpaper-mode-option"
            :class="{ active: blogAppearance.wallpaperMode === 'banner' }"
            @click="setBannerWallpaperMode"
          >
            <Icon icon="material-symbols:image-outline" class="option-icon" />
            <span class="option-label">横幅</span>
            <Icon v-if="blogAppearance.wallpaperMode === 'banner'" icon="material-symbols:check-circle" class="option-check" />
          </button>
          <button
            type="button"
            class="wallpaper-mode-option"
            :class="{ active: blogAppearance.wallpaperMode === 'overlay' }"
            @click="setOverlayWallpaperMode"
          >
            <Icon icon="material-symbols:wallpaper" class="option-icon" />
            <span class="option-label">覆盖</span>
            <Icon v-if="blogAppearance.wallpaperMode === 'overlay'" icon="material-symbols:check-circle" class="option-check" />
          </button>
          <button
            type="button"
            class="wallpaper-mode-option"
            :class="{ active: blogAppearance.wallpaperMode === 'none' }"
            @click="setPlainWallpaperMode"
          >
            <Icon icon="material-symbols:hide-image-outline" class="option-icon" />
            <span class="option-label">纯色</span>
            <Icon v-if="blogAppearance.wallpaperMode === 'none'" icon="material-symbols:check-circle" class="option-check" />
          </button>
        </div>
      </div>

      <template v-if="blogAppearance.wallpaperMode === 'banner'">
        <div class="custom-divider" role="separator" />
        <div class="setting-section">
          <div class="setting-title">
            <Icon icon="material-symbols:view-carousel-outline" class="title-icon" />
            <span>首页横幅</span>
            <button
              class="hue-reset"
              :class="{ 'hue-reset-hidden':
                blogAppearance.bannerTitleEnabled === true &&
                blogAppearance.bannerCarouselEnabled === true &&
                blogAppearance.bannerWavesEnabled === true
              }"
              @click="resetBannerContent"
            >
              <ElIcon :size="12"><RefreshLeft /></ElIcon>
            </button>
          </div>
          <div class="click-effect-switch-row banner-switch-row">
            <Icon icon="material-symbols:titlecase-rounded" class="row-icon" />
            <span class="click-effect-label">首页标题</span>
            <ElSwitch
              :model-value="blogAppearance.bannerTitleEnabled"
              @update:model-value="blogAppearance.setBannerTitleEnabled"
            />
          </div>
          <div v-if="!isExactBlogHome" class="setting-helper-text">
            当前页面不是首页，此开关仅作用于 `/blog` 首页横幅标题。
          </div>
          <div class="click-effect-switch-row banner-switch-row">
            <Icon icon="material-symbols:view-carousel-outline" class="row-icon" />
            <span class="click-effect-label">图片轮播</span>
            <ElSwitch
              :model-value="blogAppearance.bannerCarouselEnabled"
              @update:model-value="blogAppearance.setBannerCarouselEnabled"
            />
          </div>
          <div class="click-effect-switch-row banner-switch-row">
            <Icon icon="material-symbols:airwave-rounded" class="row-icon" />
            <span class="click-effect-label">水波纹</span>
            <ElSwitch
              :model-value="blogAppearance.bannerWavesEnabled"
              @update:model-value="blogAppearance.setBannerWavesEnabled"
            />
          </div>

          <div class="custom-divider" role="separator" />
          <div class="setting-title">
            <Icon icon="material-symbols:menu-open" class="title-icon" />
            <span>导航栏样式</span>
            <button
              class="hue-reset"
              :class="{ 'hue-reset-hidden':
                blogAppearance.navbarTransparentMode === 'semi' &&
                blogAppearance.navbarBlurEnabled === true &&
                blogAppearance.navbarBlur === 10
              }"
              @click="resetNavbarStyle"
            >
              <ElIcon :size="12"><RefreshLeft /></ElIcon>
            </button>
          </div>
          <div class="wallpaper-mode-options">
            <button
              type="button"
              class="wallpaper-mode-option"
              :class="{ active: blogAppearance.navbarTransparentMode === 'semi' }"
              @click="setNavbarModeSemi"
            >
              <Icon icon="material-symbols:opacity" class="option-icon" />
              <span class="option-label">半透明</span>
              <Icon v-if="blogAppearance.navbarTransparentMode === 'semi'" icon="material-symbols:check-circle" class="option-check" />
            </button>
            <button
              type="button"
              class="wallpaper-mode-option"
              :class="{ active: blogAppearance.navbarTransparentMode === 'full' }"
              @click="setNavbarModeFull"
            >
              <Icon icon="material-symbols:visibility" class="option-icon" />
              <span class="option-label">全透明</span>
              <Icon v-if="blogAppearance.navbarTransparentMode === 'full'" icon="material-symbols:check-circle" class="option-check" />
            </button>
            <button
              type="button"
              class="wallpaper-mode-option"
              :class="{ active: blogAppearance.navbarTransparentMode === 'semifull' }"
              @click="setNavbarModeSemiFull"
            >
              <Icon icon="material-symbols:motion-photos-auto" class="option-icon" />
              <span class="option-label">动态</span>
              <Icon v-if="blogAppearance.navbarTransparentMode === 'semifull'" icon="material-symbols:check-circle" class="option-check" />
            </button>
          </div>
          <div class="setting-switch-row">
            <Icon icon="material-symbols:blur-on" class="row-icon" />
            <span class="setting-switch-label">毛玻璃</span>
            <ElSwitch
              :model-value="blogAppearance.navbarBlurEnabled"
              @update:model-value="blogAppearance.setNavbarBlurEnabled"
            />
          </div>
          <div v-if="blogAppearance.navbarBlurEnabled" class="overlay-slider-list overlay-slider-list--compact">
            <div class="overlay-slider-row">
              <div class="overlay-slider-header">
                <Icon icon="material-symbols:tune" class="header-icon" />
                <span>模糊度</span>
                <span class="overlay-slider-value">{{ blogAppearance.navbarBlur }}px</span>
              </div>
              <input
                type="range"
                min="0"
                max="40"
                step="1"
                :value="blogAppearance.navbarBlur"
                class="setting-range"
                @input="(event) => blogAppearance.setNavbarBlur(Number((event.target as HTMLInputElement).value))"
              >
            </div>
          </div>
        </div>
      </template>

      <template v-if="blogAppearance.wallpaperMode === 'overlay'">
        <div class="custom-divider" role="separator" />
        <div class="setting-section">
          <div class="setting-title">
            <Icon icon="material-symbols:format-paint" class="title-icon" />
            <span>背景样式</span>
            <button
              class="hue-reset"
              :class="{ 'hue-reset-hidden':
                blogAppearance.overlayOpacity === 78 &&
                blogAppearance.overlayBlur === 6 &&
                blogAppearance.overlayCardOpacity === 68
              }"
              @click="resetOverlayStyle"
            >
              <ElIcon :size="12"><RefreshLeft /></ElIcon>
            </button>
          </div>
          <div class="overlay-slider-list">
            <div class="overlay-slider-row">
              <div class="overlay-slider-header">
                <Icon icon="material-symbols:opacity" class="header-icon" />
                <span>壁纸透明度</span>
                <span class="overlay-slider-value">{{ blogAppearance.overlayOpacity }}%</span>
              </div>
              <input
                type="range"
                min="20"
                max="100"
                step="1"
                :value="blogAppearance.overlayOpacity"
                class="setting-range"
                @input="(event) => blogAppearance.setOverlayOpacity(Number((event.target as HTMLInputElement).value))"
              >
            </div>
            <div class="overlay-slider-row">
              <div class="overlay-slider-header">
                <Icon icon="material-symbols:blur-on" class="header-icon" />
                <span>背景模糊</span>
                <span class="overlay-slider-value">{{ blogAppearance.overlayBlur }}px</span>
              </div>
              <input
                type="range"
                min="0"
                max="40"
                step="1"
                :value="blogAppearance.overlayBlur"
                class="setting-range"
                @input="(event) => blogAppearance.setOverlayBlur(Number((event.target as HTMLInputElement).value))"
              >
            </div>
            <div class="overlay-slider-row">
              <div class="overlay-slider-header">
                <Icon icon="material-symbols:layers" class="header-icon" />
                <span>卡片透明度</span>
                <span class="overlay-slider-value">{{ blogAppearance.overlayCardOpacity }}%</span>
              </div>
              <input
                type="range"
                min="35"
                max="100"
                step="1"
                :value="blogAppearance.overlayCardOpacity"
                class="setting-range"
                @input="(event) => blogAppearance.setOverlayCardOpacity(Number((event.target as HTMLInputElement).value))"
              >
            </div>
          </div>
        </div>
      </template>
    </template>
  </div>
</template>

<style scoped>
.hue-row {
  padding: 0;
}

.hue-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.hue-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 700;
  color: rgba(0, 0, 0, 0.9);
  position: relative;
  margin-left: 12px;
}

.hue-title::before {
  content: '';
  position: absolute;
  left: -12px;
  top: 50%;
  transform: translateY(-50%);
  width: 4px;
  height: 16px;
  border-radius: 4px;
  background: var(--header-accent-soft);
}

.hue-reset {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  padding: 0;
  border: none;
  border-radius: 6px;
  background: var(--header-accent-surface);
  color: var(--header-accent);
  cursor: pointer;
  transition: opacity 0.2s, background 0.15s;
}

.hue-reset:hover {
  background: var(--header-accent-surface-hover);
}

.hue-reset:active {
  transform: scale(0.9);
}

.hue-reset-hidden {
  opacity: 0;
  pointer-events: none;
}

.hue-value {
  font-size: 14px;
  font-weight: 700;
  width: 40px;
  height: 28px;
  border-radius: 6px;
  background: var(--header-accent-surface);
  color: var(--header-accent);
  display: flex;
  align-items: center;
  justify-content: center;
}

.hue-slider-wrapper {
  --slider-edge-gap: 5px;
  --slider-edge-color: oklch(0.80 0.10 0);
  position: relative;
  width: 100%;
  height: 24px;
  border-radius: 4px;
}

.hue-slider-track {
  position: absolute;
  inset: 0;
  border-radius: 4px;
  background:
    linear-gradient(var(--slider-edge-color), var(--slider-edge-color)) left center / var(--slider-edge-gap) 100% no-repeat,
    var(--color-selection-bar) center / calc(100% - (var(--slider-edge-gap) * 2)) 100% no-repeat,
    linear-gradient(var(--slider-edge-color), var(--slider-edge-color)) right center / var(--slider-edge-gap) 100% no-repeat;
  pointer-events: none;
}

.color-slider {
  position: absolute;
  top: 0;
  right: var(--slider-edge-gap);
  bottom: 0;
  left: var(--slider-edge-gap);
  -webkit-appearance: none;
  appearance: none;
  width: auto;
  height: 100%;
  border-radius: 4px;
  background: transparent;
  outline: none;
  cursor: pointer;
}

.color-slider::-webkit-slider-runnable-track {
  height: 100%;
  background: transparent;
  border: none;
}

.color-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 8px;
  height: 16px;
  margin-top: 4px;
  border-radius: 2px;
  background: rgba(255, 255, 255, 0.7);
  border: none;
  box-shadow: none;
}

.color-slider::-webkit-slider-thumb:hover {
  background: rgba(255, 255, 255, 0.85);
}

.color-slider::-webkit-slider-thumb:active {
  background: rgba(255, 255, 255, 0.6);
}

.color-slider::-moz-range-thumb {
  width: 8px;
  height: 16px;
  border: none;
  border-radius: 2px;
  background: rgba(255, 255, 255, 0.7);
  box-shadow: none;
}

.color-slider::-moz-range-thumb:hover {
  background: rgba(255, 255, 255, 0.85);
}

.color-slider::-moz-range-thumb:active {
  background: rgba(255, 255, 255, 0.6);
}

.color-slider::-moz-range-track,
.color-slider::-moz-range-progress {
  height: 100%;
  background: transparent;
  border: none;
}

.custom-divider {
  height: 1px;
  background: var(--el-border-color-light);
  margin: 8px 0;
}

.click-effect-wrapper {
  padding: 0;
}

.click-effect-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.click-effect-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 700;
  color: rgba(0, 0, 0, 0.9);
  position: relative;
  margin-left: 12px;
}

.click-effect-title::before {
  content: '';
  position: absolute;
  left: -12px;
  top: 50%;
  transform: translateY(-50%);
  width: 4px;
  height: 16px;
  border-radius: 4px;
  background: var(--header-accent-soft);
}

.click-effect-switch-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-left: 12px;
}

.click-effect-switch-row.banner-switch-row {
  padding-top: 3px;
  padding-bottom: 3px;
}

.click-effect-label {
  font-size: 14px;
  color: rgba(0, 0, 0, 0.7);
}

.setting-section {
  padding: 0;
}

.setting-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 700;
  color: rgba(0, 0, 0, 0.9);
  position: relative;
  margin-left: 12px;
  margin-bottom: 12px;
}

.setting-title::before {
  content: '';
  position: absolute;
  left: -12px;
  top: 50%;
  transform: translateY(-50%);
  width: 4px;
  height: 16px;
  border-radius: 4px;
  background: var(--header-accent-soft);
}

.wallpaper-mode-options {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  margin-bottom: 12px;
}

.wallpaper-mode-option {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 36px;
  border: 1px solid var(--el-border-color);
  border-radius: 10px;
  background: transparent;
  color: rgba(0, 0, 0, 0.72);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.wallpaper-mode-option:hover {
  border-color: var(--el-color-primary);
  color: var(--el-color-primary);
}

.wallpaper-mode-option.active {
  border-color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
}

.setting-switch-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 8px 0;
  padding-left: 12px;
}

.setting-switch-label {
  font-size: 14px;
  color: rgba(0, 0, 0, 0.72);
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.setting-helper-text {
  margin-top: -2px;
  margin-bottom: 8px;
  font-size: 12px;
  line-height: 1.6;
  color: rgba(0, 0, 0, 0.52);
}

.overlay-slider-list {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding-left: 12px;
}

.overlay-slider-list--compact {
  margin-top: 0;
  gap: 8px;
}

.overlay-slider-row {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.overlay-slider-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  font-size: 13px;
  color: rgba(0, 0, 0, 0.68);
}

.overlay-slider-value {
  color: var(--header-accent);
  font-weight: 700;
}

.setting-range {
  -webkit-appearance: none;
  appearance: none;
  width: 100%;
  height: 14px;
  border-radius: 999px;
  background: transparent;
}

.setting-range:hover {
  cursor: pointer;
}

.setting-range::-webkit-slider-runnable-track {
  height: 14px;
  border: 1px solid rgba(148, 163, 184, 0.22);
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.18);
  backdrop-filter: blur(10px) saturate(140%);
  -webkit-backdrop-filter: blur(10px) saturate(140%);
}

.setting-range::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 18px;
  height: 18px;
  margin-top: -3px;
  border: 1px solid rgba(148, 163, 184, 0.45);
  border-radius: 50%;
  background: rgba(241, 245, 249, 0.96);
  box-shadow: 0 4px 14px rgba(15, 23, 42, 0.14);
}

.setting-range::-webkit-slider-thumb:hover {
  background: rgba(226, 232, 240, 0.98);
}

.setting-range::-moz-range-track {
  height: 14px;
  border: 1px solid rgba(148, 163, 184, 0.22);
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.18);
}

.setting-range::-moz-range-thumb {
  width: 18px;
  height: 18px;
  border: 1px solid rgba(148, 163, 184, 0.45);
  border-radius: 50%;
  background: rgba(241, 245, 249, 0.96);
  box-shadow: 0 4px 14px rgba(15, 23, 42, 0.14);
}

:global(.dark) .hue-title {
  color: rgba(255, 255, 255, 0.9);
}

:global(.dark) .hue-title::before {
  background: var(--header-accent-bright);
}

:global(.dark) .click-effect-title {
  color: rgba(255, 255, 255, 0.9);
}

:global(.dark) .click-effect-title::before {
  background: var(--header-accent-bright);
}

:global(.dark) .setting-title {
  color: rgba(255, 255, 255, 0.9);
}

:global(.dark) .setting-title::before {
  background: var(--header-accent-bright);
}

:global(.dark) .click-effect-label {
  color: rgba(255, 255, 255, 0.7);
}

:global(.dark) .setting-switch-label,
:global(.dark) .overlay-slider-header {
  color: rgba(255, 255, 255, 0.72);
}

:global(.dark) .setting-helper-text {
  color: rgba(255, 255, 255, 0.5);
}

:global(.dark) .overlay-slider-value {
  color: var(--header-accent-bright);
}

:global(.dark) .wallpaper-mode-option {
  border-color: rgba(255, 255, 255, 0.18);
  color: rgba(255, 255, 255, 0.78);
}

:global(.dark) .wallpaper-mode-option:hover {
  border-color: var(--el-color-primary);
  color: var(--el-color-primary-light-5);
}

:global(.dark) .wallpaper-mode-option.active {
  border-color: var(--el-color-primary-dark-2);
  background: var(--el-color-primary-dark-2);
  color: var(--el-color-primary-light-9);
}

:global(.dark) .hue-reset {
  background: var(--header-accent-surface-dark);
  color: var(--header-accent-bright);
}

:global(.dark) .hue-reset:hover {
  background: var(--header-accent-surface-dark-hover);
}

:global(.dark) .hue-value {
  background: var(--header-accent-surface-dark);
  color: var(--header-accent-bright);
}

:global(.dark) .custom-divider {
  background: rgba(255, 255, 255, 0.08);
}

:global(.dark) .setting-range::-webkit-slider-runnable-track {
  border-color: rgba(255, 255, 255, 0.14);
  background: rgba(255, 255, 255, 0.16);
}

:global(.dark) .setting-range::-webkit-slider-thumb {
  border-color: rgba(255, 255, 255, 0.34);
  background: rgba(255, 255, 255, 0.52);
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.28);
}

:global(.dark) .setting-range::-webkit-slider-thumb:hover {
  background: rgba(255, 255, 255, 0.64);
}

:global(.dark) .setting-range::-moz-range-track {
  border-color: rgba(255, 255, 255, 0.14);
  background: rgba(255, 255, 255, 0.16);
}

:global(.dark) .setting-range::-moz-range-thumb {
  border-color: rgba(255, 255, 255, 0.34);
  background: rgba(255, 255, 255, 0.52);
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.28);
}

:global(.dark) .hue-slider-wrapper {
  --slider-edge-color: oklch(0.70 0.10 0);
}

.layout-switch-options {
  display: flex;
  gap: 8px;
}

.layout-switch-option {
  flex: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  height: 36px;
  border: 1px solid var(--el-border-color);
  border-radius: 10px;
  background: transparent;
  color: rgba(0, 0, 0, 0.72);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  padding: 0 12px;
  opacity: 0.6;
}

.layout-switch-option:hover {
  border-color: var(--el-color-primary);
  color: var(--el-color-primary);
  opacity: 1;
}

.layout-switch-option.active {
  border-color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  opacity: 1;
}

.layout-icon {
  width: 1rem;
  height: 1rem;
  flex-shrink: 0;
}

.layout-check {
  width: 1rem;
  height: 1rem;
  flex-shrink: 0;
}

:global(.dark) .layout-switch-option {
  border-color: rgba(255, 255, 255, 0.18);
  color: rgba(255, 255, 255, 0.78);
}

:global(.dark) .layout-switch-option:hover {
  border-color: var(--el-color-primary);
  color: var(--el-color-primary-light-5);
}

:global(.dark) .layout-switch-option.active {
  border-color: var(--el-color-primary-dark-2);
  background: var(--el-color-primary-dark-2);
  color: var(--el-color-primary-light-9);
}

.title-icon {
  width: 1.25rem;
  height: 1.25rem;
  flex-shrink: 0;
  color: var(--header-accent);
}

.row-icon {
  width: 1.25rem;
  height: 1.25rem;
  flex-shrink: 0;
  color: var(--header-accent);
}

.header-icon {
  width: 1rem;
  height: 1rem;
  flex-shrink: 0;
  color: var(--header-accent);
}

/* Theme mode options */
.theme-mode-options {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.theme-mode-option {
  flex: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  height: 36px;
  border: 1px solid var(--el-border-color);
  border-radius: 10px;
  background: transparent;
  color: rgba(0, 0, 0, 0.72);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  padding: 0 12px;
  opacity: 0.6;
}

.theme-mode-option:hover {
  border-color: var(--el-color-primary);
  color: var(--el-color-primary);
  opacity: 1;
}

.theme-mode-option.active {
  border-color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  opacity: 1;
}

.follow-system-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 8px 0;
  padding-left: 12px;
}

.follow-system-label {
  flex: 1;
  font-size: 14px;
  color: rgba(0, 0, 0, 0.72);
}

/* Option button with icon (used by wallpaper-mode-option and theme-mode-option) */
.option-icon {
  width: 1.25rem;
  height: 1.25rem;
  flex-shrink: 0;
}

.option-check {
  width: 1rem;
  height: 1rem;
  flex-shrink: 0;
}

.option-label {
  flex: 1;
  text-align: left;
}

.wallpaper-mode-option {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  height: 36px;
  border: 1px solid var(--el-border-color);
  border-radius: 10px;
  background: transparent;
  color: rgba(0, 0, 0, 0.72);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  padding: 0 10px;
  opacity: 0.6;
}

.wallpaper-mode-option:hover {
  border-color: var(--el-color-primary);
  color: var(--el-color-primary);
  opacity: 1;
}

.wallpaper-mode-option.active {
  border-color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  opacity: 1;
}

:global(.dark) .theme-mode-option {
  border-color: rgba(255, 255, 255, 0.18);
  color: rgba(255, 255, 255, 0.78);
}

:global(.dark) .theme-mode-option:hover {
  border-color: var(--el-color-primary);
  color: var(--el-color-primary-light-5);
}

:global(.dark) .theme-mode-option.active {
  border-color: var(--el-color-primary-dark-2);
  background: var(--el-color-primary-dark-2);
  color: var(--el-color-primary-light-9);
}

:global(.dark) .follow-system-label {
  color: rgba(255, 255, 255, 0.72);
}

:global(.dark) .option-icon,
:global(.dark) .row-icon,
:global(.dark) .header-icon,
:global(.dark) .title-icon {
  color: var(--header-accent-bright);
}
</style>
