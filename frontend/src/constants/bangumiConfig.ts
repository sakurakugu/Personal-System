export type BangumiCategoryId = 'anime' | 'book' | 'music' | 'game' | 'real'

export interface BangumiCategoryConfig {
  id: BangumiCategoryId
  name: string
  subjectType: number
  enabled: boolean
}

export interface BangumiConfig {
  userId: string
  apiBaseUrl: string
  requestLimit: number
  categories: BangumiCategoryConfig[]
}

export const bangumiConfig: BangumiConfig = {
  // 请填写你的 Bangumi 用户名，例如："sakurakugu"
  userId: '',
  apiBaseUrl: 'https://api.bgm.tv',
  requestLimit: 50,
  categories: [
    { id: 'anime', name: '动画', subjectType: 2, enabled: true },
    { id: 'book', name: '书籍', subjectType: 1, enabled: true },
    { id: 'music', name: '音乐', subjectType: 3, enabled: true },
    { id: 'game', name: '游戏', subjectType: 4, enabled: true },
    { id: 'real', name: '三次元', subjectType: 6, enabled: false },
  ],
}