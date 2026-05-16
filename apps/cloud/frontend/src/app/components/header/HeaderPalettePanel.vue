<script setup lang="ts">
import { Icon } from '@iconify/vue'
import { RefreshLeft } from '@element-plus/icons-vue'
import { ElIcon, ElSwitch } from 'element-plus'
import { GlassRangeSlider, ThemeHuePanel } from '@personal-system/ui'
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useBlogAppearanceStore } from '../../../modules/博客/store'
import { useThemeStore } from '../../../shared/stores/theme'
import { 判断是否控制台路由 } from '../../router/route-meta'

const route = useRoute()
const theme = useThemeStore()
const blogAppearance = useBlogAppearanceStore()

const defaultHue = theme.defaultHue
const supportsBlogWallpaperSettings = computed(() => !判断是否控制台路由(route))

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


</script>

<template>
  <div class="palette-settings-panel">
    <!-- 主题色相 -->
    <ThemeHuePanel
      :model-value="theme.hue"
      :default-value="defaultHue"
      :show-preview-row="false"
      @update:model-value="theme.setHue"
    />

    <div class="custom-divider" role="separator" />

    <!-- 屏幕特效 -->
    <div class="click-effect-wrapper">
      <div class="click-effect-header">
        <div class="click-effect-title">
          <span>屏幕特效</span>
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
        <Icon icon="material-symbols:celebration" class="row-icon" />
        <span class="click-effect-label">烟花效果</span>
        <ElSwitch
          :model-value="theme.clickEffectEnabled"
          @update:model-value="theme.setClickEffectEnabled"
        />
      </div>
      <div class="click-effect-switch-row">
        <Icon icon="material-symbols:local-florist" class="row-icon" />
        <span class="click-effect-label">樱花飘落</span>
        <ElSwitch
          :model-value="blogAppearance.sakuraEnabled"
          @update:model-value="blogAppearance.setSakuraEnabled"
        />
      </div>
    </div>

    <template v-if="supportsBlogWallpaperSettings">
      <div class="custom-divider" role="separator" />
      <div class="setting-section">
        <div class="setting-title">
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
          </button>
          <button
            type="button"
            class="wallpaper-mode-option"
            :class="{ active: blogAppearance.wallpaperMode === 'overlay' }"
            @click="setOverlayWallpaperMode"
          >
            <Icon icon="material-symbols:wallpaper" class="option-icon" />
            <span class="option-label">覆盖</span>
          </button>
          <button
            type="button"
            class="wallpaper-mode-option"
            :class="{ active: blogAppearance.wallpaperMode === 'none' }"
            @click="setPlainWallpaperMode"
          >
            <Icon icon="material-symbols:hide-image-outline" class="option-icon" />
            <span class="option-label">纯色</span>
          </button>
        </div>
      </div>

      <template v-if="blogAppearance.wallpaperMode === 'banner'">
        <div class="custom-divider" role="separator" />
        <div class="setting-section">
          <div class="setting-title">
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
            </button>
            <button
              type="button"
              class="wallpaper-mode-option"
              :class="{ active: blogAppearance.navbarTransparentMode === 'full' }"
              @click="setNavbarModeFull"
            >
              <Icon icon="material-symbols:visibility" class="option-icon" />
              <span class="option-label">全透明</span>
            </button>
            <button
              type="button"
              class="wallpaper-mode-option"
              :class="{ active: blogAppearance.navbarTransparentMode === 'semifull' }"
              @click="setNavbarModeSemiFull"
            >
              <Icon icon="material-symbols:motion-photos-auto" class="option-icon" />
              <span class="option-label">动态</span>
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
              <GlassRangeSlider
                :model-value="blogAppearance.navbarBlur"
                :min="0"
                :max="40"
                :step="1"
                aria-label="导航栏模糊度"
                @update:model-value="blogAppearance.setNavbarBlur"
              />
            </div>
          </div>
        </div>
      </template>

      <template v-if="blogAppearance.wallpaperMode === 'overlay'">
        <div class="custom-divider" role="separator" />
        <div class="setting-section">
          <div class="setting-title">
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
              <GlassRangeSlider
                :model-value="blogAppearance.overlayOpacity"
                :min="20"
                :max="100"
                :step="1"
                aria-label="壁纸透明度"
                @update:model-value="blogAppearance.setOverlayOpacity"
              />
            </div>
            <div class="overlay-slider-row">
              <div class="overlay-slider-header">
                <Icon icon="material-symbols:blur-on" class="header-icon" />
                <span>背景模糊</span>
                <span class="overlay-slider-value">{{ blogAppearance.overlayBlur }}px</span>
              </div>
              <GlassRangeSlider
                :model-value="blogAppearance.overlayBlur"
                :min="0"
                :max="40"
                :step="1"
                aria-label="背景模糊"
                @update:model-value="blogAppearance.setOverlayBlur"
              />
            </div>
            <div class="overlay-slider-row">
              <div class="overlay-slider-header">
                <Icon icon="material-symbols:layers" class="header-icon" />
                <span>卡片透明度</span>
                <span class="overlay-slider-value">{{ blogAppearance.overlayCardOpacity }}%</span>
              </div>
              <GlassRangeSlider
                :model-value="blogAppearance.overlayCardOpacity"
                :min="35"
                :max="100"
                :step="1"
                aria-label="卡片透明度"
                @update:model-value="blogAppearance.setOverlayCardOpacity"
              />
            </div>
          </div>
        </div>
      </template>
    </template>

    <div class="custom-divider" role="separator" />

    <!-- 文章布局 -->
    <div class="setting-section">
      <div class="setting-title">
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
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
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
  gap: 8px;
  padding-left: 10px;
}

