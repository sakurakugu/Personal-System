import { defineStore } from 'pinia'
import { ref } from 'vue'

export type BlogWallpaperMode = 'banner' | 'overlay' | 'none'
export type BlogNavbarTransparentMode = 'semi' | 'full' | 'semifull'
export type BlogPostListLayout = 'list' | 'grid'

interface BlogAppearanceSnapshot {
  wallpaperMode?: BlogWallpaperMode
  navbarTransparentMode?: BlogNavbarTransparentMode
  navbarBlurEnabled?: boolean
  navbarBlur?: number
  bannerTitleEnabled?: boolean
  bannerCarouselEnabled?: boolean
  bannerWavesEnabled?: boolean
  sakuraEnabled?: boolean
  overlayOpacity?: number
  overlayBlur?: number
  overlayCardOpacity?: number
  postListLayout?: BlogPostListLayout
}

const STORAGE_KEY = 'blogAppearance'
const DEFAULT_WALLPAPER_MODE: BlogWallpaperMode = 'banner'
const DEFAULT_NAVBAR_TRANSPARENT_MODE: BlogNavbarTransparentMode = 'semi'
const DEFAULT_NAVBAR_BLUR_ENABLED = true
const DEFAULT_NAVBAR_BLUR = 10
const DEFAULT_OVERLAY_OPACITY = 78
const DEFAULT_OVERLAY_BLUR = 6
const DEFAULT_OVERLAY_CARD_OPACITY = 68
const DEFAULT_POST_LIST_LAYOUT: BlogPostListLayout = 'list'
const DEFAULT_SAKURA_ENABLED = false

function 限制范围(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value))
}

function 解析布尔值(value: unknown, fallback: boolean) {
  return typeof value === 'boolean' ? value : fallback
}

function 解析壁纸模式(value: unknown): BlogWallpaperMode {
  return value === 'overlay' || value === 'none' ? value : DEFAULT_WALLPAPER_MODE
}

function 解析导航栏透明模式(value: unknown): BlogNavbarTransparentMode {
  return value === 'full' || value === 'semifull' ? value : DEFAULT_NAVBAR_TRANSPARENT_MODE
}

