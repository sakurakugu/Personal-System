import { galleryManifest } from './manifest'
import type { GalleryAlbum } from './config'

export function 扫描相册照片(albumId: string): string[] {
  return galleryManifest[albumId] || []
}

export function 获取相册封面(album: GalleryAlbum, photos: string[]): string {
  if (album.cover) return album.cover
  const coverFile = photos.find((p) => /\/cover\./i.test(p))
  return coverFile || photos[0] || ''
}
