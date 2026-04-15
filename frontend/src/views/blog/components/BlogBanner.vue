<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useBannerImages } from '../../../composables/useBannerImages'
import { useArticleStore } from '../../../stores/article'
import { useBlogAppearanceStore } from '../../../stores/blog-appearance'

const appearance = useBlogAppearanceStore()
const articleStore = useArticleStore()
const route = useRoute()

const articleSlug = computed(() => {
  const slug = route.params.slug
  return typeof slug === 'string' ? slug : ''
})

const isBannerMode = computed(() => appearance.wallpaperMode === 'banner')
const hasWallpaper = computed(() => appearance.wallpaperMode !== 'none')

/* ==================== Banner 轮播 ==================== */
const { images: bannerImages } = useBannerImages()
const currentBannerIndex = ref(0)
let bannerTimer: number | null = null

function stopBannerCarousel() {
  if (bannerTimer !== null) {
    window.clearInterval(bannerTimer)
    bannerTimer = null
  }
}

function startBannerCarousel() {
  stopBannerCarousel()
  if (!appearance.bannerCarouselEnabled || !hasWallpaper.value || bannerImages.value.length <= 1) return

  bannerTimer = window.setInterval(() => {
    if (bannerImages.value.length === 0) return
    currentBannerIndex.value = (currentBannerIndex.value + 1) % bannerImages.value.length
  }, 6000)
}

onMounted(() => {
  startBannerCarousel()
})

watch(
  [bannerImages, () => appearance.bannerCarouselEnabled, () => appearance.wallpaperMode],
  () => {
    if (currentBannerIndex.value >= bannerImages.value.length) {
      currentBannerIndex.value = 0
    }
    startBannerCarousel()
  },
)

onUnmounted(() => {
  stopBannerCarousel()
})

/* ==================== Typewriter 打字机效果 (Firefly 风格) ==================== */
const defaultTypewriterTexts = [
  '欢迎来到我的小窝',
  '记录生活，分享技术',
  '愿每一天都充满阳光',
]
const typewriterTexts = computed(() => {
  if (articleSlug.value && articleStore.current) {
    return [articleStore.current.title]
  }
  return defaultTypewriterTexts
})
const typewriterDisplay = ref('')
let typewriterInstance: TypewriterEffect | null = null

class TypewriterEffect {
  private texts: string[]
  private currentTextIndex: number = 0
  private currentIndex: number = 0
  private isDeleting: boolean = false
  private timeoutId: number | null = null
  private speed: number
  private deleteSpeed: number
  private pauseTime: number

  constructor(texts: string[], displayRef: { value: string }, speed = 100, deleteSpeed = 50, pauseTime = 2000) {
    this.texts = texts
    this.speed = speed
    this.deleteSpeed = deleteSpeed
    this.pauseTime = pauseTime
    this.displayRef = displayRef
    this.start()
  }

  private displayRef: { value: string }

  private start() {
    if (this.texts.length === 0) return
    this.type()
  }

  private getCurrentText(): string {
    return this.texts[this.currentTextIndex] || ''
  }

  private type() {
    const currentText = this.getCurrentText()
    const segments = this.segmentText(currentText)

    if (this.isDeleting) {
      if (this.currentIndex > 0) {
        this.currentIndex--
        this.displayRef.value = segments.slice(0, this.currentIndex).join('')
        this.timeoutId = window.setTimeout(() => this.type(), this.deleteSpeed)
      } else {
        this.isDeleting = false
        this.currentTextIndex = (this.currentTextIndex + 1) % this.texts.length
        this.timeoutId = window.setTimeout(() => this.type(), this.speed)
      }
    } else {
      if (this.currentIndex < segments.length) {
        this.currentIndex++
        this.displayRef.value = segments.slice(0, this.currentIndex).join('')
        this.timeoutId = window.setTimeout(() => this.type(), this.speed)
      } else {
        if (this.texts.length > 1) {
          this.isDeleting = true
          this.timeoutId = window.setTimeout(() => this.type(), this.pauseTime)
        }
      }
    }
  }

