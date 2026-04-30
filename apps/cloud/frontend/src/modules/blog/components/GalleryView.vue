<script setup lang="ts">
import { Icon } from '@iconify/vue'
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { galleryConfig } from '../../../modules/gallery/config'
import { getAlbumCover, scanAlbumPhotos } from '../../../modules/gallery/utils'

const route = useRoute()
const router = useRouter()

const albumId = computed(() => {
  const id = route.query.album
  return typeof id === 'string' ? id : ''
})

const albums = computed(() => {
  return galleryConfig.albums.map((album) => {
    const photos = scanAlbumPhotos(album.id)
    const cover = getAlbumCover(album, photos)
    return { ...album, cover, photoCount: photos.length }
  })
})

const allTags = computed(() => {
  const tags = albums.value.flatMap((a) => a.tags || [])
  return [...new Set(tags)].sort()
})

const selectedTag = ref('all')

const filteredAlbums = computed(() => {
  if (selectedTag.value === 'all') return albums.value
  return albums.value.filter((a) => a.tags?.includes(selectedTag.value))
})

const currentAlbum = computed(() => {
  if (!albumId.value) return null
  return albums.value.find((a) => a.id === albumId.value) || null
})

const currentPhotos = computed(() => {
  if (!albumId.value) return []
  return scanAlbumPhotos(albumId.value)
})

function enterAlbum(id: string) {
  void router.replace({ path: '/blog', query: { mode: 'gallery', album: id } })
}

function backToAlbums() {
  void router.replace({ path: '/blog', query: { mode: 'gallery' } })
}

function selectTag(tag: string) {
  selectedTag.value = tag
}

// Fancybox
async function initFancybox() {
  if (!albumId.value) return
  await nextTick()
  const container = document.getElementById('gallery-photos')
  if (!container) return
  const links = container.querySelectorAll('[data-fancybox]')
  if (links.length === 0) return

  const [{ Fancybox }] = await Promise.all([
    import('@fancyapps/ui'),
    import('@fancyapps/ui/dist/fancybox/fancybox.css'),
  ])

  Fancybox.bind('[data-fancybox]', {
    Carousel: {
      infinite: true,
    },
    Thumbs: {
      type: 'classic',
    },
    Toolbar: {
      display: {
        left: ['infobar'],
        middle: ['zoomIn', 'zoomOut', 'toggle1to1', 'rotateCCW', 'rotateCW', 'flipX', 'flipY'],
        right: ['slideshow', 'thumbs', 'close'],
      },
    },
  } as any)
}

watch(albumId, () => {
  void initFancybox()
}, { immediate: true })

onMounted(() => {
  void initFancybox()
})
</script>

