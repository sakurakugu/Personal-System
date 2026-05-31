import { computed, onBeforeUnmount, onMounted, readonly, ref } from 'vue'
import { 默认音乐播放列表, 默认音乐播放模式, 默认音乐音量 } from '../config'
import type { MusicLyricLine, MusicPlayMode, MusicTrack } from '../types'

const 音量存储键 = 'personal-system-music-volume'

type 播放器状态 = {
  playlist: MusicTrack[]
  currentIndex: number
  isPlaying: boolean
  playMode: MusicPlayMode
  volume: number
  isMuted: boolean
  currentTime: number
  duration: number
  lyrics: MusicLyricLine[]
  lyricStatus: 'none' | 'loading' | 'loaded' | 'failed'
  currentLyricIndex: number
  error: string | null
  initialized: boolean
}

const 状态 = ref<播放器状态>({
  playlist: 默认音乐播放列表,
  currentIndex: 0,
  isPlaying: false,
  playMode: 默认音乐播放模式,
  volume: 默认音乐音量,
  isMuted: false,
  currentTime: 0,
  duration: 0,
  lyrics: [],
  lyricStatus: 'none',
  currentLyricIndex: -1,
  error: null,
  initialized: false,
})

let audio: HTMLAudioElement | null = null
let listenersBound = false

function 格式化时间(seconds: number) {
  if (!Number.isFinite(seconds) || seconds <= 0) {
    return '0:00'
  }

  const minutes = Math.floor(seconds / 60)
  const restSeconds = Math.floor(seconds % 60)
  return `${minutes}:${restSeconds.toString().padStart(2, '0')}`
}

function 解析歌词(lrc: string): MusicLyricLine[] {
  const lines = lrc.split('\n')
  const result: MusicLyricLine[] = []
  const timePattern = /\[(\d{2}):(\d{2})\.(\d{2,3})\]/g

  for (const line of lines) {
    const matches = Array.from(line.matchAll(timePattern))
    if (matches.length === 0) {
      continue
    }

    const text = line.replace(timePattern, '').trim()
    if (!text) {
      continue
    }

    for (const match of matches) {
      const minutes = Number.parseInt(match[1] ?? '0', 10)
      const seconds = Number.parseInt(match[2] ?? '0', 10)
      const millisecondsText = match[3] ?? '0'
      const milliseconds = Number.parseInt(millisecondsText, 10)
      const divisor = millisecondsText.length === 3 ? 1000 : 100
      result.push({
        time: minutes * 60 + seconds + milliseconds / divisor,
        text,
      })
    }
  }

  return result.sort((left, right) => left.time - right.time)
}

function 是否歌词地址(lrc: string) {
  return /^(https?:)?\/\//.test(lrc) || lrc.startsWith('/') || /\.(lrc|txt)(\?|#|$)/i.test(lrc)
}

async function 加载歌词(track: MusicTrack) {
  状态.value.lyrics = []
  状态.value.currentLyricIndex = -1

  if (!track.lrc) {
    状态.value.lyricStatus = 'none'
    return
  }

  try {
    状态.value.lyricStatus = 'loading'
    const lrcText = 是否歌词地址(track.lrc)
      ? await fetch(track.lrc).then((response) => {
          if (!response.ok) {
            throw new Error(`歌词加载失败：${response.status}`)
          }
          return response.text()
        })
      : track.lrc

    状态.value.lyrics = 解析歌词(lrcText)
    状态.value.lyricStatus = 状态.value.lyrics.length > 0 ? 'loaded' : 'none'
  } catch (error) {
    console.warn('音乐歌词加载失败', error)
    状态.value.lyrics = []
    状态.value.lyricStatus = 'failed'
  }
}

function 读取初始音量() {
  if (typeof window === 'undefined') {
    return 默认音乐音量
  }

  const rawValue = window.localStorage.getItem(音量存储键)
  const savedValue = rawValue === null ? Number.NaN : Number.parseFloat(rawValue)
  return Number.isFinite(savedValue) ? Math.min(1, Math.max(0, savedValue)) : 默认音乐音量
}

function 确保音频实例() {
  if (typeof window === 'undefined') {
    return null
  }

  if (!audio) {
    audio = new Audio()
    audio.preload = 'metadata'
    audio.crossOrigin = 'anonymous'
    audio.volume = 状态.value.volume
  }

  if (!listenersBound) {
    audio.addEventListener('timeupdate', 同步播放时间)
    audio.addEventListener('loadedmetadata', 同步播放时间)
    audio.addEventListener('durationchange', 同步播放时间)
    audio.addEventListener('play', 同步播放状态)
    audio.addEventListener('pause', 同步播放状态)
    audio.addEventListener('ended', 处理播放结束)
    audio.addEventListener('error', 处理播放错误)
    listenersBound = true
  }

  return audio
}

function 获取当前歌曲() {
  return 状态.value.playlist[状态.value.currentIndex] ?? null
}

function 同步播放时间() {
  if (!audio) {
    return
  }

  状态.value.currentTime = Number.isFinite(audio.currentTime) ? audio.currentTime : 0
  状态.value.duration = Number.isFinite(audio.duration) ? audio.duration : 0

  if (状态.value.lyrics.length > 0) {
    let nextIndex = -1
    for (let index = 0; index < 状态.value.lyrics.length; index += 1) {
      if (状态.value.currentTime >= 状态.value.lyrics[index]!.time) {
        nextIndex = index
      } else {
        break
      }
    }
    状态.value.currentLyricIndex = nextIndex
  }
}

function 同步播放状态() {
  if (!audio) {
    return
  }

  状态.value.isPlaying = !audio.paused
}