.click-effect-switch-row.banner-switch-row {
  padding-top: 3px;
  padding-bottom: 3px;
}

.click-effect-label {
  margin-right: auto;
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

.setting-switch-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
  padding-left: 10px;
}

.setting-switch-label {
  font-size: 14px;
  color: rgba(0, 0, 0, 0.72);
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-right: auto;
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
  gap: 12px;
  font-size: 13px;
  color: rgba(0, 0, 0, 0.68);
}

.overlay-slider-value {
  color: var(--header-accent);
  font-weight: 700;
  margin-left: auto;
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

/* Option button with icon (used by wallpaper-mode-option) */
.option-icon {
  width: 1.25rem;
  height: 1.25rem;
  flex-shrink: 0;
}

.option-label {
  flex: none;
  text-align: center;
}

.layout-label {
  flex: none;
  text-align: center;
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

.dark .click-effect-title {
  color: rgba(255, 255, 255, 0.9);
}
.dark .click-effect-title::before {
  background: var(--header-accent-bright);
}
.dark .setting-title {
  color: rgba(255, 255, 255, 0.9);
}
.dark .setting-title::before {
  background: var(--header-accent-bright);
}
.dark .click-effect-label {
  color: rgba(255, 255, 255, 0.7);
}
.dark .setting-switch-label,
.dark .overlay-slider-header {
  color: rgba(255, 255, 255, 0.72);
}
.dark .overlay-slider-value {
  color: var(--header-accent-bright);
}
.dark .wallpaper-mode-option {
  border-color: rgba(255, 255, 255, 0.18);
  color: rgba(255, 255, 255, 0.78);
}
.dark .wallpaper-mode-option:hover {
  border-color: var(--el-color-primary);
  color: var(--el-color-primary-light-5);
}
.dark .wallpaper-mode-option.active {
  border-color: var(--el-color-primary-dark-2);
  background: var(--el-color-primary-dark-2);
  color: var(--el-color-primary-light-9);
}
.dark .hue-reset {
  background: var(--header-accent-surface-dark);
  color: var(--header-accent-bright);
}
.dark .hue-reset:hover {
  background: var(--header-accent-surface-dark-hover);
}
.dark .custom-divider {
  background: rgba(255, 255, 255, 0.08);
}
.dark .layout-switch-option {
  border-color: rgba(255, 255, 255, 0.18);
  color: rgba(255, 255, 255, 0.78);
}
.dark .layout-switch-option:hover {
  border-color: var(--el-color-primary);
  color: var(--el-color-primary-light-5);
}
.dark .layout-switch-option.active {
  border-color: var(--el-color-primary-dark-2);
  background: var(--el-color-primary-dark-2);
  color: var(--el-color-primary-light-9);
}
.dark .option-icon,
.dark .row-icon,
.dark .header-icon {
  color: var(--header-accent-bright);
}
</style>
