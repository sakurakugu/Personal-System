import { readonly, ref } from 'vue'
import api from '../utils/api'

export interface BannerImagesResponse {
  images: string[]
}

/**
 * 从后端接口获取 banner 图片列表
 */
export function useBannerImages() {
  const images = ref<string[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function load() {
    loading.value = true
    error.value = null
    try {
      const { data } = await api.get<BannerImagesResponse>('/banner-images')
      images.value = data.images
    } catch {
      error.value = '加载轮播图失败'
      images.value = []
    } finally {
      loading.value = false
    }
  }

  load()

  return {
    images: readonly(images),
    loading: readonly(loading),
    error: readonly(error),
    load,
  }
}
