<script setup lang="ts">
import { Icon } from '@iconify/vue'
import { computed, nextTick, ref, watch } from 'vue'
import { 使用音乐播放器 } from '../composables/使用音乐播放器'

const {
  state,
  currentTrack,
  progress,
  currentTimeText,
  durationText,
  togglePlay,
  playNext,
  playPrev,
  cyclePlayMode,
  setVolume,
  toggleMute,
  seek,
  seekToTime,
  playTrackByIndex,
} = 使用音乐播放器()

const showLyrics = ref(false)
const showPlaylist = ref(false)
const lyricContainerRef = ref<HTMLElement | null>(null)

const playModeIcon = computed(() => {
  if (state.value.playMode === 'one') {
    return 'material-symbols:repeat-one-rounded'
  }
  if (state.value.playMode === 'random') {
    return 'material-symbols:shuffle-rounded'
  }
  return 'material-symbols:repeat-rounded'
})

const playModeLabel = computed(() => {
  if (state.value.playMode === 'one') {
    return '单曲循环'
  }
  if (state.value.playMode === 'random') {
    return '随机播放'
  }
  return '列表循环'
})

const volumePercent = computed(() => Math.round((state.value.isMuted ? 0 : state.value.volume) * 100))
const hasLyrics = computed(() => state.value.lyrics.length > 0)
const hasPlaylist = computed(() => state.value.playlist.length > 0)

function handleProgressClick(event: MouseEvent) {
  const target = event.currentTarget
  if (!(target instanceof HTMLElement)) {
    return
  }

  const rect = target.getBoundingClientRect()
  seek((event.clientX - rect.left) / rect.width)
}

function handleVolumeClick(event: MouseEvent) {
  const target = event.currentTarget
  if (!(target instanceof HTMLElement)) {
    return
  }

  const rect = target.getBoundingClientRect()
  setVolume((event.clientX - rect.left) / rect.width)
}

function toggleLyrics() {
  showLyrics.value = !showLyrics.value
  if (showLyrics.value) {
    showPlaylist.value = false
  }
}

function togglePlaylist() {
  showPlaylist.value = !showPlaylist.value
  if (showPlaylist.value) {
    showLyrics.value = false
  }
}

watch(
  () => state.value.currentLyricIndex,
  async (index) => {
    if (!showLyrics.value || index < 0) {
      return
    }

    await nextTick()
    const container = lyricContainerRef.value
    const activeLine = container?.querySelector<HTMLElement>(`[data-lyric-index="${index}"]`)
    if (!container || !activeLine) {
      return
    }

    container.scrollTo({
      top: activeLine.offsetTop - container.clientHeight / 2 + activeLine.clientHeight / 2,
      behavior: 'smooth',
    })
  },
)
</script>

