import { ref, type Ref } from 'vue'
import type {
  MilkdownMarkdownImagePayload,
  MilkdownMarkdownImageUploader,
} from './MilkdownMarkdown编辑器类型'
import type { 图片裁剪矩形 } from './MilkdownMarkdown图片裁剪弹窗.vue'

interface 使用MilkdownMarkdown图片上传选项 {
  fileInputRef: Ref<HTMLInputElement | null>
  cropFileInputRef: Ref<HTMLInputElement | null>
  获取上传图片函数: () => MilkdownMarkdownImageUploader | undefined
  插入Markdown: (markdown: string) => void
  聚焦编辑器: () => void
  报告上传错误: (error: unknown) => void
}

export function 使用MilkdownMarkdown图片上传(options: 使用MilkdownMarkdown图片上传选项) {
  const isUploading = ref(false)
  const imageCropDialogVisible = ref(false)
  const imageCropPreviewUrl = ref('')
  const imageCropSourceFile = ref<File | null>(null)
  const imageCropNaturalSize = ref({ width: 0, height: 0 })
  const imageCropRect = ref<图片裁剪矩形>({ x: 0.08, y: 0.08, width: 0.84, height: 0.84 })

  function openImagePicker() {
    if (!options.获取上传图片函数() || isUploading.value) {
      return
    }

    options.fileInputRef.value?.click()
  }

  function handleFileInputChange(event: Event) {
    const input = event.target
    if (!(input instanceof HTMLInputElement)) {
      return
    }

    void uploadAndInsertImages(Array.from(input.files ?? []))
    input.value = ''
  }

  function insertImageLink() {
    const url = window.prompt('请输入图片地址')
    if (!url?.trim()) {
      return
    }

    const alt = window.prompt('请输入图片说明', '') ?? ''
    options.插入Markdown(`\n![${escapeMarkdownImageAlt(alt)}](${url.trim()})\n`)
    options.聚焦编辑器()
  }

  function escapeMarkdownImageAlt(value: string): string {
    return value
      .replace(/\\/g, '\\\\')
      .replace(/\[/g, '\\[')
      .replace(/\]/g, '\\]')
      .replace(/\r?\n/g, ' ')
      .trim()
  }

  function openCropImagePicker() {
    if (!options.获取上传图片函数() || isUploading.value) {
      return
    }

    options.cropFileInputRef.value?.click()
  }

  function handleCropFileInputChange(event: Event) {
    const input = event.target
    if (!(input instanceof HTMLInputElement)) {
      return
    }

    const file = Array.from(input.files ?? []).find((item) => item.type.startsWith('image/'))
    input.value = ''
    if (!file) {
      return
    }

    void loadImageCropFile(file)
  }

  async function loadImageCropFile(file: File) {
    releaseImageCropPreviewUrl()
    const previewUrl = URL.createObjectURL(file)
    const image = new window.Image()
    image.decoding = 'async'
    image.src = previewUrl

    try {
      await image.decode()
    } catch (error) {
      URL.revokeObjectURL(previewUrl)
      options.报告上传错误(error)
      return
    }

    imageCropPreviewUrl.value = previewUrl
    imageCropSourceFile.value = file
    imageCropNaturalSize.value = {
      width: image.naturalWidth || 1,
      height: image.naturalHeight || 1,
    }
    resetImageCropRect()
    imageCropDialogVisible.value = true
  }

  function releaseImageCropPreviewUrl() {
    if (imageCropPreviewUrl.value) {
      URL.revokeObjectURL(imageCropPreviewUrl.value)
    }
    imageCropPreviewUrl.value = ''
  }

  function closeImageCropDialog() {
    imageCropDialogVisible.value = false
    imageCropSourceFile.value = null
    releaseImageCropPreviewUrl()
  }

  function resetImageCropRect() {
    imageCropRect.value = {
      x: 0.08,
      y: 0.08,
      width: 0.84,
      height: 0.84,
    }
  }

  async function confirmImageCropUpload() {
    try {
      const croppedFile = await buildCroppedImageFile()
      if (!croppedFile) {
        return
      }

      closeImageCropDialog()
      await uploadAndInsertImages([croppedFile])
    } catch (error) {
      options.报告上传错误(error)
    }
  }

  async function buildCroppedImageFile(): Promise<File | null> {
    const sourceFile = imageCropSourceFile.value
    if (!sourceFile || !imageCropPreviewUrl.value) {
      return null
    }

    const image = new window.Image()
    image.decoding = 'async'
    image.src = imageCropPreviewUrl.value
    await image.decode()

    const naturalSize = imageCropNaturalSize.value
    const crop = imageCropRect.value
    const sourceX = Math.round(crop.x * naturalSize.width)
    const sourceY = Math.round(crop.y * naturalSize.height)
    const sourceWidth = Math.max(1, Math.round(crop.width * naturalSize.width))
    const sourceHeight = Math.max(1, Math.round(crop.height * naturalSize.height))
    const canvas = document.createElement('canvas')
    canvas.width = sourceWidth
    canvas.height = sourceHeight

    const context = canvas.getContext('2d')
    if (!context) {
      throw new Error('canvas 上下文创建失败')
    }

    context.imageSmoothingEnabled = true
    context.imageSmoothingQuality = 'high'
    context.drawImage(image, sourceX, sourceY, sourceWidth, sourceHeight, 0, 0, sourceWidth, sourceHeight)

    const outputType = sourceFile.type === 'image/jpeg' ? 'image/jpeg' : 'image/png'
    const blob = await new Promise<Blob | null>((resolve) => {
      canvas.toBlob(resolve, outputType, 0.92)
    })
    if (!blob) {
      throw new Error('图片裁剪失败')
    }

    const extension = outputType === 'image/jpeg' ? 'jpg' : 'png'
    const baseName = sourceFile.name.replace(/\.[^.]+$/, '').trim() || 'cropped-image'
    return new File([blob], `${baseName}-cropped.${extension}`, { type: outputType })
  }

  function handleEditorPaste(event: ClipboardEvent) {
    const files = Array.from(event.clipboardData?.files ?? []).filter((file) => file.type.startsWith('image/'))
    if (files.length === 0) {
      return
    }

    event.preventDefault()
    void uploadAndInsertImages(files)
  }

  function handleEditorDrop(event: DragEvent) {
    const files = Array.from(event.dataTransfer?.files ?? []).filter((file) => file.type.startsWith('image/'))
    if (files.length === 0) {
      return
    }

    event.preventDefault()
    void uploadAndInsertImages(files)
  }

  async function uploadAndInsertImages(files: File[]) {
    const uploadImages = options.获取上传图片函数()
    if (!uploadImages || files.length === 0) {
      return
    }

    isUploading.value = true
    try {
      const uploadedImages = await uploadImages(files)
      const markdown = uploadedImages
        .map((image) => formatMarkdownImage(image))
        .filter((value) => value.length > 0)
        .join('\n\n')

      if (markdown) {
        options.插入Markdown(`\n${markdown}\n`)
      }
    } catch (error) {
      options.报告上传错误(error)
    } finally {
      isUploading.value = false
    }
  }

  function formatMarkdownImage(image: MilkdownMarkdownImagePayload): string {
    const alt = image.alt ?? ''
    const title = image.title?.trim()
    const titlePart = title ? ` "${title.replace(/"/g, '\\"')}"` : ''
    return `![${alt}](${image.url}${titlePart})`
  }

  return {
    isUploading,
    imageCropDialogVisible,
    imageCropPreviewUrl,
    imageCropNaturalSize,
    imageCropRect,
    openImagePicker,
    handleFileInputChange,
    insertImageLink,
    openCropImagePicker,
    handleCropFileInputChange,
    releaseImageCropPreviewUrl,
    closeImageCropDialog,
    resetImageCropRect,
    confirmImageCropUpload,
    handleEditorPaste,
    handleEditorDrop,
  }
}
