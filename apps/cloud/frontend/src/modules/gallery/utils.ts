import { galleryManifest } from './manifest'
import type { GalleryAlbum } from './config'

export function scanAlbumPhotos(albumId: string): string[] {
  return galleryManifest[albumId] || []
}

export function getAlbumCover(album: GalleryAlbum, photos: string[]): string {
  if (album.cover) return album.cover
  const coverFile = photos.find((p) => /\/cover\./i.test(p))
  return coverFile || photos[0] || ''
}