<template>
  <div v-if="hasPlaylist" class="music-player widget-card" role="region" aria-label="音乐播放器">
    <div class="widget-header">
      <span>音乐</span>
    </div>

    <div class="music-body">
      <div class="track-row">
        <div class="cover-wrap">
          <Icon class="cover-placeholder" icon="material-symbols:music-note-rounded" />
          <img
            v-if="currentTrack?.cover"
            class="cover-image"
            :class="{ 'is-playing': state.isPlaying }"
            :src="currentTrack.cover"
            :alt="`${currentTrack.name} 封面`"
          >
        </div>

        <div class="track-info">
          <div class="track-title-row">
            <div class="track-title" :title="currentTrack?.name || '暂无歌曲'">
              {{ currentTrack?.name || '暂无歌曲' }}
            </div>
            <button
              class="icon-button subtle"
              :class="{ active: showLyrics }"
              type="button"
              title="歌词"
              @click="toggleLyrics"
            >
              <Icon :icon="showLyrics ? 'material-symbols:subtitles-rounded' : 'material-symbols:subtitles-off-outline-rounded'" />
            </button>
          </div>
          <div class="track-artist" :title="currentTrack?.artist || '未开始播放'">
            {{ currentTrack?.artist || '未开始播放' }}
          </div>
          <div v-if="state.error" class="track-error">{{ state.error }}</div>

          <div class="meta-row">
            <div class="time-row" aria-live="polite">
              <span>{{ currentTimeText }}</span>
              <span class="time-divider">/</span>
              <span>{{ durationText }}</span>
            </div>

            <div class="volume-row">
              <button class="icon-button tiny" type="button" title="静音" @click="toggleMute">
                <Icon :icon="state.isMuted || state.volume === 0 ? 'material-symbols:volume-off-rounded' : 'material-symbols:volume-up-rounded'" />
              </button>
              <button class="volume-track" type="button" aria-label="音量" @click="handleVolumeClick">
                <span class="volume-fill" :style="{ width: `${volumePercent}%` }" />
              </button>
            </div>
          </div>
        </div>
      </div>

      <button
        class="progress-track"
        type="button"
        :aria-valuenow="Math.round(progress)"
        aria-valuemin="0"
        aria-valuemax="100"
        aria-label="播放进度"
        @click="handleProgressClick"
      >
        <span class="progress-fill" :style="{ width: `${progress}%` }" />
        <span class="progress-thumb" :style="{ left: `${progress}%` }" />
      </button>

      <div class="control-row">
        <button
          class="icon-button"
          :class="{ active: state.playMode !== 'list' }"
          type="button"
          :title="playModeLabel"
          @click="cyclePlayMode"
        >
          <Icon :icon="playModeIcon" />
        </button>
        <button class="icon-button" type="button" title="上一首" @click="playPrev()">
          <Icon icon="material-symbols:skip-previous-rounded" />
        </button>
        <button class="play-button" type="button" :title="state.isPlaying ? '暂停' : '播放'" @click="togglePlay">
          <Icon :icon="state.isPlaying ? 'material-symbols:pause-rounded' : 'material-symbols:play-arrow-rounded'" />
        </button>
        <button class="icon-button" type="button" title="下一首" @click="playNext()">
          <Icon icon="material-symbols:skip-next-rounded" />
        </button>
        <button
          class="icon-button"
          :class="{ active: showPlaylist }"
          type="button"
          title="播放列表"
          @click="togglePlaylist"
        >
          <Icon icon="mdi:playlist-music" />
        </button>
      </div>

      <div class="drawer-shell" :class="{ open: showLyrics }">
        <div class="drawer-inner">
          <div class="drawer-panel">
            <div ref="lyricContainerRef" class="lyrics-list">
              <button
                v-for="(line, index) in state.lyrics"
                :key="`${line.time}-${line.text}`"
                class="lyric-line"
                :class="{ active: index === state.currentLyricIndex }"
                type="button"
                :data-lyric-index="index"
                @click="seekToTime(line.time)"
              >
                {{ line.text }}
              </button>
              <div v-if="state.lyricStatus === 'loading'" class="drawer-empty">歌词加载中</div>
              <div v-else-if="state.lyricStatus === 'failed'" class="drawer-empty">歌词加载失败</div>
              <div v-else-if="!hasLyrics" class="drawer-empty">暂无歌词</div>
            </div>
          </div>
        </div>
      </div>

      <div class="drawer-shell" :class="{ open: showPlaylist }">
        <div class="drawer-inner">
          <div class="drawer-panel">
            <div class="playlist">
              <button
                v-for="(track, index) in state.playlist"
                :key="track.id"
                class="playlist-item"
                :class="{ active: index === state.currentIndex }"
                type="button"
                @click="playTrackByIndex(index)"
              >
                <img v-if="track.cover" class="playlist-cover" :src="track.cover" :alt="`${track.name} 封面`">
                <span v-else class="playlist-cover empty">
                  <Icon icon="material-symbols:music-note-rounded" />
                </span>
                <span class="playlist-text">
                  <span class="playlist-title">{{ track.name }}</span>
                  <span class="playlist-artist">{{ track.artist }}</span>
                </span>
                <span v-if="index === state.currentIndex" class="playlist-playing">
                  <Icon icon="material-symbols:graphic-eq-rounded" />
                </span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.widget-card {
  background: var(--card-bg-transparent);
  border-radius: var(--radius-large);
  overflow: hidden;
  transition: transform 0.2s, box-shadow 0.2s, background-color 0.2s, border-color 0.2s;
  border: 1px solid rgba(255, 255, 255, 0.45);
  backdrop-filter: blur(18px);
  box-shadow: 0 12px 28px rgba(148, 163, 184, 0.14);
}