  public destroy() {
    if (this.timeoutId !== null) {
      window.clearTimeout(this.timeoutId)
      this.timeoutId = null
    }
  }

  private segmentText(text: string): string[] {
    const segmenter = new Intl.Segmenter(undefined, { granularity: 'grapheme' })
    return Array.from(segmenter.segment(text), s => s.segment)
  }
}

function restartTypewriter() {
  if (typewriterInstance) {
    typewriterInstance.destroy()
    typewriterInstance = null
  }
  typewriterDisplay.value = ''
  typewriterInstance = new TypewriterEffect(typewriterTexts.value, typewriterDisplay, 100, 50, 2000)
}

onMounted(() => {
  restartTypewriter()
})

watch(typewriterTexts, () => {
  restartTypewriter()
}, { flush: 'post' })

onUnmounted(() => {
  if (typewriterInstance) {
    typewriterInstance.destroy()
    typewriterInstance = null
  }
})
</script>

<template>
  <Transition name="wallpaper">
    <div v-if="hasWallpaper" class="top-gradient-highlight" aria-hidden="true" />
  </Transition>

  <!-- Wallpaper Wrapper -->
  <Transition name="wallpaper">
    <div
      v-if="hasWallpaper"
      id="wallpaper-wrapper"
      :class="{ 'wallpaper-overlay': !isBannerMode, 'banner-mode': isBannerMode }"
      aria-hidden="true"
    >
      <div class="wallpaper-image-container">
        <div
          v-for="(src, idx) in bannerImages"
          :key="src"
          class="wallpaper-slide"
          :class="{ active: idx === currentBannerIndex }"
        >
          <img :src="src" :alt="`banner-${idx}`">
        </div>
      </div>

      <!-- Banner 专属效果 -->
      <Transition name="banner-content">
        <div v-if="isBannerMode" class="banner-exclusive-content">
          <div class="banner-dim-overlay" />
          <div class="banner-bottom-fade" aria-hidden="true" />
          <Transition name="banner-fade-up">
            <div v-if="appearance.bannerTitleEnabled" class="banner-home-text-overlay">
              <div class="banner-text-content">
                <h1 class="banner-title">Hello, 你们好呀!</h1>
                <p class="banner-subtitle">
                  <span class="typewriter">{{ typewriterDisplay }}</span>
                  <span class="typewriter-cursor">|</span>
                </p>
              </div>
            </div>
          </Transition>
          <!-- Waves -->
          <Transition name="banner-fade-up">
            <div
              v-if="appearance.bannerWavesEnabled"
              id="header-waves"
              class="waves"
            >
              <svg
                class="waves"
                xmlns="http://www.w3.org/2000/svg"
                xmlns:xlink="http://www.w3.org/1999/xlink"
                viewBox="0 24 150 28"
                preserveAspectRatio="none"
                shape-rendering="geometricPrecision"
              >
                <defs>
                  <path
                    id="gentle-wave"
                    d="M-160 44c30 0 58-18 88-18s 58 18 88 18 58-18 88-18 58 18 88 18 v48h-352z"
                  />
                </defs>
                <g class="parallax">
                  <use
                    xlink:href="#gentle-wave"
                    x="48"
                    y="0"
                    class="wave-layer wave-layer-1"
                  />
                  <use
                    xlink:href="#gentle-wave"
                    x="48"
                    y="3"
                    class="wave-layer wave-layer-2"
                  />
                  <use
                    xlink:href="#gentle-wave"
                    x="48"
                    y="5"
                    class="wave-layer wave-layer-3"
                  />
                  <use
                    xlink:href="#gentle-wave"
                    x="48"
                    y="7"
                    class="wave-layer wave-layer-4"
                  />
                </g>
              </svg>
            </div>
          </Transition>
        </div>
      </Transition>
    </div>
  </Transition>
</template>

