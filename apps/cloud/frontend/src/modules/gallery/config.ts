export interface GalleryAlbum {
  id: string
  name: string
  description?: string
  date?: string
  location?: string
  tags?: string[]
  cover?: string
}

export interface GalleryConfig {
  albums: GalleryAlbum[]
  columnWidth: number
}

export const galleryConfig: GalleryConfig = {
  albums: [
    {
      id: 'firefly-2026',
      name: '可爱流萤',
      description: '飞萤之火自无梦的长夜亮起，绽放在终竟的明天。',
      location: '崩坏：星穹铁道',
      date: '2026-01-01',
      tags: ['崩坏星穹铁道', '流萤'],
    },
  ],
  columnWidth: 240,
}