.widget-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 18px 36px rgba(148, 163, 184, 0.18);
}

.dark .widget-card {
  border-color: rgba(148, 163, 184, 0.16);
  box-shadow: 0 12px 28px rgba(2, 6, 23, 0.28);
}

.dark .widget-card:hover {
  box-shadow: 0 18px 36px rgba(2, 6, 23, 0.35);
}

.widget-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0;
  font-weight: 700;
  font-size: 1.125rem;
  color: var(--text-primary);
  position: relative;
  margin-left: 32px;
  margin-top: 16px;
  margin-bottom: 8px;
  border-bottom: none;
}

.widget-header::before {
  content: '';
  position: absolute;
  left: -16px;
  top: 5.5px;
  width: 4px;
  height: 16px;
  border-radius: 2px;
  background: var(--primary);
}

.music-body {
  display: flex;
  flex-direction: column;
  gap: 9px;
  padding: 0 12px 9px;
}

.track-row {
  display: flex;
  gap: 10px;
  align-items: center;
  min-width: 0;
  padding: 0 4px;
}

.cover-wrap {
  position: relative;
  width: 56px;
  height: 56px;
  flex: 0 0 auto;
  display: grid;
  place-items: center;
  overflow: hidden;
  border-radius: 50%;
  background: color-mix(in srgb, var(--primary) 12%, transparent);
  border: 2px solid rgba(255, 255, 255, 0.62);
}

.dark .cover-wrap {
  border-color: rgba(148, 163, 184, 0.2);
}

.cover-placeholder {
  position: absolute;
  font-size: 1.7rem;
  color: var(--primary);
  opacity: 0.45;
}

.cover-image {
  position: relative;
  z-index: 1;
  width: 100%;
  height: 100%;
  object-fit: cover;
  animation: music-cover-spin 12s linear infinite;
  animation-play-state: paused;
}

.cover-image.is-playing {
  animation-play-state: running;
}

.track-info {
  min-width: 0;
  flex: 1 1 auto;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.track-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.track-title,
.track-artist,
.track-error {
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.track-title {
  flex: 1 1 auto;
  min-width: 0;
  color: var(--text-primary);
  font-size: 0.96rem;
  font-weight: 700;
  line-height: 1.25;
}

.track-artist {
  color: var(--text-secondary);
  font-size: 0.78rem;
}

.track-error {
  color: #dc2626;
  font-size: 0.72rem;
}

.meta-row {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  height: 20px;
}

.progress-track,
.volume-track {
  position: relative;
  display: block;
  width: 100%;
  padding: 0;
  border: 0;
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.2);
  cursor: pointer;
}

.progress-track {
  height: 5px;
  margin-top: 2px;
  overflow: hidden;
}

.progress-fill,
.volume-fill {
  position: absolute;
  inset: 0 auto 0 0;
  display: block;
  border-radius: inherit;
  background: var(--primary);
}

.progress-thumb {
  position: absolute;
  top: 50%;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--primary);
  border: 2px solid rgba(255, 255, 255, 0.9);
  box-shadow: 0 4px 10px rgba(15, 23, 42, 0.16);
  transform: translate(-50%, -50%) scale(0);
  transition: transform 0.2s;
}

.progress-track:hover {
  overflow: visible;
}

.progress-track:hover .progress-thumb {
  transform: translate(-50%, -50%) scale(1);
}

.time-row {
  display: flex;
  align-items: center;
  gap: 4px;
  flex: 0 0 auto;
  color: var(--text-tertiary);
  font-family: ui-monospace, SFMono-Regular, Consolas, 'Liberation Mono', monospace;
  font-size: 0.72rem;
}

.time-divider {
  opacity: 0.55;
}