<style scoped>
.top-gradient-highlight {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 180px;
  background: linear-gradient(to bottom, rgba(255, 255, 255, 0.5) 0%, rgba(255, 255, 255, 0.3) 30%, rgba(255, 255, 255, 0.15) 60%, rgba(255, 255, 255, 0.05) 80%, transparent 100%);
  pointer-events: none;
  z-index: 20;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.wallpaper-enter-active,
.wallpaper-leave-active {
  transition: opacity 0.6s ease, transform 0.6s ease;
}

.wallpaper-enter-from,
.wallpaper-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.banner-exclusive-content {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
}

.banner-content-enter-active,
.banner-content-leave-active {
  transition: opacity 0.4s ease;
}

.banner-content-enter-from,
.banner-content-leave-to {
  opacity: 0;
}

.banner-fade-up-enter-active,
.banner-fade-up-leave-active {
  transition: opacity 0.4s cubic-bezier(0.4, 0, 0.2, 1), transform 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.banner-fade-up-enter-from,
.banner-fade-up-leave-to {
  opacity: 0;
  transform: translateY(20px);
}

.dark .top-gradient-highlight {
  background: linear-gradient(to bottom, rgba(0, 0, 0, 0.5) 0%, rgba(0, 0, 0, 0.3) 30%, rgba(0, 0, 0, 0.15) 60%, rgba(0, 0, 0, 0.05) 80%, transparent 100%);
}

/* Wallpaper Wrapper */
#wallpaper-wrapper {
  position: relative;
  width: 100%;
  overflow: hidden;
  z-index: 0;
}

#wallpaper-wrapper.wallpaper-overlay {
  position: fixed;
  inset: 0 !important;
  width: 100% !important;
  height: 100% !important;
  z-index: -1 !important;
  opacity: var(--overlay-opacity, 0.8) !important;
  pointer-events: none !important;
  overflow: hidden !important;
  min-height: unset !important;
  max-height: unset !important;
  transform: none !important;
  transition: opacity 0.6s ease !important;
}

#wallpaper-wrapper.wallpaper-overlay .wallpaper-slide img {
  width: 100% !important;
  height: 100% !important;
  object-fit: cover !important;
  object-position: center !important;
  filter: blur(var(--overlay-blur, 0px));
}

/* Banner mode */
#wallpaper-wrapper.banner-mode {
  height: 65vh;
  min-height: 420px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: -64px;
  padding-top: 64px;
}

.wallpaper-image-container {
  position: absolute;
  inset: 0;
  z-index: 0;
}

.wallpaper-slide {
  position: absolute;
  inset: 0;
  opacity: 0;
  transition: opacity 1.5s ease-in-out;
}

.wallpaper-slide.active {
  opacity: 1;
}

.wallpaper-slide img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transform: scale(1);
  transition: transform 6s ease-out, filter 0.3s ease;
}

.banner-mode .wallpaper-slide.active img {
  animation: kenBurns 6s ease-out forwards;
}

@keyframes kenBurns {
  0% { transform: scale(1); }
  100% { transform: scale(1.1); }
}

.banner-dim-overlay {
  position: absolute;
  inset: 0;
  z-index: 1;
  background: rgba(0, 0, 0, 0.15);
  pointer-events: none;
}

.banner-bottom-fade {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 40%;
  z-index: 1;
  background: linear-gradient(to bottom, transparent 0%, var(--page-bg) 100%);
  pointer-events: none;
}

.banner-home-text-overlay {
  position: absolute;
  inset: 0;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  color: #fff;
  padding: 1rem;
  user-select: none;
  pointer-events: none;
}

.banner-text-content {
  width: 80%;
  max-width: 900px;
  margin-bottom: 0;
  pointer-events: auto;
}

.banner-title {
  font-size: 3.5rem;
  font-weight: 700;
  margin-bottom: 0.75rem;
  text-shadow: 0 4px 24px rgba(0, 0, 0, 0.6);
  animation: banner-fadeInUp 0.6s ease-out both;
}