function 处理播放错误() {
  状态.value.error = '音频播放失败'
  状态.value.isPlaying = false
  console.warn('音乐播放失败', audio?.error)
}

function 获取随机索引() {
  const length = 状态.value.playlist.length
  if (length <= 1) {
    return 0
  }

  let nextIndex = 状态.value.currentIndex
  while (nextIndex === 状态.value.currentIndex) {
    nextIndex = Math.floor(Math.random() * length)
  }
  return nextIndex
}

async function 载入歌曲(index: number, autoPlay = false) {
  const currentAudio = 确保音频实例()
  const track = 状态.value.playlist[index]
  if (!currentAudio || !track) {
    return
  }

  状态.value.currentIndex = index
  状态.value.currentTime = 0
  状态.value.duration = 0
  状态.value.error = null
  currentAudio.src = track.url
  await 加载歌词(track)
  currentAudio.load()

  if (autoPlay) {
    await 播放()
  } else {
    状态.value.isPlaying = false
  }
}

async function 初始化播放器() {
  if (状态.value.initialized) {
    return
  }

  状态.value.volume = 读取初始音量()
  const currentAudio = 确保音频实例()
  if (!currentAudio) {
    return
  }

  currentAudio.volume = 状态.value.volume
  currentAudio.muted = 状态.value.isMuted
  状态.value.initialized = true

  if (状态.value.playlist.length > 0) {
    await 载入歌曲(状态.value.playMode === 'random' ? 获取随机索引() : 0)
  }
}

async function 播放() {
  const currentAudio = 确保音频实例()
  const track = 获取当前歌曲()
  if (!currentAudio || !track) {
    return
  }

  if (!currentAudio.src) {
    currentAudio.src = track.url
  }

  try {
    await currentAudio.play()
    状态.value.isPlaying = true
    状态.value.error = null
  } catch (error) {
    状态.value.isPlaying = false
    状态.value.error = '浏览器阻止了自动播放，请手动点击播放'
    console.warn('音乐播放被浏览器阻止或失败', error)
  }
}

function 暂停() {
  audio?.pause()
  状态.value.isPlaying = false
}

async function 切换播放() {
  if (状态.value.isPlaying) {
    暂停()
    return
  }

  await 播放()
}

async function 下一首(auto = false) {
  if (状态.value.playlist.length === 0) {
    return
  }

  if (auto && 状态.value.playMode === 'one' && audio) {
    audio.currentTime = 0
    await 播放()
    return
  }

  const nextIndex = 状态.value.playMode === 'random'
    ? 获取随机索引()
    : (状态.value.currentIndex + 1) % 状态.value.playlist.length

  await 载入歌曲(nextIndex, true)
}

async function 上一首() {
  if (状态.value.playlist.length === 0) {
    return
  }

  const nextIndex = 状态.value.playMode === 'random'
    ? 获取随机索引()
    : (状态.value.currentIndex - 1 + 状态.value.playlist.length) % 状态.value.playlist.length

  await 载入歌曲(nextIndex, true)
}

function 处理播放结束() {
  void 下一首(true)
}

function 设置音量(volume: number) {
  const nextVolume = Math.min(1, Math.max(0, volume))
  状态.value.volume = nextVolume
  状态.value.isMuted = false

  if (audio) {
    audio.volume = nextVolume
    audio.muted = false
  }

  if (typeof window !== 'undefined') {
    window.localStorage.setItem(音量存储键, nextVolume.toString())
  }
}

function 切换静音() {
  状态.value.isMuted = !状态.value.isMuted
  if (audio) {
    audio.muted = 状态.value.isMuted
  }
}

function 设置进度(percent: number) {
  if (!audio || !Number.isFinite(audio.duration)) {
    return
  }

  audio.currentTime = Math.min(1, Math.max(0, percent)) * audio.duration
}

function 跳转到时间(time: number) {
  if (!audio || !Number.isFinite(audio.duration)) {
    return
  }

  audio.currentTime = Math.min(audio.duration, Math.max(0, time))
}

function 切换播放模式() {
  const modes: MusicPlayMode[] = ['list', 'one', 'random']
  const currentIndex = modes.indexOf(状态.value.playMode)
  状态.value.playMode = modes[(currentIndex + 1) % modes.length] ?? 'list'
}

async function 播放指定歌曲(index: number) {
  if (index === 状态.value.currentIndex) {
    await 切换播放()
    return
  }

  await 载入歌曲(index, true)
}

function 计算进度() {
  if (状态.value.duration <= 0) {
    return 0
  }

  return Math.min(100, Math.max(0, (状态.value.currentTime / 状态.value.duration) * 100))
}

export function 使用音乐播放器() {
  const mounted = ref(false)
  const currentTrack = computed(() => 获取当前歌曲())
  const progress = computed(() => 计算进度())
  const currentTimeText = computed(() => 格式化时间(状态.value.currentTime))
  const durationText = computed(() => 格式化时间(状态.value.duration))

  onMounted(() => {
    mounted.value = true
    void 初始化播放器()
  })

  onBeforeUnmount(() => {
    mounted.value = false
  })

  return {
    state: readonly(状态),
    mounted: readonly(mounted),
    currentTrack,
    progress,
    currentTimeText,
    durationText,
    togglePlay: 切换播放,
    playNext: 下一首,
    playPrev: 上一首,
    cyclePlayMode: 切换播放模式,
    setVolume: 设置音量,
    toggleMute: 切换静音,
    seek: 设置进度,
    seekToTime: 跳转到时间,
    playTrackByIndex: 播放指定歌曲,
  }
}