.control-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 2px;
}

.volume-row {
  display: flex;
  align-items: center;
  gap: 4px;
  flex: 1 1 auto;
  min-width: 64px;
}

.icon-button,
.play-button {
  display: inline-grid;
  place-items: center;
  border: 0;
  color: var(--text-secondary);
  background: transparent;
  cursor: pointer;
  transition: color 0.2s, background-color 0.2s, transform 0.2s;
}

.icon-button {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  font-size: 1.45rem;
}

.icon-button.subtle {
  width: 26px;
  height: 26px;
  flex: 0 0 auto;
  color: var(--text-tertiary);
  font-size: 1.15rem;
}

.icon-button.tiny {
  width: 22px;
  height: 22px;
  flex: 0 0 auto;
  border-radius: 6px;
  font-size: 1.1rem;
}

.icon-button:hover,
.icon-button.active {
  color: var(--primary);
  background: var(--btn-plain-bg-hover);
}

.play-button {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  color: var(--primary);
  background: var(--btn-regular-bg);
  font-size: 2.1rem;
}

.play-button:hover {
  color: #ffffff;
  background: var(--primary);
}

.icon-button:active,
.play-button:active {
  transform: scale(0.96);
}

.volume-track {
  height: 5px;
  flex: 1 1 auto;
  min-width: 0;
  overflow: hidden;
}

.drawer-shell {
  display: grid;
  grid-template-rows: 0fr;
  opacity: 0;
  transition: grid-template-rows 0.3s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.3s;
}

.drawer-shell:not(.open) {
  display: none;
}

.drawer-shell.open {
  grid-template-rows: 1fr;
  opacity: 1;
}

.drawer-inner {
  min-height: 0;
  overflow: hidden;
}

.drawer-panel {
  margin: 2px 4px 0;
  padding-top: 10px;
  border-top: 1px solid var(--line-divider);
}

.lyrics-list,
.playlist {
  max-height: 180px;
  overflow-y: auto;
}

.lyrics-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 54px 4px;
  scroll-behavior: smooth;
}

.lyric-line {
  border: 0;
  border-radius: 8px;
  padding: 6px 8px;
  color: var(--text-tertiary);
  background: transparent;
  font-size: 0.82rem;
  line-height: 1.5;
  cursor: pointer;
  transition: color 0.2s, background-color 0.2s, font-size 0.2s;
}

.lyric-line:hover,
.lyric-line.active {
  color: var(--primary);
  background: var(--btn-plain-bg-hover);
}

.lyric-line.active {
  font-size: 0.9rem;
  font-weight: 700;
}

.drawer-empty {
  padding: 30px 0;
  color: var(--text-tertiary);
  text-align: center;
  font-size: 0.82rem;
}

.playlist {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding-right: 2px;
}

.playlist-item {
  display: flex;
  align-items: center;
  gap: 9px;
  width: 100%;
  min-width: 0;
  border: 0;
  border-radius: 8px;
  padding: 7px;
  color: var(--text-secondary);
  background: transparent;
  text-align: left;
  cursor: pointer;
  transition: color 0.2s, background-color 0.2s;
}

.playlist-item:hover,
.playlist-item.active {
  color: var(--primary);
  background: var(--btn-plain-bg-hover);
}

.playlist-cover {
  width: 34px;
  height: 34px;
  flex: 0 0 auto;
  border-radius: 7px;
  object-fit: cover;
  overflow: hidden;
}

.playlist-cover.empty {
  display: grid;
  place-items: center;
  background: rgba(148, 163, 184, 0.18);
}

.playlist-text {
  min-width: 0;
  flex: 1 1 auto;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.playlist-title,
.playlist-artist {
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.playlist-title {
  color: var(--text-primary);
  font-size: 0.82rem;
  font-weight: 700;
}

.playlist-artist {
  color: var(--text-tertiary);
  font-size: 0.72rem;
}

.playlist-playing {
  display: grid;
  place-items: center;
  flex: 0 0 auto;
  color: var(--primary);
  font-size: 1rem;
}

@keyframes music-cover-spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