<template>
  <div class="gallery-view">
    <!-- 相册列表 -->
    <template v-if="!albumId">
      <div class="gallery-card">
        <div class="gallery-header">
          <div class="gallery-title-wrap">
            <div class="gallery-icon">
              <Icon icon="material-symbols:photo-library" class="gallery-icon-svg" />
            </div>
            <h1 class="gallery-title">相册</h1>
          </div>
          <p class="gallery-desc">记录生活中的美好瞬间</p>
        </div>

        <!-- 标签筛选 -->
        <div v-if="filteredAlbums.length > 0 && allTags.length > 0" class="gallery-filter">
          <button
            class="filter-btn"
            :class="{ active: selectedTag === 'all' }"
            @click="selectTag('all')"
          >
            全部
          </button>
          <button
            v-for="tag in allTags"
            :key="tag"
            class="filter-btn"
            :class="{ active: selectedTag === tag }"
            @click="selectTag(tag)"
          >
            {{ tag }}
          </button>
        </div>

        <!-- 相册卡片网格 -->
        <div v-if="filteredAlbums.length > 0" class="album-grid">
          <div
            v-for="album in filteredAlbums"
            :key="album.id"
            class="album-card"
            data-tags=""
            @click="enterAlbum(album.id)"
          >
            <div class="album-cover-wrap">
              <img
                v-if="album.cover"
                :src="album.cover"
                :alt="album.name"
                class="album-cover"
                loading="lazy"
              >
              <div v-else class="album-cover-placeholder">
                <span class="album-cover-icon">&#x1f4f7;</span>
              </div>
              <div class="album-count">
                {{ album.photoCount }} 张照片
              </div>
              <div class="album-gradient" />
              <div class="album-info">
                <h3 class="album-name">{{ album.name }}</h3>
                <p v-if="album.description" class="album-description">{{ album.description }}</p>
                <div class="album-meta">
                  <span v-if="album.date">{{ album.date }}</span>
                  <span v-if="album.location" class="album-location">
                    <Icon icon="material-symbols:location-on" class="album-location-icon" />
                    {{ album.location }}
                  </span>
                </div>
                <div v-if="album.tags && album.tags.length > 0" class="album-tags">
                  <span v-for="t in album.tags.slice(0, 4)" :key="t" class="album-tag">{{ t }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 空状态 -->
        <div v-else class="gallery-empty">
          <Icon icon="material-symbols:photo-library" class="gallery-empty-icon" />
          <p class="gallery-empty-text">暂无相册</p>
        </div>
      </div>
    </template>

    <!-- 相册详情 -->
    <template v-else-if="currentAlbum">
      <!-- 封面横幅 -->
      <div class="album-banner">
        <template v-if="currentAlbum.cover">
          <div class="album-banner-cover">
            <img
              :src="currentAlbum.cover"
              :alt="currentAlbum.name"
              class="album-banner-img"
            >
            <div class="album-banner-gradient" />
            <button class="album-back-btn" @click="backToAlbums">
              <Icon icon="material-symbols:arrow-back" class="album-back-icon" />
              返回相册
            </button>
            <div class="album-banner-info">
              <h2 class="album-banner-title">{{ currentAlbum.name }}</h2>
              <p v-if="currentAlbum.description" class="album-banner-desc">{{ currentAlbum.description }}</p>
              <div class="album-banner-meta">
                <span v-if="currentAlbum.date" class="album-banner-meta-item">
                  <Icon icon="material-symbols:calendar-today" class="album-banner-meta-icon" />
                  {{ currentAlbum.date }}
                </span>
                <span v-if="currentAlbum.location" class="album-banner-meta-item">
                  <Icon icon="material-symbols:location-on" class="album-banner-meta-icon" />
                  {{ currentAlbum.location }}
                </span>
                <span class="album-banner-meta-item">
                  <Icon icon="material-symbols:photo-library" class="album-banner-meta-icon" />
                  {{ currentPhotos.length }} 张照片
                </span>
              </div>
              <div v-if="currentAlbum.tags && currentAlbum.tags.length > 0" class="album-banner-tags">
                <span v-for="tag in currentAlbum.tags" :key="tag" class="album-banner-tag">{{ tag }}</span>
              </div>
            </div>
          </div>
        </template>
        <template v-else>
          <div class="gallery-card album-banner-fallback">
            <button class="album-back-btn-text" @click="backToAlbums">
              <Icon icon="material-symbols:arrow-back" class="album-back-icon" />
              返回相册
            </button>
            <h2 class="album-banner-title-fallback">{{ currentAlbum.name }}</h2>
            <div class="album-banner-meta-fallback">
              <span v-if="currentAlbum.date">{{ currentAlbum.date }}</span>
              <span v-if="currentAlbum.location">{{ currentAlbum.location }}</span>
              <span>{{ currentPhotos.length }} 张照片</span>
            </div>
          </div>
        </template>
      </div>

      <!-- 瀑布流照片 -->
      <div class="gallery-card">
        <div id="gallery-photos" class="gallery-photos">
          <div
            v-if="currentPhotos.length > 0"
            class="gallery-masonry"
            :style="{ '--col-width': `${galleryConfig.columnWidth || 240}px` }"
          >
            <div
              v-for="(photo, idx) in currentPhotos"
              :key="idx"
              class="photo-card"
              :data-fancybox="`gallery-${currentAlbum.id}`"
              :data-src="photo"
              data-type="image"
            >
              <img
                :src="photo"
                :alt="`${currentAlbum.name} - ${idx + 1}`"
                loading="lazy"
                class="photo-img"
              >
            </div>
          </div>
          <div v-else class="gallery-empty">
            <Icon icon="material-symbols:photo-library" class="gallery-empty-icon" />
            <p class="gallery-empty-text">暂无照片</p>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.gallery-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.gallery-card {
  background: var(--card-bg-transparent);
  border-radius: var(--radius-large);
  border: 1px solid rgba(255, 255, 255, 0.45);
  backdrop-filter: blur(18px);
  padding: 24px;
  box-shadow: 0 10px 30px rgba(148, 163, 184, 0.14);
  transition: transform var(--transition-base), box-shadow var(--transition-base), background-color var(--transition-base), border-color var(--transition-base);
}

.dark .gallery-card {
  border-color: rgba(148, 163, 184, 0.16);
  box-shadow: 0 12px 28px rgba(2, 6, 23, 0.28);
}

.gallery-header {
  margin-bottom: 16px;
}

.gallery-title-wrap {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.gallery-icon {
  height: 32px;
  width: 32px;
  border-radius: 8px;
  background: var(--primary);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.gallery-icon-svg {
  font-size: 20px;
}

.gallery-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.gallery-desc {
  font-size: 0.875rem;
  color: var(--text-secondary);
  margin: 0;
}

.gallery-filter {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
}

.filter-btn {
  padding: 6px 14px;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  border: none;
  cursor: pointer;
  transition: all 0.2s;
  background: var(--btn-regular-bg);
  color: var(--btn-content);
}

.filter-btn:hover {
  background: var(--btn-regular-bg-hover);
}

.filter-btn.active {
  background: var(--primary);
  color: white;
}

.album-grid {
  display: grid;
  grid-template-columns: repeat(1, 1fr);
  gap: 16px;
}

@media (min-width: 640px) {
  .album-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 1024px) {
  .album-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

.album-card {
  position: relative;
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.3s, box-shadow 0.3s;
}

.album-card:hover {
  transform: scale(1.02);
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.15);
}

.album-cover-wrap {
  position: relative;
  aspect-ratio: 4 / 3;
  overflow: hidden;
}

.album-cover {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.5s;
  pointer-events: none;
}

.album-card:hover .album-cover {
  transform: scale(1.05);
}

.album-cover-placeholder {
  width: 100%;
  height: 100%;
  background: #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: center;
}

.dark .album-cover-placeholder {
  background: #374151;
}

.album-cover-icon {
  font-size: 3rem;
  color: #9ca3af;
}

.album-count {
  position: absolute;
  top: 8px;
  right: 8px;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 500;
  color: white;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
}

.album-gradient {
  position: absolute;
  inset: 0;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.7) 0%, rgba(0, 0, 0, 0.2) 50%, transparent 100%);
  pointer-events: none;
}

.album-info {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 16px;
  color: white;
}

.album-name {
  font-size: 1rem;
  font-weight: 700;
  margin: 0 0 4px;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.album-description {
  font-size: 0.75rem;
  opacity: 0.85;
  margin: 0 0 6px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.album-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 0.75rem;
  opacity: 0.75;
  flex-wrap: wrap;
}

.album-location {
  display: inline-flex;
  align-items: center;
  gap: 2px;
}

.album-location-icon {
  font-size: 12px;
}

.album-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 8px;
}

.album-tag {
  font-size: 0.65rem;
  padding: 2px 8px;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.2);
  color: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(4px);
}

