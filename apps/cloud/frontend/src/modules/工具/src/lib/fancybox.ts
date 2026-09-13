export type 图片预览项 = {
  src: string
  thumbSrc: string
  type: 'image'
  caption: string
}

export type 图片预览实例 = {
  close: () => void
  show: (items: 图片预览项[], options?: Record<string, unknown>) => void
}

let fancybox实例Promise: Promise<图片预览实例> | null = null

export function 获取图片预览实例() {
  if (!fancybox实例Promise) {
    fancybox实例Promise = Promise.all([
      import('@fancyapps/ui'),
      import('@fancyapps/ui/dist/fancybox/fancybox.css'),
    ]).then(([module]) => module.Fancybox as unknown as 图片预览实例)
  }

  return fancybox实例Promise
}