export const 使用博客外观存储 = defineStore('blogAppearance', () => {
  const wallpaperMode = ref<BlogWallpaperMode>(DEFAULT_WALLPAPER_MODE)
  const navbarTransparentMode = ref<BlogNavbarTransparentMode>(DEFAULT_NAVBAR_TRANSPARENT_MODE)
  const navbarBlurEnabled = ref(DEFAULT_NAVBAR_BLUR_ENABLED)
  const navbarBlur = ref(DEFAULT_NAVBAR_BLUR)
  const bannerTitleEnabled = ref(true)
  const bannerCarouselEnabled = ref(true)
  const bannerWavesEnabled = ref(true)
  const sakuraEnabled = ref(DEFAULT_SAKURA_ENABLED)
  const overlayOpacity = ref(DEFAULT_OVERLAY_OPACITY)
  const overlayBlur = ref(DEFAULT_OVERLAY_BLUR)
  const overlayCardOpacity = ref(DEFAULT_OVERLAY_CARD_OPACITY)
  const postListLayout = ref<BlogPostListLayout>(DEFAULT_POST_LIST_LAYOUT)

  function 持久化() {
    const snapshot: BlogAppearanceSnapshot = {
      wallpaperMode: wallpaperMode.value,
      navbarTransparentMode: navbarTransparentMode.value,
      navbarBlurEnabled: navbarBlurEnabled.value,
      navbarBlur: navbarBlur.value,
      bannerTitleEnabled: bannerTitleEnabled.value,
      bannerCarouselEnabled: bannerCarouselEnabled.value,
      bannerWavesEnabled: bannerWavesEnabled.value,
      sakuraEnabled: sakuraEnabled.value,
      overlayOpacity: overlayOpacity.value,
      overlayBlur: overlayBlur.value,
      overlayCardOpacity: overlayCardOpacity.value,
      postListLayout: postListLayout.value,
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(snapshot))
  }

  function 初始化() {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) {
      持久化()
      return
    }

    try {
      const snapshot = JSON.parse(raw) as BlogAppearanceSnapshot
      wallpaperMode.value = 解析壁纸模式(snapshot.wallpaperMode)
      navbarTransparentMode.value = 解析导航栏透明模式(snapshot.navbarTransparentMode)
      navbarBlurEnabled.value = 解析布尔值(snapshot.navbarBlurEnabled, DEFAULT_NAVBAR_BLUR_ENABLED)
      navbarBlur.value = 限制范围(Number(snapshot.navbarBlur ?? DEFAULT_NAVBAR_BLUR), 0, 40)
      bannerTitleEnabled.value = 解析布尔值(snapshot.bannerTitleEnabled, true)
      bannerCarouselEnabled.value = 解析布尔值(snapshot.bannerCarouselEnabled, true)
      bannerWavesEnabled.value = 解析布尔值(snapshot.bannerWavesEnabled, true)
      sakuraEnabled.value = 解析布尔值(snapshot.sakuraEnabled, DEFAULT_SAKURA_ENABLED)
      overlayOpacity.value = 限制范围(Number(snapshot.overlayOpacity ?? DEFAULT_OVERLAY_OPACITY), 20, 100)
      overlayBlur.value = 限制范围(Number(snapshot.overlayBlur ?? DEFAULT_OVERLAY_BLUR), 0, 40)
      overlayCardOpacity.value = 限制范围(Number(snapshot.overlayCardOpacity ?? DEFAULT_OVERLAY_CARD_OPACITY), 35, 100)
      postListLayout.value = (snapshot.postListLayout === 'grid' ? 'grid' : DEFAULT_POST_LIST_LAYOUT)
    } catch {
      wallpaperMode.value = DEFAULT_WALLPAPER_MODE
      navbarTransparentMode.value = DEFAULT_NAVBAR_TRANSPARENT_MODE
      navbarBlurEnabled.value = DEFAULT_NAVBAR_BLUR_ENABLED
      navbarBlur.value = DEFAULT_NAVBAR_BLUR
      bannerTitleEnabled.value = true
      bannerCarouselEnabled.value = true
      bannerWavesEnabled.value = true
      sakuraEnabled.value = DEFAULT_SAKURA_ENABLED
      overlayOpacity.value = DEFAULT_OVERLAY_OPACITY
      overlayBlur.value = DEFAULT_OVERLAY_BLUR
      overlayCardOpacity.value = DEFAULT_OVERLAY_CARD_OPACITY
      postListLayout.value = DEFAULT_POST_LIST_LAYOUT
      持久化()
    }
  }

  function 设置壁纸模式(mode: BlogWallpaperMode) {
    wallpaperMode.value = mode
    持久化()
  }

  function 设置导航栏透明模式(mode: BlogNavbarTransparentMode) {
    navbarTransparentMode.value = mode
    持久化()
  }

  function 设置导航栏模糊启用(value: boolean | string | number) {
    navbarBlurEnabled.value = Boolean(value)
    持久化()
  }

  function 设置导航栏模糊度(value: number) {
    navbarBlur.value = 限制范围(Math.round(value), 0, 40)
    持久化()
  }

  function 设置横幅标题启用(value: boolean | string | number) {
    bannerTitleEnabled.value = Boolean(value)
    持久化()
  }

  function 设置横幅轮播启用(value: boolean | string | number) {
    bannerCarouselEnabled.value = Boolean(value)
    持久化()
  }

  function 设置横幅波浪启用(value: boolean | string | number) {
    bannerWavesEnabled.value = Boolean(value)
    持久化()
  }

  function 设置樱花启用(value: boolean | string | number) {
    sakuraEnabled.value = Boolean(value)
    持久化()
  }

  function 设置叠加层不透明度(value: number) {
    overlayOpacity.value = 限制范围(Math.round(value), 20, 100)
    持久化()
  }

  function 设置叠加层模糊度(value: number) {
    overlayBlur.value = 限制范围(Math.round(value), 0, 40)
    持久化()
  }

  function 设置叠加层卡片不透明度(value: number) {
    overlayCardOpacity.value = 限制范围(Math.round(value), 35, 100)
    持久化()
  }

  function 设置文章列表布局(value: BlogPostListLayout) {
    postListLayout.value = value
    持久化()
  }

  return {
    wallpaperMode,
    navbarTransparentMode,
    navbarBlurEnabled,
    navbarBlur,
    bannerTitleEnabled,
    bannerCarouselEnabled,
    bannerWavesEnabled,
    sakuraEnabled,
    overlayOpacity,
    overlayBlur,
    overlayCardOpacity,
    postListLayout,
    init: 初始化,
    setWallpaperMode: 设置壁纸模式,
    setNavbarTransparentMode: 设置导航栏透明模式,
    setNavbarBlurEnabled: 设置导航栏模糊启用,
    setNavbarBlur: 设置导航栏模糊度,
    setBannerTitleEnabled: 设置横幅标题启用,
    setBannerCarouselEnabled: 设置横幅轮播启用,
    setBannerWavesEnabled: 设置横幅波浪启用,
    setSakuraEnabled: 设置樱花启用,
    setOverlayOpacity: 设置叠加层不透明度,
    setOverlayBlur: 设置叠加层模糊度,
    setOverlayCardOpacity: 设置叠加层卡片不透明度,
    setPostListLayout: 设置文章列表布局,
  }
})