.gallery-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 0;
  color: var(--text-tertiary);
}

.gallery-empty-icon {
  font-size: 4rem;
  margin-bottom: 16px;
  opacity: 0.5;
}

.gallery-empty-text {
  font-size: 1.125rem;
  margin: 0;
}

/* 详情页横幅 */
.album-banner {
  border-radius: var(--radius-large);
  overflow: hidden;
}

.album-banner-cover {
  position: relative;
  width: 100%;
  aspect-ratio: 3 / 1;
  min-height: 200px;
  max-height: 360px;
}

.album-banner-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.album-banner-gradient {
  position: absolute;
  inset: 0;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.7) 0%, rgba(0, 0, 0, 0.3) 50%, transparent 100%);
}

.album-back-btn {
  position: absolute;
  top: 16px;
  left: 16px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.9);
  background: rgba(0, 0, 0, 0.3);
  border: none;
  backdrop-filter: blur(4px);
  padding: 8px 14px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.album-back-btn:hover {
  background: rgba(0, 0, 0, 0.5);
  color: white;
}

.album-back-icon {
  font-size: 16px;
}

.album-banner-info {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 24px;
  color: white;
}

.album-banner-title {
  font-size: 1.75rem;
  font-weight: 700;
  margin: 0 0 8px;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
}

.album-banner-desc {
  font-size: 0.875rem;
  opacity: 0.8;
  margin: 0 0 10px;
  max-width: 42rem;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.album-banner-meta {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 0.875rem;
  opacity: 0.85;
  flex-wrap: wrap;
}

.album-banner-meta-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.album-banner-meta-icon {
  font-size: 14px;
}

.album-banner-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 10px;
}

.album-banner-tag {
  font-size: 0.75rem;
  padding: 3px 10px;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.2);
  color: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(4px);
}

.album-banner-fallback {
  padding: 20px 24px;
}

.album-back-btn-text {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 0.875rem;
  color: var(--primary);
  background: transparent;
  border: none;
  padding: 0;
  margin-bottom: 12px;
  cursor: pointer;
}

.album-back-btn-text:hover {
  text-decoration: underline;
}

.album-banner-title-fallback {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 8px;
}

.album-banner-meta-fallback {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 0.875rem;
  color: var(--text-secondary);
  flex-wrap: wrap;
}

/* 瀑布流 */
.gallery-photos {
  min-height: 120px;
}

.gallery-masonry {
  column-count: 2;
  column-gap: 12px;
}

@media (min-width: 640px) {
  .gallery-masonry {
    column-width: var(--col-width, 240px);
    column-count: auto;
  }
}

.photo-card {
  break-inside: avoid;
  margin-bottom: 12px;
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
}

.photo-img {
  width: 100%;
  height: auto;
  object-fit: cover;
  transition: transform 0.3s;
  display: block;
}

.photo-card:hover .photo-img {
  transform: scale(1.05);
}
</style>
