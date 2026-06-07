export interface VditorMarkdownImagePayload {
  url: string
  alt?: string
  title?: string
}

export type VditorMarkdownImageUploader = (
  files: File[],
) => Promise<VditorMarkdownImagePayload[]>

export function 创建Vditor图片上传配置(
  uploadImages: VditorMarkdownImageUploader | undefined,
  onError: (error: unknown) => void,
) {
  if (!uploadImages) {
    return undefined
  }

  return {
    accept: 'image/*',
    multiple: true,
    handler: async (files: File[]) => {
      try {
        const uploadedImages = await uploadImages(files)
        return uploadedImages
          .map((image) => 格式化Markdown图片(image))
          .filter((value) => value.length > 0)
          .join('\n\n')
      } catch (error) {
        onError(error)
        return '图片上传失败'
      }
    },
  }
}

export function 格式化Markdown图片(image: VditorMarkdownImagePayload): string {
  const alt = image.alt ?? ''
  const title = image.title?.trim()
  const titlePart = title ? ` "${title.replace(/"/g, '\\"')}"` : ''
  return `![${alt}](${image.url}${titlePart})`
}
