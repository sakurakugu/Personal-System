import { computed, ref, type ComputedRef, type Ref } from 'vue'
import {
  创建媒体预览状态,
  计算切换后的预览媒体ID,
} from '../../core/preview'
import type {
  文件展示项,
  资源标识,
} from '../../core/shared'

export function 使用文件页面对话框(options: {
  当前展示文件列表: Ref<文件展示项[]> | ComputedRef<文件展示项[]>
  可预览媒体文件列表: Ref<文件展示项[]> | ComputedRef<文件展示项[]>
  已选资源总数: Ref<number> | ComputedRef<number>
  已选文件夹: Ref<Set<string>>
  已选文件: Ref<Set<string>>
}) {
  const 移动对话框可见 = ref(false)
  const 批量重命名对话框可见 = ref(false)
  const 媒体预览对话框可见 = ref(false)
  const 移动目标目录ID = ref<string | null>(null)
  const 当前预览媒体ID = ref<string | null>(null)
  const 待移动资源列表 = ref<资源标识[]>([])
  const 批量重命名前缀 = ref('资源-')
  const 批量重命名起始序号 = ref(1)
  const 批量重命名位数 = ref(2)
  const 批量重命名保留扩展名 = ref(true)

  const 是否单选资源 = computed(() => options.已选资源总数.value === 1)
  const 当前单文件下载项 = computed<文件展示项 | null>(() => {
    if (options.已选资源总数.value !== 1 || options.已选文件夹.value.size > 0) {
      return null
    }
    const [fileId] = [...options.已选文件.value]
    if (!fileId) {
      return null
    }
    return options.当前展示文件列表.value.find((file) => file.id === fileId) ?? null
  })
  const 下载操作按钮文案 = computed(() => (当前单文件下载项.value ? '直接下载' : '打包下载'))
  const 已选资源下载菜单文案 = computed(() => (当前单文件下载项.value ? '直接下载已选文件' : '下载已选资源'))
  const 已选资源移动文案 = computed(() => (是否单选资源.value ? '移动' : '批量移动'))
  const 已选资源重命名文案 = computed(() => (是否单选资源.value ? '重命名' : '批量重命名'))
  const 已选资源删除文案 = computed(() => (是否单选资源.value ? '删除' : '批量删除'))
  const 已选资源移动菜单文案 = computed(() => (是否单选资源.value ? '移动' : '移动已选资源'))
  const 已选资源删除菜单文案 = computed(() => (是否单选资源.value ? '删除' : '删除已选资源'))
  const 重命名对话框标题 = computed(() => (是否单选资源.value ? '重命名' : '批量重命名'))
  const 当前预览媒体索引 = computed(() => (
    options.可预览媒体文件列表.value.findIndex((file) => file.id === 当前预览媒体ID.value)
  ))
  const 当前预览媒体 = computed(() => {
    const currentIndex = 当前预览媒体索引.value
    if (currentIndex < 0) {
      return null
    }
    return options.可预览媒体文件列表.value[currentIndex] ?? null
  })

  function 打开媒体预览(file: 文件展示项) {
    const previewState = 创建媒体预览状态(file)
    当前预览媒体ID.value = previewState.当前预览媒体ID
    媒体预览对话框可见.value = previewState.媒体预览对话框可见
  }

  function 切换预览媒体(step: number) {
    const nextPreviewMediaId = 计算切换后的预览媒体ID(
      当前预览媒体索引.value,
      step,
      options.可预览媒体文件列表.value,
    )
    if (!nextPreviewMediaId) {
      return
    }
    当前预览媒体ID.value = nextPreviewMediaId
  }

  return {
    移动对话框可见,
    批量重命名对话框可见,
    媒体预览对话框可见,
    移动目标目录ID,
    当前预览媒体ID,
    待移动资源列表,
    批量重命名前缀,
    批量重命名起始序号,
    批量重命名位数,
    批量重命名保留扩展名,
    当前单文件下载项,
    下载操作按钮文案,
    已选资源下载菜单文案,
    已选资源移动文案,
    已选资源重命名文案,
    已选资源删除文案,
    已选资源移动菜单文案,
    已选资源删除菜单文案,
    重命名对话框标题,
    当前预览媒体索引,
    当前预览媒体,
    打开媒体预览,
    切换预览媒体,
  }
}
