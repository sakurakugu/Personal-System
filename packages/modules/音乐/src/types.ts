export type MusicPlayMode = 'list' | 'one' | 'random'

export type MusicLyricLine = {
  time: number
  text: string
}

export type MusicTrack = {
  id: string
  name: string
  artist: string
  url: string
  cover?: string
  lrc?: string
}