.banner-subtitle {
  font-size: 1.5rem;
  font-weight: 400;
  opacity: 0.95;
  text-shadow: 0 2px 16px rgba(0, 0, 0, 0.6);
  animation: banner-fadeInUp 0.6s ease-out 0.2s both;
  height: 2.25rem;
  line-height: 2.25rem;
}

.typewriter {
  display: inline;
}

.typewriter-cursor {
  display: inline;
  animation: blink 1s infinite;
  margin-left: 2px;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

@keyframes banner-fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Waves */
#header-waves {
  position: absolute;
  bottom: -1px;
  width: 100%;
  height: 10vh;
  max-height: 150px;
  min-height: 50px;
  isolation: isolate;
  contain: layout style;
  margin-bottom: -1px;
  will-change: transform;
  transform: translateZ(0);
  backface-visibility: hidden;
}

@media (min-width: 768px) {
  #header-waves {
    height: 15vh;
  }
}

.waves {
  overflow: visible;
  z-index: 5;
  transform: translateZ(0);
  will-change: transform;
  contain: layout style;
}

.waves svg {
  width: 100%;
  height: 100%;
  display: block;
  transform: translateZ(0);
  backface-visibility: hidden;
}

@media (max-width: 1023px) {
  .waves svg {
    min-height: 60px;
  }

  .waves {
    bottom: -1px !important;
    position: absolute !important;
  }
}

.wave-layer {
  fill: var(--page-bg);
}

.wave-layer-1 {
  opacity: 0.25;
}

.wave-layer-2 {
  opacity: 0.5;
}

.wave-layer-3 {
  opacity: 0.65;
}

.wave-layer-4 {
  opacity: 0.75;
}

#header-waves .parallax {
  will-change: transform;
  transform: translateZ(0);
  backface-visibility: hidden;
}

#header-waves .parallax use {
  animation: wave 25s cubic-bezier(0.5, 0.5, 0.45, 0.5) infinite;
  will-change: transform;
  transform: translateZ(0);
  backface-visibility: hidden;
}

#header-waves .parallax use:nth-child(1) {
  animation-delay: -2s;
  animation-duration: 7s;
}

#header-waves .parallax use:nth-child(2) {
  animation-delay: -3s;
  animation-duration: 10s;
}

#header-waves .parallax use:nth-child(3) {
  animation-delay: -4s;
  animation-duration: 13s;
}

#header-waves .parallax use:nth-child(4) {
  animation-delay: -5s;
  animation-duration: 20s;
}

@keyframes wave {
  0% {
    transform: translate3d(-90px, 0, 0);
  }
  100% {
    transform: translate3d(85px, 0, 0);
  }
}

/* 移动端 Banner 高度优化 - Firefly 风格 */
@media (max-width: 480px) {
  #wallpaper-wrapper.banner-mode {
    height: 70vh !important;
    min-height: 450px;
  }
}

@media (min-width: 481px) and (max-width: 640px) {
  #wallpaper-wrapper.banner-mode {
    height: 75vh !important;
    min-height: 500px;
  }
}

@media (min-width: 641px) and (max-width: 767px) {
  #wallpaper-wrapper.banner-mode {
    height: 72vh !important;
    min-height: 520px;
  }
}

@media (min-width: 768px) and (max-width: 1023px) {
  #wallpaper-wrapper.banner-mode {
    height: 70vh !important;
    min-height: 500px;
  }
}

/* 横屏模式优化 */
@media (max-width: 1023px) and (orientation: landscape) {
  #wallpaper-wrapper.banner-mode {
    height: 60vh !important;
    min-height: 300px;
  }
}

/* 基于屏幕高度的 Banner 优化 */
@media (max-height: 500px) {
  #wallpaper-wrapper.banner-mode {
    height: 85vh !important;
    min-height: 350px;
  }
}

@media (min-height: 501px) and (max-height: 600px) {
  #wallpaper-wrapper.banner-mode {
    height: 80vh !important;
    min-height: 400px;
  }
}

@media (min-height: 601px) and (max-height: 700px) {
  #wallpaper-wrapper.banner-mode {
    height: 75vh !important;
    min-height: 450px;
  }
}
</style>
