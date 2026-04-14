import { defineStore } from 'pinia'
import { ref } from 'vue'

export type BlogWallpaperMode = 'banner' | 'overlay' | 'none'
export type BlogNavbarTransparentMode = 'semi' | 'full' | 'semifull'

interface BlogAppearanceSnapshot {
  wallpaperMode?: BlogWallpaperMode
  navbarTransparentMode?: BlogNavbarTransparentMode
  navbarBlurEnabled?: boolean
  navbarBlur?: number
  bannerTitleEnabled?: boolean
  bannerCarouselEnabled?: boolean
  bannerWavesEnabled?: boolean
  overlayOpacity?: number
  overlayBlur?: number
  overlayCardOpacity?: number
}

const STORAGE_KEY = 'blogAppearance'
const DEFAULT_WALLPAPER_MODE: BlogWallpaperMode = 'banner'
const DEFAULT_NAVBAR_TRANSPARENT_MODE: BlogNavbarTransparentMode = 'semi'
const DEFAULT_NAVBAR_BLUR_ENABLED = true
const DEFAULT_NAVBAR_BLUR = 10
const DEFAULT_OVERLAY_OPACITY = 78
const DEFAULT_OVERLAY_BLUR = 18
const DEFAULT_OVERLAY_CARD_OPACITY = 68

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value))
}

function parseBoolean(value: unknown, fallback: boolean) {
  return typeof value === 'boolean' ? value : fallback
}

function parseMode(value: unknown): BlogWallpaperMode {
  return value === 'overlay' || value === 'none' ? value : DEFAULT_WALLPAPER_MODE
}

function parseNavbarTransparentMode(value: unknown): BlogNavbarTransparentMode {
  return value === 'full' || value === 'semifull' ? value : DEFAULT_NAVBAR_TRANSPARENT_MODE
}

export const useBlogAppearanceStore = defineStore('blogAppearance', () => {
  const wallpaperMode = ref<BlogWallpaperMode>(DEFAULT_WALLPAPER_MODE)
  const navbarTransparentMode = ref<BlogNavbarTransparentMode>(DEFAULT_NAVBAR_TRANSPARENT_MODE)
  const navbarBlurEnabled = ref(DEFAULT_NAVBAR_BLUR_ENABLED)
  const navbarBlur = ref(DEFAULT_NAVBAR_BLUR)
  const bannerTitleEnabled = ref(true)
  const bannerCarouselEnabled = ref(true)
  const bannerWavesEnabled = ref(true)
  const overlayOpacity = ref(DEFAULT_OVERLAY_OPACITY)
  const overlayBlur = ref(DEFAULT_OVERLAY_BLUR)
  const overlayCardOpacity = ref(DEFAULT_OVERLAY_CARD_OPACITY)

  function persist() {
    const snapshot: BlogAppearanceSnapshot = {
      wallpaperMode: wallpaperMode.value,
      navbarTransparentMode: navbarTransparentMode.value,
      navbarBlurEnabled: navbarBlurEnabled.value,
      navbarBlur: navbarBlur.value,
      bannerTitleEnabled: bannerTitleEnabled.value,
      bannerCarouselEnabled: bannerCarouselEnabled.value,
      bannerWavesEnabled: bannerWavesEnabled.value,
      overlayOpacity: overlayOpacity.value,
      overlayBlur: overlayBlur.value,
      overlayCardOpacity: overlayCardOpacity.value,
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(snapshot))
  }

  function init() {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) {
      persist()
      return
    }

    try {
      const snapshot = JSON.parse(raw) as BlogAppearanceSnapshot
      wallpaperMode.value = parseMode(snapshot.wallpaperMode)
      navbarTransparentMode.value = parseNavbarTransparentMode(snapshot.navbarTransparentMode)
      navbarBlurEnabled.value = parseBoolean(snapshot.navbarBlurEnabled, DEFAULT_NAVBAR_BLUR_ENABLED)
      navbarBlur.value = clamp(Number(snapshot.navbarBlur ?? DEFAULT_NAVBAR_BLUR), 0, 40)
      bannerTitleEnabled.value = parseBoolean(snapshot.bannerTitleEnabled, true)
      bannerCarouselEnabled.value = parseBoolean(snapshot.bannerCarouselEnabled, true)
      bannerWavesEnabled.value = parseBoolean(snapshot.bannerWavesEnabled, true)
      overlayOpacity.value = clamp(Number(snapshot.overlayOpacity ?? DEFAULT_OVERLAY_OPACITY), 20, 100)
      overlayBlur.value = clamp(Number(snapshot.overlayBlur ?? DEFAULT_OVERLAY_BLUR), 0, 40)
      overlayCardOpacity.value = clamp(Number(snapshot.overlayCardOpacity ?? DEFAULT_OVERLAY_CARD_OPACITY), 35, 100)
    } catch {
      wallpaperMode.value = DEFAULT_WALLPAPER_MODE
      navbarTransparentMode.value = DEFAULT_NAVBAR_TRANSPARENT_MODE
      navbarBlurEnabled.value = DEFAULT_NAVBAR_BLUR_ENABLED
      navbarBlur.value = DEFAULT_NAVBAR_BLUR
      bannerTitleEnabled.value = true
      bannerCarouselEnabled.value = true
      bannerWavesEnabled.value = true
      overlayOpacity.value = DEFAULT_OVERLAY_OPACITY
      overlayBlur.value = DEFAULT_OVERLAY_BLUR
      overlayCardOpacity.value = DEFAULT_OVERLAY_CARD_OPACITY
      persist()
    }
  }

  function setWallpaperMode(mode: BlogWallpaperMode) {
    wallpaperMode.value = mode
    persist()
  }

  function setNavbarTransparentMode(mode: BlogNavbarTransparentMode) {
    navbarTransparentMode.value = mode
    persist()
  }

  function setNavbarBlurEnabled(value: boolean | string | number) {
    navbarBlurEnabled.value = Boolean(value)
    persist()
  }

  function setNavbarBlur(value: number) {
    navbarBlur.value = clamp(Math.round(value), 0, 40)
    persist()
  }

  function setBannerTitleEnabled(value: boolean | string | number) {
    bannerTitleEnabled.value = Boolean(value)
    persist()
  }

  function setBannerCarouselEnabled(value: boolean | string | number) {
    bannerCarouselEnabled.value = Boolean(value)
    persist()
  }

  function setBannerWavesEnabled(value: boolean | string | number) {
    bannerWavesEnabled.value = Boolean(value)
    persist()
  }

  function setOverlayOpacity(value: number) {
    overlayOpacity.value = clamp(Math.round(value), 20, 100)
    persist()
  }

  function setOverlayBlur(value: number) {
    overlayBlur.value = clamp(Math.round(value), 0, 40)
    persist()
  }

  function setOverlayCardOpacity(value: number) {
    overlayCardOpacity.value = clamp(Math.round(value), 35, 100)
    persist()
  }

  return {
    wallpaperMode,
    navbarTransparentMode,
    navbarBlurEnabled,
    navbarBlur,
    bannerTitleEnabled,
    bannerCarouselEnabled,
    bannerWavesEnabled,
    overlayOpacity,
    overlayBlur,
    overlayCardOpacity,
    init,
    setWallpaperMode,
    setNavbarTransparentMode,
    setNavbarBlurEnabled,
    setNavbarBlur,
    setBannerTitleEnabled,
    setBannerCarouselEnabled,
    setBannerWavesEnabled,
    setOverlayOpacity,
    setOverlayBlur,
    setOverlayCardOpacity,
  }
})
