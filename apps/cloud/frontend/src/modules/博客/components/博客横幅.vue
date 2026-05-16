<script setup lang="ts">
import { Icon } from '@iconify/vue'
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import readingTime from 'reading-time/lib/reading-time'
import { useBannerImages } from '../composables/useBannerImages'
import type { BlogViewMode } from '../../../modules/博客/view'
import { useArticleStore, type CategoryRecord } from '@personal-system/module-articles'
import { useBlogAppearanceStore } from '../store'
import TypewriterText from './打字机效果.vue'

const appearance = useBlogAppearanceStore()
const articleStore = useArticleStore()
const route = useRoute()

const props = defineProps<{
  viewMode: BlogViewMode
  activeCategory?: string | null
  categories?: CategoryRecord[]
}>()

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

/* ==================== 页面类型判断 ==================== */
const isHomePage = computed(() => !articleSlug.value && props.viewMode === 'feed' && !props.activeCategory)
const isCategoryPage = computed(() => !articleSlug.value && props.viewMode === 'feed' && !!props.activeCategory)
const isPostPage = computed(() => !!articleSlug.value)
const isOtherPage = computed(() => !isHomePage.value && !isCategoryPage.value && !isPostPage.value)

const pageTitleMap: Record<string, string> = {
  archive: '归档',
  announcements: '公告',
  friends: '友情链接',
  about: '关于我',
  guestbook: '留言板',
  sponsor: '赞助支持',
  bangumi: '番组计划',
  gallery: '相册',
  rss: 'RSS 订阅',
}
const pageTitle = computed(() => pageTitleMap[props.viewMode] || '')

const categoryName = computed(() => {
  if (!props.activeCategory || !props.categories) return ''
  const cat = props.categories.find((c) => c.slug === props.activeCategory)
  return cat?.name || props.activeCategory
})

/* ==================== Typewriter 打字机效果 (Firefly 风格) ==================== */
const defaultTypewriterTexts = [
  '欢迎来到我的小窝',
  '记录生活，分享技术',
  '愿每一天都充满阳光',
]
const typewriterTexts = computed(() => {
  if (isPostPage.value && articleStore.current) {
    return [articleStore.current.title]
  }
  return defaultTypewriterTexts
})

/* ==================== 文章页元信息 ==================== */
const readingTimeInfo = computed(() => {
  if (!articleStore.current?.content) return null
  const rt = readingTime(articleStore.current.content)
  return {
    minutes: Math.max(1, Math.round(rt.minutes)),
    words: articleStore.current.word_count,
  }
})

function formatDate(date: string | null | undefined) {
  if (!date) return ''
  return new Date(date).toISOString().slice(0, 10)
}
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
          <!-- 首页文字 -->
          <Transition name="banner-fade-up">
            <div v-if="isHomePage && appearance.bannerTitleEnabled" class="banner-home-text-overlay">
              <div class="banner-text-content">
                <h1 class="banner-title">Hello, 你们好呀!</h1>
                <p class="banner-subtitle">
                  <TypewriterText :texts="typewriterTexts" />
                </p>
              </div>
            </div>
          </Transition>

          <!-- 文章页元信息 -->
          <Transition name="banner-fade-up">
            <div v-if="isPostPage && articleStore.current" class="banner-post-meta-overlay">
              <div class="banner-text-content">
                <div class="banner-post-title">{{ articleStore.current.title }}</div>
                <div class="banner-post-meta-list">
                  <span class="banner-meta-item">
                    <Icon icon="material-symbols:calendar-month-outline-rounded" class="banner-meta-icon" />
                    <span>发布于 {{ formatDate(articleStore.current.published_at || articleStore.current.created_at) }}</span>
                  </span>
                  <span v-if="articleStore.current.updated_at && new Date(articleStore.current.updated_at).getTime() !== new Date(articleStore.current.published_at || articleStore.current.created_at).getTime()" class="banner-meta-item">
                    <Icon icon="material-symbols:update-rounded" class="banner-meta-icon" />
                    <span>更新于 {{ formatDate(articleStore.current.updated_at) }}</span>
                  </span>
                  <span v-if="typeof readingTimeInfo?.words === 'number'" class="banner-meta-item">
                    <Icon icon="material-symbols:ink-pen-outline-rounded" class="banner-meta-icon" />
                    <span>{{ readingTimeInfo.words }} 字</span>
                  </span>
                  <span v-if="readingTimeInfo" class="banner-meta-item">
                    <Icon icon="material-symbols:schedule-outline-rounded" class="banner-meta-icon" />
                    <span>{{ readingTimeInfo.minutes }} 分钟 · 阅读时间</span>
                  </span>
                </div>
              </div>
            </div>
          </Transition>

          <!-- 分类页面标题 -->
          <Transition name="banner-fade-up">
            <div v-if="isCategoryPage && categoryName" class="banner-page-title-overlay">
              <div class="banner-text-content">
                <div class="banner-page-title">{{ categoryName }}</div>
              </div>
            </div>
          </Transition>

          <!-- 其他页面标题 -->
          <Transition name="banner-fade-up">
            <div v-if="isOtherPage && pageTitle" class="banner-page-title-overlay">
              <div class="banner-text-content">
                <div class="banner-page-title">{{ pageTitle }}</div>
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

/* 文章页元信息层 */
.banner-post-meta-overlay {
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

.banner-post-title {
  font-size: clamp(2rem, 4vw, 3rem);
  font-weight: 700;
  line-height: 1.2;
  margin-bottom: 0.75rem;
  text-shadow: 0 4px 24px rgba(0, 0, 0, 0.65);
  animation: banner-fadeInUp 0.6s ease-out both;
}

.banner-post-meta-list {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 0.5rem 1.25rem;
  font-size: 0.95rem;
  color: rgba(255, 255, 255, 0.9);
  text-shadow: 0 2px 16px rgba(0, 0, 0, 0.6);
  animation: banner-fadeInUp 0.6s ease-out 0.2s both;
}

.banner-meta-item {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
}

.banner-meta-icon {
  font-size: 1.05em;
}

/* 其他页面标题层 */
.banner-page-title-overlay {
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

.banner-page-title {
  font-size: clamp(2rem, 4vw, 3rem);
  font-weight: 700;
  line-height: 1.2;
  text-shadow: 0 4px 24px rgba(0, 0, 0, 0.65);
  animation: banner-fadeInUp 0.6s ease-out both;
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
