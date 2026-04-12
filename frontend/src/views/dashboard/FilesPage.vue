<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import type { ComponentPublicInstance } from 'vue'
import { useRouter } from 'vue-router'
import { Icon, addCollection } from '@iconify/vue'
import { icons as codiconIcons } from '@iconify-json/codicon'
import type { TreeInstance } from 'element-plus'
import {
  ElBreadcrumb,
  ElBreadcrumbItem,
  ElButton,
  ElCard,
  ElCheckbox,
  ElEmpty,
  ElIcon,
  ElInput,
  ElInputNumber,
  ElMessage,
  ElMessageBox,
  ElOption,
  ElSelect,
  ElSkeleton,
  ElSpace,
  ElTag,
  ElText,
  ElTree,
} from 'element-plus'
import {
  Document,
  Folder,
  FolderOpened,
  Loading,
  Picture,
  Search,
  VideoPlay,
} from '@element-plus/icons-vue'
import BaseDialog from '../../components/BaseDialog.vue'
import {
  createFolder as requestCreateFolder,
  deleteFile as requestDeleteFile,
  deleteFolder as requestDeleteFolder,
  downloadArchive as requestDownloadArchive,
  downloadFile as requestDownloadFile,
  fetchExplorer,
  moveFile as requestMoveFile,
  moveFolder as requestMoveFolder,
  renameFile as requestRenameFile,
  renameFolder as requestRenameFolder,
  searchFiles as requestSearchFiles,
  uploadFile as requestUploadFile,
} from '../../features/files/api'
import type {
  FileBreadcrumbItem,
  FileExplorerData,
  FileFolderItem,
  FileItem,
  FileSearchData,
  FileSearchFileItem,
  FileSearchFolderItem,
  FileTreeNode,
} from '../../features/files/types'
import { getApiErrorMessage } from '../../utils/api'
import { extractManagedFilePath, resolveManagedFileUrl } from '../../utils/managedFile'

addCollection(codiconIcons)

type 资源类型 = 'folder' | 'file'
type 右键菜单范围 = 'blank' | 'folder' | 'file'
type 排序方式 = 'name-asc' | 'name-desc' | 'time-desc' | 'time-asc' | 'size-desc' | 'size-asc'
type 搜索范围 = 'current' | 'global'
type 文件夹展示项 = FileFolderItem | FileSearchFolderItem
type 文件展示项 = FileItem | FileSearchFileItem
type 资源展示项 =
  | { type: 'folder'; id: string; item: 文件夹展示项 }
  | { type: 'file'; id: string; item: 文件展示项 }
type 带目录路径文件 = globalThis.File & {
  webkitRelativePath?: string
}

interface 资源标识 {
  type: 资源类型
  id: string
}

interface 目录树节点 extends FileTreeNode {
  isRoot?: boolean
  isArticleImages?: boolean
  isDraft?: boolean
}

interface 右键菜单状态 {
  visible: boolean
  x: number
  y: number
  scope: 右键菜单范围
  source: 'blank' | 'tree' | 'list'
  resource: 资源标识 | null
}

interface 新建目录草稿 {
  id: string
  parentId: string | null
  name: string
}

interface 右侧新建文件夹草稿 {
  id: string
  parentId: string | null
  name: string
}

interface 重命名目录草稿 {
  id: string
  name: string
  originalName: string
}

interface 列表重命名草稿 {
  type: 资源类型
  id: string
  name: string
  originalName: string
}

const 根目录节点键 = '__root__'
const 文章图片节点键 = '__article_images__'
const 拖拽数据类型 = 'application/x-web-system-resource'
const 根目录名称 = '全部文件'
const 最小目录树宽度 = 220
const 最大目录树宽度 = 520
const 最小主区域宽度 = 420
const 分隔线宽度 = 20
const 文章图片标签 = '文章图片'
interface 拉取资源选项 {
  静默?: boolean
}

const 资源数据 = ref<FileExplorerData | null>(null)
const 首次加载中 = ref(true)
const 刷新中 = ref(false)
const 正在上传 = ref(false)
const 搜索关键词 = ref('')
const 搜索范围值 = ref<搜索范围>('current')
const 全局搜索中 = ref(false)
const 全局搜索结果 = ref<FileSearchData>({ folders: [], files: [] })
const 当前排序 = ref<排序方式>('name-asc')
const 当前目录ID = ref<string | null>(null)
const 当前拖拽资源 = ref<资源标识 | null>(null)
const 已选文件夹 = ref<Set<string>>(new Set())
const 已选文件 = ref<Set<string>>(new Set())
const 移动对话框可见 = ref(false)
const 批量重命名对话框可见 = ref(false)
const 媒体预览对话框可见 = ref(false)
const 移动目标目录ID = ref<string | null>(null)
const 当前预览媒体ID = ref<string | null>(null)
const 待移动资源列表 = ref<资源标识[]>([])
const 文件上传输入框 = ref<globalThis.HTMLInputElement | null>(null)
const 目录上传输入框 = ref<globalThis.HTMLInputElement | null>(null)
const 浏览器布局容器 = ref<globalThis.HTMLElement | null>(null)
const 目录树引用 = ref<TreeInstance | null>(null)
const 新建目录输入框 = ref<globalThis.HTMLInputElement | null>(null)
const 重命名目录输入框 = ref<globalThis.HTMLInputElement | null>(null)
const 列表重命名输入框 = ref<globalThis.HTMLInputElement | null>(null)
const 右侧新建文件夹输入框 = ref<globalThis.HTMLInputElement | null>(null)
const 批量重命名前缀 = ref('资源-')
const 批量重命名起始序号 = ref(1)
const 批量重命名位数 = ref(2)
const 批量重命名保留扩展名 = ref(true)
const 目录树宽度 = ref(280)
const 正在拖动分隔线 = ref(false)
const 当前资源视图 = ref<'files' | 'article-images'>('files')
const 新建目录草稿状态 = ref<新建目录草稿 | null>(null)
const 正在提交新建目录 = ref(false)
const 右侧新建文件夹草稿状态 = ref<右侧新建文件夹草稿 | null>(null)
const 正在提交右侧新建文件夹 = ref(false)
const 重命名目录草稿状态 = ref<重命名目录草稿 | null>(null)
const 正在提交重命名目录 = ref(false)
const 列表重命名草稿状态 = ref<列表重命名草稿 | null>(null)
const 正在提交列表重命名 = ref(false)
const 右键菜单 = ref<右键菜单状态>({
  visible: false,
  x: 0,
  y: 0,
  scope: 'blank',
  source: 'blank',
  resource: null,
})
let 全局搜索定时器: ReturnType<typeof window.setTimeout> | null = null
let 全局搜索序号 = 0
const 路由 = useRouter()
const 新建目录临时节点键 = '__creating_folder__'
const 右侧新建文件夹临时资源键 = '__creating_folder_in_list__'

const 当前目录 = computed(() => 资源数据.value?.current_folder ?? null)
const 是否显示骨架屏 = computed(() => 首次加载中.value && 资源数据.value === null)
const 当前是文章图片视图 = computed(() => 当前资源视图.value === 'article-images')
const 导航栏列表 = computed<FileBreadcrumbItem[]>(() => (
  当前是文章图片视图.value
    ? [{ id: 文章图片节点键, name: 文章图片标签 }]
    : (资源数据.value?.breadcrumbs ?? [{ id: null, name: 根目录名称 }])
))
const 原始子文件夹列表 = computed<FileFolderItem[]>(() => 资源数据.value?.folders ?? [])
const 全部普通文件列表 = computed<FileItem[]>(() => (
  (资源数据.value?.files ?? []).filter((file) => file.purpose === 'file')
))
const 全部文章图片列表 = computed<FileItem[]>(() => (
  (资源数据.value?.files ?? []).filter((file) => file.purpose === 'article_image')
))
const 原始文件列表 = computed<FileItem[]>(() => (
  当前是文章图片视图.value ? 全部文章图片列表.value : 全部普通文件列表.value
))
const 当前目录名称 = computed(() => (
  当前是文章图片视图.value ? 文章图片标签 : (当前目录.value?.name ?? 根目录名称)
))
const 选中目录树节点键 = computed(() => (
  当前是文章图片视图.value ? 文章图片节点键 : (当前目录ID.value ?? 根目录节点键)
))
const 新建目录名称 = computed({
  get: () => 新建目录草稿状态.value?.name ?? '',
  set: (value: string) => {
    if (!新建目录草稿状态.value) {
      return
    }
    新建目录草稿状态.value = {
      ...新建目录草稿状态.value,
      name: value,
    }
  },
})
const 右侧新建文件夹名称 = computed({
  get: () => 右侧新建文件夹草稿状态.value?.name ?? '',
  set: (value: string) => {
    if (!右侧新建文件夹草稿状态.value) {
      return
    }
    右侧新建文件夹草稿状态.value = {
      ...右侧新建文件夹草稿状态.value,
      name: value,
    }
  },
})
const 重命名目录名称 = computed({
  get: () => 重命名目录草稿状态.value?.name ?? '',
  set: (value: string) => {
    if (!重命名目录草稿状态.value) {
      return
    }
    重命名目录草稿状态.value = {
      ...重命名目录草稿状态.value,
      name: value,
    }
  },
})
const 列表重命名名称 = computed({
  get: () => 列表重命名草稿状态.value?.name ?? '',
  set: (value: string) => {
    if (!列表重命名草稿状态.value) {
      return
    }
    列表重命名草稿状态.value = {
      ...列表重命名草稿状态.value,
      name: value,
    }
  },
})
const 普通目录树数据 = computed<目录树节点[]>(() => (
  插入新建目录节点(资源数据.value?.tree ?? [], 新建目录草稿状态.value)
))
const 目录树数据 = computed<目录树节点[]>(() => ([
  {
    id: 根目录节点键,
    parent_id: null,
    name: 根目录名称,
    isRoot: true,
    children: 普通目录树数据.value,
  },
  {
    id: 文章图片节点键,
    parent_id: null,
    name: 文章图片标签,
    isArticleImages: true,
    children: [],
  },
]))
const 排序选项 = [
  { label: '名称 A-Z', value: 'name-asc' },
  { label: '名称 Z-A', value: 'name-desc' },
  { label: '时间 新到旧', value: 'time-desc' },
  { label: '时间 旧到新', value: 'time-asc' },
  { label: '大小 大到小', value: 'size-desc' },
  { label: '大小 小到大', value: 'size-asc' },
] as const
const 搜索范围选项 = [
  { label: '当前目录', value: 'current' },
  { label: '跨目录', value: 'global' },
] as const

function 是否匹配搜索关键词(name: string) {
  const keyword = 搜索关键词.value.trim().toLowerCase()
  if (!keyword) {
    return true
  }
  return name.toLowerCase().includes(keyword)
}

function 比较文本(a: string, b: string) {
  return a.localeCompare(b, 'zh-CN', { numeric: true, sensitivity: 'base' })
}

function 比较时间(a: string, b: string) {
  return new Date(a).getTime() - new Date(b).getTime()
}

function 排序文件夹列表(source: FileFolderItem[]) {
  const sorted = [...source]
  sorted.sort((left, right) => {
    switch (当前排序.value) {
      case 'name-desc':
        return 比较文本(right.name, left.name)
      case 'time-desc':
        return 比较时间(right.updated_at, left.updated_at)
      case 'time-asc':
        return 比较时间(left.updated_at, right.updated_at)
      default:
        return 比较文本(left.name, right.name)
    }
  })
  return sorted
}

function 排序文件列表(source: FileItem[]) {
  const sorted = [...source]
  sorted.sort((left, right) => {
    switch (当前排序.value) {
      case 'name-desc':
        return 比较文本(right.original_name, left.original_name)
      case 'time-desc':
        return 比较时间(right.created_at, left.created_at)
      case 'time-asc':
        return 比较时间(left.created_at, right.created_at)
      case 'size-desc':
        return right.size - left.size
      case 'size-asc':
        return left.size - right.size
      default:
        return 比较文本(left.original_name, right.original_name)
    }
  })
  return sorted
}

function 比较资源类型(left: 资源展示项, right: 资源展示项) {
  if (left.type === right.type) {
    return 0
  }
  return left.type === 'folder' ? -1 : 1
}

function 获取资源名称(resource: 资源展示项) {
  return resource.type === 'folder' ? resource.item.name : resource.item.original_name
}

function 获取资源时间(resource: 资源展示项) {
  return resource.type === 'folder' ? resource.item.updated_at : resource.item.created_at
}

function 排序资源列表(folders: 文件夹展示项[], files: 文件展示项[]) {
  const sorted = [
    ...folders.map((folder) => ({ type: 'folder', id: folder.id, item: folder } as const)),
    ...files.map((file) => ({ type: 'file', id: file.id, item: file } as const)),
  ]
  sorted.sort((left, right) => {
    switch (当前排序.value) {
      case 'name-desc': {
        const result = 比较文本(获取资源名称(right), 获取资源名称(left))
        return result || 比较资源类型(left, right)
      }
      case 'time-desc': {
        const result = 比较时间(获取资源时间(right), 获取资源时间(left))
        return result || 比较资源类型(left, right) || 比较文本(获取资源名称(left), 获取资源名称(right))
      }
      case 'time-asc': {
        const result = 比较时间(获取资源时间(left), 获取资源时间(right))
        return result || 比较资源类型(left, right) || 比较文本(获取资源名称(left), 获取资源名称(right))
      }
      case 'size-desc':
      case 'size-asc': {
        if (left.type === 'folder' || right.type === 'folder') {
          return 比较资源类型(left, right) || 比较文本(获取资源名称(left), 获取资源名称(right))
        }
        const result = 当前排序.value === 'size-desc'
          ? right.item.size - left.item.size
          : left.item.size - right.item.size
        return result || 比较文本(left.item.original_name, right.item.original_name)
      }
      default: {
        const result = 比较文本(获取资源名称(left), 获取资源名称(right))
        return result || 比较资源类型(left, right)
      }
    }
  })
  return sorted
}

const 子文件夹列表 = computed<FileFolderItem[]>(() => (
  当前是文章图片视图.value
    ? []
    : 排序文件夹列表(原始子文件夹列表.value.filter((folder) => 是否匹配搜索关键词(folder.name)))
))
const 文件列表 = computed<FileItem[]>(() => 排序文件列表(
  原始文件列表.value.filter((file) => 是否匹配搜索关键词(file.original_name)),
))
const 当前可在右侧新建文件夹 = computed(() => !当前是文章图片视图.value && !是否全局搜索模式.value)
const 当前展示文件夹列表 = computed<文件夹展示项[]>(() => (
  是否全局搜索模式.value ? 全局搜索文件夹结果.value : 子文件夹列表.value
))
const 当前展示文件列表 = computed<文件展示项[]>(() => (
  是否全局搜索模式.value ? 全局搜索文件结果.value : 文件列表.value
))
const 右侧新建文件夹资源 = computed<资源展示项 | null>(() => {
  const draft = 右侧新建文件夹草稿状态.value
  if (!draft || !当前可在右侧新建文件夹.value || draft.parentId !== 当前目录ID.value) {
    return null
  }
  return {
    type: 'folder',
    id: draft.id,
    item: {
      id: draft.id,
      parent_id: draft.parentId,
      name: draft.name,
      created_at: '',
      updated_at: '',
    },
  }
})
const 当前展示资源列表 = computed<资源展示项[]>(() => {
  const list = 排序资源列表(当前展示文件夹列表.value, 当前展示文件列表.value)
  return 右侧新建文件夹资源.value ? [右侧新建文件夹资源.value, ...list] : list
})
const 当前目录文件夹总数 = computed(() => (当前是文章图片视图.value ? 0 : 原始子文件夹列表.value.length))
const 当前目录文件总数 = computed(() => 原始文件列表.value.length)
const 当前页资源总数 = computed(() => 当前展示资源列表.value.length)
const 已选资源总数 = computed(() => 已选文件夹.value.size + 已选文件.value.size)
const 当前选择可移动 = computed(() => {
  const selectedResources = 读取当前已选资源()
  return selectedResources.length > 0 && selectedResources.every((resource) => 是否资源支持移动(resource))
})
const 当前空状态描述 = computed(() => {
  if (是否全局搜索模式.value) {
    return 全局搜索中.value ? '正在跨目录搜索...' : '没有找到匹配的资源'
  }
  if (当前是文章图片视图.value) {
    return 搜索关键词.value.trim() ? '当前文章图片筛选无结果' : '当前还没有文章图片'
  }
  return 搜索关键词.value.trim() ? '当前筛选无结果' : '当前目录为空'
})
const 当前页已选文件夹数 = computed(() => 当前展示文件夹列表.value.filter((folder) => 已选文件夹.value.has(folder.id)).length)
const 当前页已选文件数 = computed(() => 当前展示文件列表.value.filter((file) => 已选文件.value.has(file.id)).length)
const 是否已全选当前页 = computed(() => (
  当前页资源总数.value > 0
  && 当前页已选文件夹数.value === 当前展示文件夹列表.value.length
  && 当前页已选文件数.value === 当前展示文件列表.value.length
))
const 是否全局搜索模式 = computed(() => 搜索范围值.value === 'global' && 搜索关键词.value.trim().length > 0)
const 全局搜索文件夹结果 = computed<FileSearchFolderItem[]>(() => 全局搜索结果.value.folders)
const 全局搜索文件结果 = computed<FileSearchFileItem[]>(() => 全局搜索结果.value.files)
const 全局搜索结果总数 = computed(() => 全局搜索文件夹结果.value.length + 全局搜索文件结果.value.length)
const 可预览媒体文件列表 = computed<文件展示项[]>(() => 当前展示文件列表.value.filter((file) => 是否可预览媒体(file)))
const 当前单文件下载项 = computed<文件展示项 | null>(() => {
  if (已选资源总数.value !== 1 || 已选文件夹.value.size > 0) {
    return null
  }
  const [fileId] = [...已选文件.value]
  if (!fileId) {
    return null
  }
  return 查找文件展示项(fileId)
})
const 搜索框占位文案 = computed(() => (
  搜索范围值.value === 'global'
    ? '跨目录搜索文件夹和文件'
    : (当前是文章图片视图.value ? '搜索当前文章图片' : '搜索当前目录中的文件夹和文件')
))
const 浏览器布局样式 = computed<Record<string, string>>(() => ({
  '--explorer-sidebar-width': `${目录树宽度.value}px`,
}))
const 是否搜索中 = computed(() => 搜索关键词.value.trim().length > 0)
const 搜索统计文案 = computed(() => {
  if (搜索范围值.value === 'global') {
    if (全局搜索中.value) {
      return `正在搜索“${搜索关键词.value.trim()}”`
    }
    return `共找到 ${全局搜索文件夹结果.value.length} 个文件夹、${全局搜索文件结果.value.length} 个文件`
  }
  if (当前是文章图片视图.value) {
    return `当前显示 ${文件列表.value.length} 个文章图片`
  }
  return `当前显示 ${子文件夹列表.value.length} 个文件夹、${文件列表.value.length} 个文件`
})
const 主区域描述 = computed(() => {
  if (是否全局搜索模式.value) {
    return `关键词“${搜索关键词.value.trim()}”共匹配 ${全局搜索结果总数.value} 项资源。`
  }
  if (当前是文章图片视图.value) {
    return `这里汇总文章编辑器上传的 ${当前目录文件总数.value} 个图片资源。`
  }
  return `当前目录包含 ${当前目录文件夹总数.value} 个文件夹、${当前目录文件总数.value} 个文件。`
})
const 底部状态文案 = computed(() => (是否搜索中.value ? 搜索统计文案.value : 主区域描述.value))
const 是否单选资源 = computed(() => 已选资源总数.value === 1)
const 下载操作按钮文案 = computed(() => (当前单文件下载项.value ? '直接下载' : '打包下载'))
const 已选资源下载菜单文案 = computed(() => (当前单文件下载项.value ? '直接下载已选文件' : '下载已选资源'))
const 已选资源移动文案 = computed(() => (是否单选资源.value ? '移动' : '批量移动'))
const 已选资源重命名文案 = computed(() => (是否单选资源.value ? '重命名' : '批量重命名'))
const 已选资源删除文案 = computed(() => (是否单选资源.value ? '删除' : '批量删除'))
const 已选资源移动菜单文案 = computed(() => (是否单选资源.value ? '移动' : '移动已选资源'))
const 已选资源删除菜单文案 = computed(() => (是否单选资源.value ? '删除' : '删除已选资源'))
const 重命名对话框标题 = computed(() => (是否单选资源.value ? '重命名' : '批量重命名'))
const 当前预览媒体索引 = computed(() => 可预览媒体文件列表.value.findIndex((file) => file.id === 当前预览媒体ID.value))
const 当前预览媒体 = computed(() => {
  const currentIndex = 当前预览媒体索引.value
  if (currentIndex < 0) {
    return null
  }
  return 可预览媒体文件列表.value[currentIndex] ?? null
})
const 右键菜单文件 = computed<文件展示项 | null>(() => {
  if (右键菜单.value.scope !== 'file' || 右键菜单.value.resource?.type !== 'file') {
    return null
  }
  return 当前展示文件列表.value.find((file) => file.id === 右键菜单.value.resource?.id) ?? null
})
const 右键菜单文件夹 = computed<文件夹展示项 | null>(() => {
  if (右键菜单.value.scope !== 'folder' || 右键菜单.value.resource?.type !== 'folder') {
    return null
  }
  return 查找文件夹展示项(右键菜单.value.resource.id)
})

function 计算最大目录树宽度() {
  const layoutWidth = 浏览器布局容器.value?.clientWidth ?? 0
  if (layoutWidth <= 0) {
    return 最大目录树宽度
  }
  return Math.max(
    最小目录树宽度,
    Math.min(最大目录树宽度, layoutWidth - 最小主区域宽度 - 分隔线宽度),
  )
}

function 约束目录树宽度(width: number) {
  return Math.min(Math.max(width, 最小目录树宽度), 计算最大目录树宽度())
}

function 同步目录树宽度() {
  目录树宽度.value = 约束目录树宽度(目录树宽度.value)
}

function 开始拖动分隔线(event: globalThis.PointerEvent) {
  if (window.innerWidth <= 960) {
    return
  }
  event.preventDefault()
  正在拖动分隔线.value = true
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
}

function 处理拖动分隔线(event: globalThis.PointerEvent) {
  if (!正在拖动分隔线.value || !浏览器布局容器.value) {
    return
  }
  const layoutRect = 浏览器布局容器.value.getBoundingClientRect()
  目录树宽度.value = 约束目录树宽度(event.clientX - layoutRect.left)
}

function 停止拖动分隔线() {
  if (!正在拖动分隔线.value) {
    return
  }
  正在拖动分隔线.value = false
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
}

function 处理窗口尺寸变化() {
  关闭右键菜单()
  if (window.innerWidth <= 960) {
    停止拖动分隔线()
  }
  同步目录树宽度()
}

function 处理窗口失焦() {
  关闭右键菜单()
  停止拖动分隔线()
}

onMounted(() => {
  window.addEventListener('click', 关闭右键菜单)
  window.addEventListener('resize', 处理窗口尺寸变化)
  window.addEventListener('blur', 处理窗口失焦)
  window.addEventListener('pointermove', 处理拖动分隔线)
  window.addEventListener('pointerup', 停止拖动分隔线)
  window.addEventListener('pointercancel', 停止拖动分隔线)
  window.requestAnimationFrame(同步目录树宽度)
  void 拉取资源()
})

onBeforeUnmount(() => {
  window.removeEventListener('click', 关闭右键菜单)
  window.removeEventListener('resize', 处理窗口尺寸变化)
  window.removeEventListener('blur', 处理窗口失焦)
  window.removeEventListener('pointermove', 处理拖动分隔线)
  window.removeEventListener('pointerup', 停止拖动分隔线)
  window.removeEventListener('pointercancel', 停止拖动分隔线)
  停止拖动分隔线()
  if (全局搜索定时器 !== null) {
    window.clearTimeout(全局搜索定时器)
    全局搜索定时器 = null
  }
})

function 清空选择() {
  已选文件夹.value = new Set()
  已选文件.value = new Set()
}

function 应用资源数据(data: FileExplorerData) {
  资源数据.value = data
  当前目录ID.value = data.current_folder?.id ?? null
  清空选择()
}

async function 拉取资源(folderId: string | null = 当前目录ID.value, options: 拉取资源选项 = {}) {
  const 静默 = options.静默 ?? false
  if (静默) {
    刷新中.value = true
  } else {
    首次加载中.value = true
  }
  try {
    const data = await fetchExplorer(folderId)
    应用资源数据(data)
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '加载资源失败'))
  } finally {
    if (静默) {
      刷新中.value = false
    } else {
      首次加载中.value = false
    }
  }
}

function 重置全局搜索结果() {
  全局搜索中.value = false
  全局搜索结果.value = { folders: [], files: [] }
}

async function 执行全局搜索(keyword: string, requestId: number) {
  try {
    const data = await requestSearchFiles(keyword)
    if (requestId !== 全局搜索序号) {
      return
    }
    全局搜索结果.value = data
  } catch (error) {
    if (requestId !== 全局搜索序号) {
      return
    }
    重置全局搜索结果()
    ElMessage.error(getApiErrorMessage(error, '跨目录搜索失败'))
    return
  }

  if (requestId === 全局搜索序号) {
    全局搜索中.value = false
  }
}

async function 刷新当前视图(folderId: string | null = 当前目录ID.value) {
  await 拉取资源(folderId, { 静默: true })
  if (!是否全局搜索模式.value) {
    return
  }

  const keyword = 搜索关键词.value.trim()
  if (!keyword) {
    重置全局搜索结果()
    return
  }

  全局搜索序号 += 1
  const requestId = 全局搜索序号
  全局搜索中.value = true
  await 执行全局搜索(keyword, requestId)
}

watch([搜索关键词, 搜索范围值], ([keyword, scope]) => {
  if (全局搜索定时器 !== null) {
    window.clearTimeout(全局搜索定时器)
    全局搜索定时器 = null
  }

  全局搜索序号 += 1
  const requestId = 全局搜索序号
  if (scope !== 'global') {
    重置全局搜索结果()
    return
  }

  const normalizedKeyword = keyword.trim()
  if (!normalizedKeyword) {
    重置全局搜索结果()
    return
  }

  全局搜索中.value = true
  全局搜索定时器 = window.setTimeout(() => {
    全局搜索定时器 = null
    void 执行全局搜索(normalizedKeyword, requestId)
  }, 280)
})

watch([当前目录ID, 当前资源视图, 搜索范围值, 搜索关键词], () => {
  const draft = 右侧新建文件夹草稿状态.value
  if (!draft) {
    return
  }
  if (!当前可在右侧新建文件夹.value || draft.parentId !== 当前目录ID.value) {
    取消右侧新建文件夹()
  }
})

function 处理树节点点击(data: 目录树节点) {
  if (data.isDraft || 重命名目录草稿状态.value?.id === data.id) {
    return
  }
  if (data.isArticleImages) {
    void 打开文章图片视图()
    return
  }
  void 进入文件夹(data.isRoot ? null : data.id)
}

function 显示目录树文件夹右键菜单(data: 目录树节点, event: globalThis.MouseEvent) {
  if (data.isRoot || data.isArticleImages || data.isDraft || 重命名目录草稿状态.value?.id === data.id) {
    return
  }
  显示文件夹右键菜单(从目录树节点构建文件夹(data), event, 'tree')
}

async function 打开文件夹(folderId: string | null) {
  关闭右键菜单()
  当前资源视图.value = 'files'
  await 拉取资源(folderId, { 静默: 资源数据.value !== null })
}

async function 进入文件夹(folderId: string | null) {
  搜索范围值.value = 'current'
  await 打开文件夹(folderId)
}

async function 打开文章图片视图() {
  关闭右键菜单()
  搜索范围值.value = 'current'
  if (当前目录ID.value !== null || 当前资源视图.value !== 'article-images') {
    await 拉取资源(null, { 静默: 资源数据.value !== null })
  }
  当前资源视图.value = 'article-images'
}

function 处理导航栏点击(item: FileBreadcrumbItem) {
  if (item.id === 文章图片节点键) {
    void 打开文章图片视图()
    return
  }
  void 进入文件夹(item.id)
}

function 是否消息框取消(error: unknown) {
  if (error === 'cancel' || error === 'close') {
    return true
  }
  if (typeof error !== 'object' || error === null || !('action' in error)) {
    return false
  }
  const action = (error as { action?: unknown }).action
  return action === 'cancel' || action === 'close'
}

function 构建文件夹键(parentId: string | null, name: string) {
  return `${parentId ?? '__root__'}::${name.trim().toLowerCase()}`
}

function 插入新建目录节点(source: FileTreeNode[], draft: 新建目录草稿 | null): 目录树节点[] {
  if (!draft) {
    return source as 目录树节点[]
  }

  const draftNode: 目录树节点 = {
    id: draft.id,
    parent_id: draft.parentId,
    name: draft.name,
    isDraft: true,
    children: [],
  }

  if (draft.parentId === null) {
    return [...source, draftNode]
  }

  let inserted = false

  const visit = (nodes: FileTreeNode[]): 目录树节点[] => {
    let changed = false
    const nextNodes = nodes.map((node) => {
      if (node.id === draft.parentId) {
        inserted = true
        changed = true
        return {
          ...node,
          children: [...node.children, draftNode],
        }
      }

      if (!node.children.length) {
        return node as 目录树节点
      }

      const nextChildren = visit(node.children)
      if (nextChildren !== node.children) {
        changed = true
        return {
          ...node,
          children: nextChildren,
        }
      }

      return node as 目录树节点
    })

    return changed ? nextNodes : (nodes as 目录树节点[])
  }

  const nextTree = visit(source)
  return inserted ? nextTree : (source as 目录树节点[])
}

function 写入文件夹索引(nodes: FileTreeNode[], lookup: Map<string, string>) {
  for (const node of nodes) {
    lookup.set(构建文件夹键(node.parent_id, node.name), node.id)
    写入文件夹索引(node.children, lookup)
  }
}

function 构建文件夹索引() {
  const lookup = new Map<string, string>()
  写入文件夹索引(资源数据.value?.tree ?? [], lookup)
  return lookup
}

async function 确保目录路径(relativeDirectory: string, lookup: Map<string, string>) {
  let parentId = 当前目录ID.value
  const segments = relativeDirectory.split('/').map((item) => item.trim()).filter(Boolean)

  for (const segment of segments) {
    const folderKey = 构建文件夹键(parentId, segment)
    let folderId = lookup.get(folderKey) ?? null
    if (!folderId) {
      const createdFolder = await requestCreateFolder(segment, parentId)
      folderId = createdFolder.id
      lookup.set(folderKey, folderId)
    }
    parentId = folderId
  }

  return parentId
}

async function 执行文件上传(files: globalThis.File[]) {
  if (files.length === 0) {
    return
  }

  关闭右键菜单()
  正在上传.value = true
  try {
    const results = await Promise.allSettled(files.map((file) => requestUploadFile(file, 当前目录ID.value)))
    const successCount = results.filter((result) => result.status === 'fulfilled').length
    const failResults = results.filter((result) => result.status === 'rejected')

    if (successCount > 0) {
      ElMessage.success(`已上传 ${successCount} 个文件`)
    }
    if (failResults.length > 0) {
      const firstError = failResults[0]
      if (firstError.status === 'rejected') {
        ElMessage.error(getApiErrorMessage(firstError.reason, `有 ${failResults.length} 个文件上传失败`))
      }
    }

    await 刷新当前视图()
  } finally {
    正在上传.value = false
  }
}

async function 执行目录上传(files: 带目录路径文件[]) {
  if (files.length === 0) {
    return
  }

  关闭右键菜单()
  正在上传.value = true
  try {
    const folderLookup = 构建文件夹索引()
    let successCount = 0
    const failReasons: unknown[] = []

    for (const file of files) {
      try {
        const relativePath = (file.webkitRelativePath || file.name).replace(/\\/g, '/')
        const segments = relativePath.split('/').filter(Boolean)
        const directoryPath = segments.slice(0, -1).join('/')
        const folderId = await 确保目录路径(directoryPath, folderLookup)
        await requestUploadFile(file, folderId)
        successCount += 1
      } catch (error) {
        failReasons.push(error)
      }
    }

    if (successCount > 0) {
      ElMessage.success(`目录上传完成，共处理 ${successCount} 个文件`)
    }
    if (failReasons.length > 0) {
      ElMessage.error(getApiErrorMessage(failReasons[0], `有 ${failReasons.length} 个文件上传失败`))
    }

    await 刷新当前视图()
  } finally {
    正在上传.value = false
  }
}

function 触发文件上传() {
  关闭右键菜单()
  文件上传输入框.value?.click()
}

function 触发目录上传() {
  关闭右键菜单()
  目录上传输入框.value?.click()
}

async function 处理文件选择(event: globalThis.Event) {
  const input = event.target as globalThis.HTMLInputElement | null
  const files = Array.from(input?.files ?? [])
  if (input) {
    input.value = ''
  }
  await 执行文件上传(files)
}

async function 处理目录选择(event: globalThis.Event) {
  const input = event.target as globalThis.HTMLInputElement | null
  const files = Array.from(input?.files ?? []) as 带目录路径文件[]
  if (input) {
    input.value = ''
  }
  await 执行目录上传(files)
}

async function 新建文件夹() {
  关闭右键菜单()
  if (await 聚焦现有编辑输入框()) {
    return
  }

  const parentId = 当前是文章图片视图.value ? null : 当前目录ID.value
  新建目录草稿状态.value = {
    id: 新建目录临时节点键,
    parentId,
    name: '',
  }

  if (parentId) {
    await nextTick()
    目录树引用.value?.getNode(parentId)?.expand()
  }

  await 聚焦新建目录输入框()
}

async function 聚焦现有编辑输入框() {
  const rightDraft = 右侧新建文件夹草稿状态.value
  if (rightDraft) {
    if (当前可在右侧新建文件夹.value && rightDraft.parentId === 当前目录ID.value) {
      await 聚焦右侧新建文件夹输入框()
      return true
    }
    取消右侧新建文件夹()
  }

  if (新建目录草稿状态.value) {
    await 聚焦新建目录输入框()
    return true
  }

  if (重命名目录草稿状态.value) {
    await 聚焦重命名目录输入框()
    return true
  }

  const listDraft = 列表重命名草稿状态.value
  if (listDraft) {
    const isVisible = 当前展示资源列表.value.some((resource) => (
      resource.id === listDraft.id && resource.type === listDraft.type
    ))
    if (isVisible) {
      await 聚焦列表重命名输入框()
      return true
    }
    取消列表重命名()
  }

  return false
}

async function 聚焦新建目录输入框() {
  await nextTick()
  window.requestAnimationFrame(() => {
    新建目录输入框.value?.focus()
    新建目录输入框.value?.select()
  })
}

function 取消新建文件夹() {
  新建目录草稿状态.value = null
  正在提交新建目录.value = false
}

async function 在右侧新建文件夹() {
  关闭右键菜单()
  if (!当前可在右侧新建文件夹.value) {
    await 新建文件夹()
    return
  }
  if (await 聚焦现有编辑输入框()) {
    return
  }

  右侧新建文件夹草稿状态.value = {
    id: 右侧新建文件夹临时资源键,
    parentId: 当前目录ID.value,
    name: '',
  }

  await 聚焦右侧新建文件夹输入框()
}

async function 聚焦右侧新建文件夹输入框() {
  await nextTick()
  window.requestAnimationFrame(() => {
    const input = 右侧新建文件夹输入框.value
      ?? document.querySelector<globalThis.HTMLInputElement>('.resource-row--editing .resource-row__input')
    input?.focus()
    input?.select()
  })
}

function 取消右侧新建文件夹() {
  右侧新建文件夹草稿状态.value = null
  正在提交右侧新建文件夹.value = false
}

async function 聚焦重命名目录输入框() {
  await nextTick()
  window.requestAnimationFrame(() => {
    重命名目录输入框.value?.focus()
    重命名目录输入框.value?.select()
  })
}

function 取消重命名目录() {
  重命名目录草稿状态.value = null
  正在提交重命名目录.value = false
}

async function 聚焦列表重命名输入框() {
  await nextTick()
  window.requestAnimationFrame(() => {
    const input = 列表重命名输入框.value
      ?? document.querySelector<globalThis.HTMLInputElement>('.resource-row--editing .resource-row__input')
    input?.focus()
    input?.select()
  })
}

function 提取输入框元素(
  element: globalThis.Element | ComponentPublicInstance | null,
): globalThis.HTMLInputElement | null {
  return element instanceof globalThis.HTMLInputElement ? element : null
}

function 设置右侧新建文件夹输入框引用(element: globalThis.Element | ComponentPublicInstance | null) {
  右侧新建文件夹输入框.value = 提取输入框元素(element)
}

function 设置列表重命名输入框引用(element: globalThis.Element | ComponentPublicInstance | null) {
  列表重命名输入框.value = 提取输入框元素(element)
}

function 取消列表重命名() {
  列表重命名草稿状态.value = null
  正在提交列表重命名.value = false
}

async function 保存右侧新建文件夹() {
  const draft = 右侧新建文件夹草稿状态.value
  if (!draft || 正在提交右侧新建文件夹.value) {
    return
  }

  const name = draft.name.trim()
  if (!name) {
    取消右侧新建文件夹()
    return
  }

  正在提交右侧新建文件夹.value = true
  try {
    await requestCreateFolder(name, draft.parentId)
    右侧新建文件夹草稿状态.value = null
    ElMessage.success('文件夹已创建')
    await 刷新当前视图()
  } catch (error) {
    正在提交右侧新建文件夹.value = false
    ElMessage.error(getApiErrorMessage(error, '创建文件夹失败'))
    await 聚焦右侧新建文件夹输入框()
    return
  }

  正在提交右侧新建文件夹.value = false
}

async function 保存新建文件夹() {
  const draft = 新建目录草稿状态.value
  if (!draft || 正在提交新建目录.value) {
    return
  }

  const name = draft.name.trim()
  if (!name) {
    取消新建文件夹()
    return
  }

  正在提交新建目录.value = true
  try {
    await requestCreateFolder(name, draft.parentId)
    新建目录草稿状态.value = null
    ElMessage.success('文件夹已创建')
    await 刷新当前视图()
  } catch (error) {
    正在提交新建目录.value = false
    ElMessage.error(getApiErrorMessage(error, '创建文件夹失败'))
    await 聚焦新建目录输入框()
    return
  }

  正在提交新建目录.value = false
}

async function 处理新建目录输入框失焦() {
  if (正在提交新建目录.value) {
    return
  }
  await 保存新建文件夹()
}

async function 处理右侧新建文件夹输入框失焦() {
  if (正在提交右侧新建文件夹.value) {
    return
  }
  await 保存右侧新建文件夹()
}

function 处理新建目录键盘事件(event: globalThis.KeyboardEvent) {
  if (event.isComposing) {
    return
  }
  if (event.key === 'Enter') {
    event.preventDefault()
    event.stopPropagation()
    void 保存新建文件夹()
    return
  }
  if (event.key === 'Escape') {
    event.preventDefault()
    event.stopPropagation()
    取消新建文件夹()
  }
}

function 处理右侧新建文件夹键盘事件(event: globalThis.KeyboardEvent) {
  if (event.isComposing) {
    return
  }
  if (event.key === 'Enter') {
    event.preventDefault()
    event.stopPropagation()
    void 保存右侧新建文件夹()
    return
  }
  if (event.key === 'Escape') {
    event.preventDefault()
    event.stopPropagation()
    取消右侧新建文件夹()
  }
}

async function 重命名文件夹(folder: 文件夹展示项) {
  const menuSource = 右键菜单.value.source
  关闭右键菜单()
  if (await 聚焦现有编辑输入框()) {
    return
  }
  if (menuSource === 'tree') {
    重命名目录草稿状态.value = {
      id: folder.id,
      name: folder.name,
      originalName: folder.name,
    }
    await 聚焦重命名目录输入框()
    return
  }
  列表重命名草稿状态.value = {
    type: 'folder',
    id: folder.id,
    name: folder.name,
    originalName: folder.name,
  }
  await 聚焦列表重命名输入框()
}

async function 保存重命名目录() {
  const draft = 重命名目录草稿状态.value
  if (!draft || 正在提交重命名目录.value) {
    return
  }

  const name = draft.name.trim()
  if (!name || name === draft.originalName.trim()) {
    取消重命名目录()
    return
  }

  正在提交重命名目录.value = true
  try {
    await requestRenameFolder(draft.id, name)
    重命名目录草稿状态.value = null
    ElMessage.success('文件夹已重命名')
    await 刷新当前视图()
  } catch (error) {
    正在提交重命名目录.value = false
    ElMessage.error(getApiErrorMessage(error, '重命名文件夹失败'))
    await 聚焦重命名目录输入框()
    return
  }

  正在提交重命名目录.value = false
}

async function 处理重命名目录输入框失焦() {
  if (正在提交重命名目录.value) {
    return
  }
  await 保存重命名目录()
}

function 处理重命名目录键盘事件(event: globalThis.KeyboardEvent) {
  if (event.isComposing) {
    return
  }
  if (event.key === 'Enter') {
    event.preventDefault()
    event.stopPropagation()
    void 保存重命名目录()
    return
  }
  if (event.key === 'Escape') {
    event.preventDefault()
    event.stopPropagation()
    取消重命名目录()
  }
}

function 是否资源正在右侧重命名(resource: 资源展示项) {
  return 列表重命名草稿状态.value?.id === resource.id && 列表重命名草稿状态.value?.type === resource.type
}

function 是否资源是右侧新建文件夹草稿(resource: 资源展示项) {
  return resource.type === 'folder' && 右侧新建文件夹草稿状态.value?.id === resource.id
}

function 是否资源处于右侧编辑态(resource: 资源展示项) {
  return 是否资源是右侧新建文件夹草稿(resource) || 是否资源正在右侧重命名(resource)
}

async function 保存右侧重命名() {
  const draft = 列表重命名草稿状态.value
  if (!draft || 正在提交列表重命名.value) {
    return
  }

  const name = draft.name.trim()
  if (!name || name === draft.originalName.trim()) {
    取消列表重命名()
    return
  }

  正在提交列表重命名.value = true
  try {
    if (draft.type === 'folder') {
      await requestRenameFolder(draft.id, name)
      ElMessage.success('文件夹已重命名')
    } else {
      await requestRenameFile(draft.id, name)
      ElMessage.success('文件已重命名')
    }
    列表重命名草稿状态.value = null
    await 刷新当前视图()
  } catch (error) {
    正在提交列表重命名.value = false
    ElMessage.error(getApiErrorMessage(error, draft.type === 'folder' ? '重命名文件夹失败' : '重命名文件失败'))
    await 聚焦列表重命名输入框()
    return
  }

  正在提交列表重命名.value = false
}

async function 处理右侧重命名输入框失焦() {
  if (正在提交列表重命名.value) {
    return
  }
  await 保存右侧重命名()
}

function 处理右侧重命名键盘事件(event: globalThis.KeyboardEvent) {
  if (event.isComposing) {
    return
  }
  if (event.key === 'Enter') {
    event.preventDefault()
    event.stopPropagation()
    void 保存右侧重命名()
    return
  }
  if (event.key === 'Escape') {
    event.preventDefault()
    event.stopPropagation()
    取消列表重命名()
  }
}

async function 重命名文件(file: 文件展示项) {
  关闭右键菜单()
  if (await 聚焦现有编辑输入框()) {
    return
  }
  列表重命名草稿状态.value = {
    type: 'file',
    id: file.id,
    name: file.original_name,
    originalName: file.original_name,
  }
  await 聚焦列表重命名输入框()
}

async function 删除文件夹(folder: 文件夹展示项) {
  关闭右键菜单()
  try {
    await requestDeleteFolder(folder.id)
    ElMessage.success('文件夹已删除')
    if (当前目录.value?.id === folder.id) {
      await 进入文件夹(folder.parent_id)
      return
    }
    await 刷新当前视图()
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '删除文件夹失败'))
  }
}

async function 确认删除文件夹(folder: 文件夹展示项) {
  关闭右键菜单()
  try {
    await ElMessageBox.confirm(
      '确定删除此文件夹？仅空文件夹可删除。',
      '删除文件夹',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
      },
    )
  } catch (error) {
    if (是否消息框取消(error)) {
      return
    }
    ElMessage.error(getApiErrorMessage(error, '删除文件夹失败'))
    return
  }
  await 删除文件夹(folder)
}

function 是否选中文件夹(id: string) {
  return 已选文件夹.value.has(id)
}

function 是否选中文件(id: string) {
  return 已选文件.value.has(id)
}

function 设置文件夹选中(id: string, selected: boolean) {
  const next = new Set(已选文件夹.value)
  if (selected) {
    next.add(id)
  } else {
    next.delete(id)
  }
  已选文件夹.value = next
}

function 设置文件选中(id: string, selected: boolean) {
  const next = new Set(已选文件.value)
  if (selected) {
    next.add(id)
  } else {
    next.delete(id)
  }
  已选文件.value = next
}

function 切换当前页全选() {
  if (是否已全选当前页.value) {
    const nextFolders = new Set(已选文件夹.value)
    const nextFiles = new Set(已选文件.value)
    for (const folder of 当前展示文件夹列表.value) {
      nextFolders.delete(folder.id)
    }
    for (const file of 当前展示文件列表.value) {
      nextFiles.delete(file.id)
    }
    已选文件夹.value = nextFolders
    已选文件.value = nextFiles
    return
  }
  const nextFolders = new Set(已选文件夹.value)
  const nextFiles = new Set(已选文件.value)
  for (const folder of 当前展示文件夹列表.value) {
    nextFolders.add(folder.id)
  }
  for (const file of 当前展示文件列表.value) {
    nextFiles.add(file.id)
  }
  已选文件夹.value = nextFolders
  已选文件.value = nextFiles
}

function 读取当前已选资源() {
  const selectedFolders = [...已选文件夹.value].map((id) => ({ type: 'folder', id } as const))
  const selectedFiles = [...已选文件.value].map((id) => ({ type: 'file', id } as const))
  return [...selectedFolders, ...selectedFiles]
}

function 获取操作资源列表(resource?: 资源标识) {
  const targetResources = resource ? [resource] : 读取当前已选资源()
  if (targetResources.length === 0) {
    ElMessage.warning('请先选择资源')
    return null
  }
  return targetResources
}

async function 批量删除资源(resource?: 资源标识) {
  const targetResources = 获取操作资源列表(resource)
  if (!targetResources) {
    return
  }

  关闭右键菜单()
  try {
    await ElMessageBox.confirm(
      `确定删除选中的 ${targetResources.length} 项资源？`,
      '删除资源',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
      },
    )
  } catch (error) {
    if (是否消息框取消(error)) {
      return
    }
    ElMessage.error(getApiErrorMessage(error, '删除资源失败'))
    return
  }

  const files = targetResources.filter((item) => item.type === 'file')
  const folders = targetResources.filter((item) => item.type === 'folder')
  const 当前目录父级ID = 当前目录.value?.parent_id ?? null
  const 当前目录删除结果索引 = 当前目录.value ? folders.findIndex((item) => item.id === 当前目录.value?.id) : -1
  const 文件删除结果 = await Promise.allSettled(files.map((item) => requestDeleteFile(item.id)))
  const 文件夹删除结果 = await Promise.allSettled(folders.map((item) => requestDeleteFolder(item.id)))
  const results = [
    ...文件删除结果,
    ...文件夹删除结果,
  ]
  const failResults = results.filter((result) => result.status === 'rejected')
  const successCount = results.length - failResults.length
  const 当前目录已删除 = 当前目录删除结果索引 >= 0 && 文件夹删除结果[当前目录删除结果索引]?.status === 'fulfilled'

  if (successCount > 0) {
    ElMessage.success(`已删除 ${successCount} 项资源`)
  }
  if (failResults.length > 0) {
    const firstError = failResults[0]
    if (firstError.status === 'rejected') {
      ElMessage.error(getApiErrorMessage(firstError.reason, `有 ${failResults.length} 项资源删除失败`))
    }
  }

  if (当前目录已删除) {
    await 进入文件夹(当前目录父级ID)
    return
  }
  await 刷新当前视图()
}

function 打开移动对话框(resource?: 资源标识) {
  const targetResources = 获取操作资源列表(resource)
  if (!targetResources) {
    return
  }
  const 不可移动资源数量 = 获取不可移动资源数量(targetResources)
  if (不可移动资源数量 > 0) {
    ElMessage.warning(`当前选中内容中有 ${不可移动资源数量} 项文章图片，暂不支持移动`)
    return
  }
  关闭右键菜单()
  待移动资源列表.value = targetResources
  移动目标目录ID.value = 当前目录ID.value
  移动对话框可见.value = true
}

function 打开批量重命名对话框() {
  const targetResources = 获取操作资源列表()
  if (!targetResources) {
    return
  }
  关闭右键菜单()
  批量重命名对话框可见.value = true
}

function 生成批量序号(offset: number) {
  return String(批量重命名起始序号.value + offset).padStart(批量重命名位数.value, '0')
}

function 构建批量文件名(resource: 资源标识, offset: number) {
  const serial = 生成批量序号(offset)
  if (resource.type === 'folder') {
    return `${批量重命名前缀.value}${serial}`
  }

  const file = 原始文件列表.value.find((item) => item.id === resource.id)
  const extension = file ? 提取扩展名(file.original_name) : ''
  if (!批量重命名保留扩展名.value || !extension) {
    return `${批量重命名前缀.value}${serial}`
  }
  return `${批量重命名前缀.value}${serial}.${extension}`
}

function 获取批量重命名资源列表() {
  const orderedFolders = 排序文件夹列表(
    原始子文件夹列表.value.filter((folder) => 已选文件夹.value.has(folder.id)),
  ).map((folder) => ({ type: 'folder', id: folder.id } as const))
  const orderedFiles = 排序文件列表(
    原始文件列表.value.filter((file) => 已选文件.value.has(file.id)),
  ).map((file) => ({ type: 'file', id: file.id } as const))
  return [...orderedFolders, ...orderedFiles]
}

async function 确认批量重命名() {
  const targetResources = 获取批量重命名资源列表()
  if (targetResources.length === 0) {
    ElMessage.warning('请先选择资源')
    批量重命名对话框可见.value = false
    return
  }

  const results = await Promise.allSettled(
    targetResources.map((resource, index) => {
      const nextName = 构建批量文件名(resource, index)
      if (resource.type === 'folder') {
        return requestRenameFolder(resource.id, nextName)
      }
      return requestRenameFile(resource.id, nextName)
    }),
  )
  const failResults = results.filter((result) => result.status === 'rejected')
  const successCount = results.length - failResults.length

  if (successCount > 0) {
    ElMessage.success(`已重命名 ${successCount} 项资源`)
  }
  if (failResults.length > 0) {
    const firstError = failResults[0]
    if (firstError.status === 'rejected') {
      ElMessage.error(getApiErrorMessage(firstError.reason, `有 ${failResults.length} 项资源重命名失败`))
    }
  }

  批量重命名对话框可见.value = false
  await 刷新当前视图()
}

async function 确认移动资源() {
  if (待移动资源列表.value.length === 0) {
    移动对话框可见.value = false
    return
  }
  const 不可移动资源数量 = 获取不可移动资源数量(待移动资源列表.value)
  if (不可移动资源数量 > 0) {
    ElMessage.warning(`当前选中内容中有 ${不可移动资源数量} 项文章图片，暂不支持移动`)
    移动对话框可见.value = false
    待移动资源列表.value = []
    return
  }

  const files = 待移动资源列表.value.filter((item) => item.type === 'file')
  const folders = 待移动资源列表.value.filter((item) => item.type === 'folder')
  const results = [
    ...(await Promise.allSettled(files.map((item) => requestMoveFile(item.id, 移动目标目录ID.value)))),
    ...(await Promise.allSettled(folders.map((item) => requestMoveFolder(item.id, 移动目标目录ID.value)))),
  ]
  const failResults = results.filter((result) => result.status === 'rejected')
  const successCount = results.length - failResults.length

  if (successCount > 0) {
    ElMessage.success(`已移动 ${successCount} 项资源`)
  }
  if (failResults.length > 0) {
    const firstError = failResults[0]
    if (firstError.status === 'rejected') {
      ElMessage.error(getApiErrorMessage(firstError.reason, `有 ${failResults.length} 项资源移动失败`))
    }
  }

  移动对话框可见.value = false
  待移动资源列表.value = []
  await 刷新当前视图()
}

function 从目录树节点构建文件夹(node: FileTreeNode): FileFolderItem {
  return {
    id: node.id,
    parent_id: node.parent_id,
    name: node.name,
    created_at: '',
    updated_at: '',
  }
}

function 查找文件夹展示项(id: string): 文件夹展示项 | null {
  if (当前目录.value?.id === id) {
    return 当前目录.value
  }
  const treeFolder = 资源数据.value?.tree
    .flatMap((node) => 收集目录树节点(node))
    .find((item) => item.id === id)
  return 当前展示文件夹列表.value.find((item) => item.id === id)
    ?? 原始子文件夹列表.value.find((item) => item.id === id)
    ?? (treeFolder ? 从目录树节点构建文件夹(treeFolder) : null)
    ?? null
}

function 查找文件展示项(id: string) {
  return 当前展示文件列表.value.find((item) => item.id === id)
    ?? 原始文件列表.value.find((item) => item.id === id)
    ?? null
}

function 收集目录树节点(node: FileTreeNode): FileTreeNode[] {
  return [node, ...node.children.flatMap((child) => 收集目录树节点(child))]
}

function 去掉末尾压缩包扩展名(name: string) {
  return name.replace(/\.zip$/i, '')
}

function 去掉最后一个扩展名(name: string) {
  const lastDotIndex = name.lastIndexOf('.')
  if (lastDotIndex <= 0) {
    return name
  }
  return name.slice(0, lastDotIndex)
}

function 构建压缩包名称(resourceList: 资源标识[]) {
  if (resourceList.length === 1) {
    const resource = resourceList[0]
    if (resource.type === 'folder') {
      const folder = 查找文件夹展示项(resource.id)
      return 去掉末尾压缩包扩展名(folder?.name?.trim() || '资源打包')
    }

    const file = 查找文件展示项(resource.id)
    return 去掉末尾压缩包扩展名(去掉最后一个扩展名(file?.original_name?.trim() || '资源打包'))
  }

  if (是否全局搜索模式.value) {
    return `搜索结果-${resourceList.length}项`
  }
  return 去掉末尾压缩包扩展名(当前目录名称.value || '资源打包')
}

function 触发浏览器下载(blob: globalThis.Blob, fileName: string) {
  const downloadUrl = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = downloadUrl
  link.download = fileName
  document.body.append(link)
  link.click()
  link.remove()
  window.setTimeout(() => {
    window.URL.revokeObjectURL(downloadUrl)
  }, 0)
}

function 获取单文件下载项(resourceList: 资源标识[]) {
  if (resourceList.length !== 1 || resourceList[0]?.type !== 'file') {
    return null
  }
  return 查找文件展示项(resourceList[0].id)
}

async function 直接下载文件(file: 文件展示项) {
  try {
    const blob = await requestDownloadFile(file.url)
    触发浏览器下载(blob, file.original_name)
    ElMessage.success('文件已开始下载')
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '文件下载失败'))
  }
}

async function 下载资源(resource?: 资源标识) {
  const targetResources = 获取操作资源列表(resource)
  if (!targetResources) {
    return
  }

  关闭右键菜单()
  const 单文件下载项 = 获取单文件下载项(targetResources)
  if (单文件下载项) {
    await 直接下载文件(单文件下载项)
    return
  }

  const folderIds = targetResources.filter((item) => item.type === 'folder').map((item) => item.id)
  const fileIds = targetResources.filter((item) => item.type === 'file').map((item) => item.id)
  const archiveName = 构建压缩包名称(targetResources)

  try {
    const blob = await requestDownloadArchive(folderIds, fileIds, archiveName)
    触发浏览器下载(blob, `${archiveName}.zip`)
    ElMessage.success('压缩包已开始下载')
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '打包下载失败'))
  }
}

function 打开媒体预览(file: 文件展示项) {
  关闭右键菜单()
  当前预览媒体ID.value = file.id
  媒体预览对话框可见.value = true
}

function 切换预览媒体(step: number) {
  const currentIndex = 当前预览媒体索引.value
  if (currentIndex < 0) {
    return
  }
  const nextIndex = currentIndex + step
  if (nextIndex < 0 || nextIndex >= 可预览媒体文件列表.value.length) {
    return
  }
  当前预览媒体ID.value = 可预览媒体文件列表.value[nextIndex]?.id ?? null
}

function 开始拖拽文件夹(folder: 文件夹展示项, event: globalThis.DragEvent) {
  写入拖拽资源(event, {
    type: 'folder',
    id: folder.id,
  })
}

function 是否可拖拽目录树节点(node: 目录树节点) {
  return !node.isRoot && !node.isArticleImages && !node.isDraft && 重命名目录草稿状态.value?.id !== node.id
}

function 开始拖拽目录树文件夹(node: 目录树节点, event: globalThis.DragEvent) {
  if (!是否可拖拽目录树节点(node)) {
    return
  }
  写入拖拽资源(event, {
    type: 'folder',
    id: node.id,
  })
}

function 开始拖拽文件(file: 文件展示项, event: globalThis.DragEvent) {
  if (!是否可移动文件(file)) {
    return
  }
  写入拖拽资源(event, {
    type: 'file',
    id: file.id,
  })
}

function 写入拖拽资源(event: globalThis.DragEvent, resource: 资源标识) {
  当前拖拽资源.value = resource
  event.dataTransfer?.setData(拖拽数据类型, JSON.stringify(resource))
  event.dataTransfer?.setData('text/plain', JSON.stringify(resource))
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move'
  }
}

function 结束拖拽资源() {
  当前拖拽资源.value = null
}

function 读取拖拽资源(event: globalThis.DragEvent) {
  const payload = event.dataTransfer?.getData(拖拽数据类型) || event.dataTransfer?.getData('text/plain')
  if (!payload) {
    return 当前拖拽资源.value
  }
  try {
    return JSON.parse(payload) as 资源标识
  } catch {
    return 当前拖拽资源.value
  }
}

async function 处理拖放到目录(targetFolderId: string | null, event: globalThis.DragEvent) {
  event.preventDefault()
  event.stopPropagation()

  const resource = 读取拖拽资源(event)
  当前拖拽资源.value = null
  if (!resource) {
    return
  }

  if ((resource.type !== 'file' && resource.type !== 'folder') || typeof resource.id !== 'string' || !resource.id) {
    ElMessage.warning('拖拽数据无效，请重试')
    return
  }

  try {
    if (resource.type === 'file') {
      const file = 查找文件展示项(resource.id)
      if (file && !是否可移动文件(file)) {
        ElMessage.warning('文章图片暂不支持移动')
        return
      }
      await requestMoveFile(resource.id, targetFolderId)
    } else {
      if (resource.id === targetFolderId) {
        return
      }
      await requestMoveFolder(resource.id, targetFolderId)
    }
    ElMessage.success('已移动')
    await 刷新当前视图()
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '移动失败'))
  }
}

function 解析链接(url: string) {
  return resolveManagedFileUrl(url)
}

function 获取可预览文件链接(url: string) {
  return resolveManagedFileUrl(url)
}

function 获取图片缩略图链接(file: 文件展示项) {
  return resolveManagedFileUrl(file.thumbnail_url || file.url)
}

function 打开文件(url: string) {
  关闭右键菜单()
  window.open(解析链接(url), '_blank', 'noopener,noreferrer')
}

function 获取原始文件路径(url: string) {
  return extractManagedFilePath(url) || url
}

function 打开文章编辑器(articleId: string) {
  关闭右键菜单()
  void 路由.push(`/dashboard/articles/edit/${articleId}`)
}

async function 复制文章图片链接(url: string) {
  关闭右键菜单()
  try {
    await navigator.clipboard.writeText(获取原始文件路径(url))
    ElMessage.success('文章图片链接已复制')
  } catch {
    ElMessage.error('复制失败，请检查浏览器权限')
  }
}

function 格式化大小(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1048576).toFixed(1)} MB`
}

function 格式化时间(value: string) {
  return new Date(value).toLocaleString()
}

function 提取扩展名(filename: string) {
  return filename.split('.').pop()?.trim().toLowerCase() || ''
}

function 是否文章图片(file: 文件展示项) {
  return file.purpose === 'article_image'
}

function 是否普通文件(file: 文件展示项) {
  return file.purpose === 'file'
}

function 是否资源支持移动(resource: 资源标识) {
  if (resource.type === 'folder') {
    return true
  }
  const file = 查找文件展示项(resource.id)
  return file ? 是否普通文件(file) : true
}

function 获取不可移动资源数量(resources: 资源标识[]) {
  return resources.filter((resource) => !是否资源支持移动(resource)).length
}

function 是否可移动文件(file: 文件展示项) {
  return 是否普通文件(file)
}

function 是否图片(file: 文件展示项) {
  return file.mime_type.startsWith('image/')
}

function 是否视频(file: 文件展示项) {
  return file.mime_type.startsWith('video/')
}

function 是否可预览媒体(file: 文件展示项) {
  return 是否图片(file) || 是否视频(file)
}

function 获取文件用途标签(file: 文件展示项) {
  return 是否文章图片(file) ? 文章图片标签 : ''
}

function 获取文件附加说明(file: 文件展示项) {
  if (是否文章图片(file) && file.article_title) {
    return `所属文章：${file.article_title}`
  }
  return ''
}

function 获取文件标签(file: 文件展示项) {
  const extension = 提取扩展名(file.original_name)
  if (extension) {
    return extension.toUpperCase()
  }
  if (file.mime_type.startsWith('image/')) {
    return 'IMG'
  }
  return 'FILE'
}

function 获取文件图标(file: 文件展示项) {
  return 是否图片(file) ? Picture : Document
}

function 是否文件夹资源(resource: 资源展示项): resource is Extract<资源展示项, { type: 'folder' }> {
  return resource.type === 'folder'
}

function 是否文件资源(resource: 资源展示项): resource is Extract<资源展示项, { type: 'file' }> {
  return resource.type === 'file'
}

function 是否资源已选中(resource: 资源展示项) {
  return resource.type === 'folder' ? 是否选中文件夹(resource.id) : 是否选中文件(resource.id)
}

function 设置资源选中(resource: 资源展示项, selected: boolean) {
  if (resource.type === 'folder') {
    设置文件夹选中(resource.id, selected)
    return
  }
  设置文件选中(resource.id, selected)
}

function 获取资源附加说明(resource: 资源展示项) {
  if (resource.type === 'folder') {
    return ''
  }
  return 获取文件附加说明(resource.item)
}

function 获取资源路径(resource: 资源展示项) {
  if (!是否全局搜索模式.value) {
    return ''
  }
  return 'path' in resource.item ? resource.item.path : ''
}

function 获取资源主标签(resource: 资源展示项) {
  if (resource.type === 'folder') {
    return '文件夹'
  }
  return 获取文件标签(resource.item)
}

function 获取资源用途标签(resource: 资源展示项) {
  if (resource.type === 'folder') {
    return ''
  }
  return 获取文件用途标签(resource.item)
}

function 是否可拖拽资源(resource: 资源展示项) {
  if (是否全局搜索模式.value) {
    return false
  }
  if (resource.type === 'folder') {
    return true
  }
  return 是否可移动文件(resource.item)
}

function 开始拖拽资源(resource: 资源展示项, event: globalThis.DragEvent) {
  if (resource.type === 'folder') {
    开始拖拽文件夹(resource.item, event)
    return
  }
  开始拖拽文件(resource.item, event)
}

function 处理资源行右键菜单(resource: 资源展示项, event: globalThis.MouseEvent) {
  if (是否资源处于右侧编辑态(resource)) {
    event.preventDefault()
    event.stopPropagation()
    return
  }
  if (resource.type === 'folder') {
    显示文件夹右键菜单(resource.item, event)
    return
  }
  显示文件右键菜单(resource.item, event)
}

function 显示文件右键菜单(file: 文件展示项, event: globalThis.MouseEvent) {
  event.preventDefault()
  event.stopPropagation()
  右键菜单.value = {
    visible: true,
    x: event.clientX,
    y: event.clientY,
    scope: 'file',
    source: 'list',
    resource: { type: 'file', id: file.id },
  }
}

function 显示文件夹右键菜单(folder: 文件夹展示项, event: globalThis.MouseEvent, source: 'tree' | 'list' = 'list') {
  event.preventDefault()
  event.stopPropagation()
  右键菜单.value = {
    visible: true,
    x: event.clientX,
    y: event.clientY,
    scope: 'folder',
    source,
    resource: { type: 'folder', id: folder.id },
  }
}

function 显示空白右键菜单(event: globalThis.MouseEvent) {
  if (event.defaultPrevented) {
    return
  }
  event.preventDefault()
  右键菜单.value = {
    visible: true,
    x: event.clientX,
    y: event.clientY,
    scope: 'blank',
    source: 'blank',
    resource: null,
  }
}

function 关闭右键菜单() {
  if (!右键菜单.value.visible) {
    return
  }
  右键菜单.value = {
    visible: false,
    x: 0,
    y: 0,
    scope: 'blank',
    source: 'blank',
    resource: null,
  }
}
</script>

<template>
  <div class="page-container">
    <input
      ref="文件上传输入框"
      type="file"
      multiple
      class="hidden-input"
      @change="处理文件选择"
    >
    <input
      ref="目录上传输入框"
      type="file"
      multiple
      webkitdirectory
      directory
      class="hidden-input"
      @change="处理目录选择"
    >

    <div class="page-header">
      <div class="page-heading">
        <h2 class="page-title">
          <ElIcon><FolderOpened /></ElIcon>
          <span>资源管理器</span>
        </h2>
      </div>
      <div class="page-actions">
        <ElButton :loading="正在上传" @click="触发目录上传">
          <Icon icon="codicon:folder-opened" class="page-action-icon" aria-hidden="true" />
          <span>上传目录</span>
        </ElButton>
        <ElButton type="primary" :loading="正在上传" @click="触发文件上传">
          <Icon icon="codicon:cloud-upload" class="page-action-icon" aria-hidden="true" />
          <span>上传文件</span>
        </ElButton>
      </div>
    </div>

    <div class="filter-toolbar page-filter-toolbar">
      <ElInput
        v-model="搜索关键词"
        clearable
        :placeholder="搜索框占位文案"
        class="filter-toolbar__search"
      >
        <template #prefix>
          <ElIcon><Search /></ElIcon>
        </template>
      </ElInput>
      <ElSelect v-model="搜索范围值" class="filter-toolbar__scope">
        <ElOption
          v-for="option in 搜索范围选项"
          :key="option.value"
          :label="option.label"
          :value="option.value"
        />
      </ElSelect>
      <ElSelect v-model="当前排序" class="filter-toolbar__sort" :disabled="是否全局搜索模式">
        <ElOption
          v-for="option in 排序选项"
          :key="option.value"
          :label="option.label"
          :value="option.value"
        />
      </ElSelect>
    </div>

    <div class="page-body">
      <ElSkeleton :loading="是否显示骨架屏" animated class="page-skeleton">
        <ElCard shadow="never" class="explorer-shell">
          <div
            ref="浏览器布局容器"
            class="explorer-layout"
            :style="浏览器布局样式"
          >
            <aside class="explorer-sidebar">
              <div class="sidebar-card__header">
                <h3 class="sidebar-card__title">目录树</h3>
                <div class="sidebar-card__actions">
                  <button
                    type="button"
                    class="sidebar-action-button"
                    :disabled="正在上传"
                    title="新建文件夹"
                    aria-label="新建文件夹"
                    @click="新建文件夹"
                  >
                    <Icon icon="codicon:new-folder" class="sidebar-action-button__icon" aria-hidden="true" />
                  </button>
                </div>
              </div>

              <div class="explorer-tree">
                <ElTree
                  ref="目录树引用"
                  :data="目录树数据"
                  node-key="id"
                  default-expand-all
                  highlight-current
                  :current-node-key="选中目录树节点键"
                  :expand-on-click-node="false"
                  empty-text="暂无文件夹"
                  @node-click="处理树节点点击"
                >
                  <template #default="{ data, node }">
                    <div
                      class="tree-node"
                      :class="{
                        'tree-node--draft': data.isDraft,
                        'tree-node--editing': 重命名目录草稿状态?.id === data.id,
                      }"
                      :draggable="是否可拖拽目录树节点(data)"
                      @contextmenu="显示目录树文件夹右键菜单(data, $event)"
                      @dragstart="开始拖拽目录树文件夹(data, $event)"
                      @dragend="结束拖拽资源"
                      @dragover.prevent
                      @drop="data.isArticleImages || data.isDraft || 重命名目录草稿状态?.id === data.id ? null : 处理拖放到目录(data.isRoot ? null : data.id, $event)"
                    >
                      <ElIcon class="tree-node__icon">
                        <component
                          :is="data.isArticleImages
                            ? Picture
                            : (((data.isRoot && 当前目录ID === null) || data.id === 当前目录ID || (node.expanded && !node.isLeaf))
                              ? FolderOpened
                              : Folder)"
                        />
                      </ElIcon>
                      <input
                        v-if="data.isDraft"
                        ref="新建目录输入框"
                        v-model="新建目录名称"
                        class="tree-node__input"
                        :disabled="正在提交新建目录"
                        placeholder="新建文件夹"
                        @click.stop
                        @mousedown.stop
                        @keydown="处理新建目录键盘事件"
                        @blur="处理新建目录输入框失焦"
                      >
                      <input
                        v-else-if="重命名目录草稿状态?.id === data.id"
                        ref="重命名目录输入框"
                        v-model="重命名目录名称"
                        class="tree-node__input"
                        :disabled="正在提交重命名目录"
                        @click.stop
                        @mousedown.stop
                        @keydown="处理重命名目录键盘事件"
                        @blur="处理重命名目录输入框失焦"
                      >
                      <span v-else class="tree-node__label">{{ data.name }}</span>
                    </div>
                  </template>
                </ElTree>
              </div>
            </aside>

            <button
              type="button"
              class="explorer-resizer"
              :class="{ 'is-dragging': 正在拖动分隔线 }"
              aria-label="拖动调整目录树宽度"
              @pointerdown="开始拖动分隔线"
            >
              <span class="explorer-resizer__handle" />
            </button>

            <section class="explorer-main" @contextmenu="显示空白右键菜单">
              <div class="explorer-toolbar">
                <div class="breadcrumb-trail">
                  <ElBreadcrumb separator="/">
                    <ElBreadcrumbItem v-for="item in 导航栏列表" :key="item.id ?? 'root'">
                      <button
                        type="button"
                        class="breadcrumb-button"
                        @click="处理导航栏点击(item)"
                        @dragover.prevent
                        @drop="item.id === 文章图片节点键 ? null : 处理拖放到目录(item.id, $event)"
                      >
                        {{ item.name }}
                      </button>
                    </ElBreadcrumbItem>
                  </ElBreadcrumb>
                </div>
              </div>

              <div
                class="explorer-content"
                :class="{ 'explorer-content--with-selection': 已选资源总数 > 0 }"
              >
                <div v-if="当前页资源总数 === 0" class="empty-state empty-state--inner">
                  <ElEmpty :description="当前空状态描述" />
                </div>

                <template v-else>
                  <section class="resource-section">
                    <div class="resource-list">
                      <div
                        v-for="resource in 当前展示资源列表"
                        :key="`${resource.type}-${resource.id}`"
                        class="resource-row"
                        :class="{
                          'is-selected': 是否资源已选中(resource),
                          'resource-row--folder': 是否文件夹资源(resource),
                          'resource-row--editing': 是否资源处于右侧编辑态(resource),
                        }"
                        :draggable="是否可拖拽资源(resource) && !是否资源处于右侧编辑态(resource)"
                        @click="!是否资源处于右侧编辑态(resource) && 是否文件夹资源(resource) ? void 进入文件夹(resource.item.id) : null"
                        @contextmenu="处理资源行右键菜单(resource, $event)"
                        @dragstart="开始拖拽资源(resource, $event)"
                        @dragend="结束拖拽资源"
                        @dragover.prevent
                        @drop="是否文件夹资源(resource) && !是否全局搜索模式 && !是否资源处于右侧编辑态(resource) ? 处理拖放到目录(resource.item.id, $event) : null"
                      >
                        <div class="resource-selector" @click.stop>
                          <ElCheckbox
                            v-if="!是否资源是右侧新建文件夹草稿(resource)"
                            :model-value="是否资源已选中(resource)"
                            @change="(checked) => 设置资源选中(resource, Boolean(checked))"
                          />
                        </div>

                        <div v-if="是否文件夹资源(resource)" class="resource-row__icon resource-row__icon--folder">
                          <ElIcon><Folder /></ElIcon>
                        </div>
                        <div v-else-if="是否图片(resource.item)" class="resource-row__preview">
                          <img
                            :src="获取图片缩略图链接(resource.item)"
                            :alt="resource.item.original_name"
                            loading="lazy"
                            decoding="async"
                            @click.stop="打开媒体预览(resource.item)"
                          >
                        </div>
                        <button
                          v-else-if="是否视频(resource.item)"
                          type="button"
                          class="resource-row__preview resource-row__preview--video"
                          @click.stop="打开媒体预览(resource.item)"
                        >
                          <ElIcon><VideoPlay /></ElIcon>
                          <span class="resource-row__preview-badge">VIDEO</span>
                        </button>
                        <div v-else class="resource-row__icon">
                          <ElIcon><component :is="获取文件图标(resource.item)" /></ElIcon>
                        </div>

                        <div class="resource-row__body">
                          <input
                            v-if="是否资源是右侧新建文件夹草稿(resource)"
                            :ref="设置右侧新建文件夹输入框引用"
                            v-model="右侧新建文件夹名称"
                            class="resource-row__input"
                            :disabled="正在提交右侧新建文件夹"
                            placeholder="新建文件夹"
                            @click.stop
                            @mousedown.stop
                            @keydown="处理右侧新建文件夹键盘事件"
                            @blur="处理右侧新建文件夹输入框失焦"
                          >
                          <input
                            v-else-if="是否资源正在右侧重命名(resource)"
                            :ref="设置列表重命名输入框引用"
                            v-model="列表重命名名称"
                            class="resource-row__input"
                            :disabled="正在提交列表重命名"
                            @click.stop
                            @mousedown.stop
                            @keydown="处理右侧重命名键盘事件"
                            @blur="处理右侧重命名输入框失焦"
                          >
                          <button
                            v-else
                            type="button"
                            class="resource-row__name"
                            @click.stop="是否文件夹资源(resource) ? void 进入文件夹(resource.item.id) : 打开文件(resource.item.url)"
                          >
                            {{ 是否文件夹资源(resource) ? resource.item.name : resource.item.original_name }}
                          </button>
                          <div
                            v-if="!是否资源是右侧新建文件夹草稿(resource) && 获取资源附加说明(resource)"
                            class="resource-row__path"
                          >
                            {{ 获取资源附加说明(resource) }}
                          </div>
                          <div
                            v-if="!是否资源是右侧新建文件夹草稿(resource) && 获取资源路径(resource)"
                            class="resource-row__path"
                          >
                            {{ 获取资源路径(resource) }}
                          </div>
                          <div class="resource-row__meta">
                            <template v-if="是否资源是右侧新建文件夹草稿(resource)">
                              <ElTag size="small" effect="plain">文件夹</ElTag>
                              <span>输入名称后按回车创建，按 Esc 取消</span>
                            </template>
                            <template v-else>
                              <ElTag v-if="获取资源用途标签(resource)" size="small" type="success" effect="plain">
                                {{ 获取资源用途标签(resource) }}
                              </ElTag>
                              <ElTag size="small" effect="plain">{{ 获取资源主标签(resource) }}</ElTag>
                              <template v-if="是否文件资源(resource)">
                                <span>{{ 格式化大小(resource.item.size) }}</span>
                                <span>{{ resource.item.mime_type }}</span>
                              </template>
                              <span>{{ 格式化时间(获取资源时间(resource)) }}</span>
                            </template>
                          </div>
                        </div>
                      </div>
                    </div>
                  </section>
                </template>
              </div>
            </section>
          </div>

          <div class="explorer-footer">
            <span class="explorer-footer__text">{{ 底部状态文案 }}</span>
            <div v-if="刷新中" class="explorer-footer__status" aria-label="正在刷新列表" role="status">
              <ElIcon class="explorer-footer__spinner is-loading" aria-hidden="true">
                <Loading />
              </ElIcon>
            </div>
          </div>
        </ElCard>
      </ElSkeleton>
    </div>

    <div v-if="已选资源总数 > 0" class="selection-toolbar">
      <div class="selection-toolbar__summary">
        <span>已选择 {{ 已选资源总数 }} 项</span>
      </div>
      <div class="selection-toolbar__actions">
        <ElButton @click="切换当前页全选">
          {{ 是否已全选当前页 ? '取消全选' : '全选' }}
        </ElButton>
        <ElButton @click="清空选择">退出选择</ElButton>
        <ElButton @click="下载资源()">{{ 下载操作按钮文案 }}</ElButton>
        <ElButton :disabled="!当前选择可移动" @click="打开移动对话框()">{{ 已选资源移动文案 }}</ElButton>
        <ElButton
          v-if="!是否全局搜索模式"
          @click="打开批量重命名对话框"
        >
          {{ 已选资源重命名文案 }}
        </ElButton>
        <ElButton type="danger" @click="批量删除资源()">{{ 已选资源删除文案 }}</ElButton>
      </div>
    </div>

    <BaseDialog v-model="移动对话框可见" title="移动资源" width="420px">
      <div class="move-dialog__summary">
        即将移动 {{ 待移动资源列表.length }} 项资源，选择下方目标目录即可。
      </div>

      <div class="move-dialog__picker">
        <button
          type="button"
          class="move-dialog__root"
          :class="{ 'is-active': 移动目标目录ID === null }"
          @click="移动目标目录ID = null"
        >
          <ElIcon><FolderOpened /></ElIcon>
          <span>{{ 根目录名称 }}</span>
        </button>

        <ElTree
          :data="目录树数据"
          node-key="id"
          default-expand-all
          :current-node-key="移动目标目录ID ?? 根目录节点键"
          :expand-on-click-node="false"
          empty-text="暂无文件夹"
          @node-click="(data: 目录树节点) => { 移动目标目录ID = data.isRoot ? null : data.id }"
        >
          <template #default="{ data }">
            <div class="tree-node">
              <ElIcon class="tree-node__icon">
                <component :is="data.isRoot || data.id === 移动目标目录ID ? FolderOpened : Folder" />
              </ElIcon>
              <span class="tree-node__label">{{ data.name }}</span>
            </div>
          </template>
        </ElTree>
      </div>

      <template #footer>
        <ElButton @click="移动对话框可见 = false">取消</ElButton>
        <ElButton type="primary" @click="确认移动资源">确认移动</ElButton>
      </template>
    </BaseDialog>

    <BaseDialog v-model="批量重命名对话框可见" :title="重命名对话框标题" width="460px">
      <div class="batch-rename-form">
        <div class="batch-rename-form__row">
          <span class="batch-rename-form__label">名称前缀</span>
          <ElInput v-model="批量重命名前缀" placeholder="例如：素材-" />
        </div>
        <div class="batch-rename-form__grid">
          <div class="batch-rename-form__row">
            <span class="batch-rename-form__label">起始序号</span>
            <ElInputNumber v-model="批量重命名起始序号" :min="1" :step="1" />
          </div>
          <div class="batch-rename-form__row">
            <span class="batch-rename-form__label">补零位数</span>
            <ElInputNumber v-model="批量重命名位数" :min="1" :max="8" :step="1" />
          </div>
        </div>
        <ElCheckbox v-model="批量重命名保留扩展名">文件保留原扩展名</ElCheckbox>
        <ElText type="info">
          会按当前排序顺序执行，文件夹排在文件前面。
        </ElText>
      </div>

      <template #footer>
        <ElButton @click="批量重命名对话框可见 = false">取消</ElButton>
        <ElButton type="primary" @click="确认批量重命名">确认重命名</ElButton>
      </template>
    </BaseDialog>

    <BaseDialog
      v-model="媒体预览对话框可见"
      title="媒体预览"
      width="min(980px, 94vw)"
      top="4vh"
      class="image-preview-dialog"
    >
      <template v-if="当前预览媒体">
        <div class="image-preview">
          <img
            v-if="是否图片(当前预览媒体)"
            :src="获取可预览文件链接(当前预览媒体.url)"
            :alt="当前预览媒体.original_name"
          >
          <video
            v-else-if="是否视频(当前预览媒体)"
            :src="获取可预览文件链接(当前预览媒体.url)"
            controls
            preload="metadata"
          />
        </div>
        <div class="image-preview__footer">
          <div class="image-preview__meta">
            <strong>{{ 当前预览媒体.original_name }}</strong>
            <ElText type="info">
              {{ 当前预览媒体索引 + 1 }} / {{ 可预览媒体文件列表.length }} · {{ 格式化大小(当前预览媒体.size) }}
            </ElText>
          </div>
          <ElSpace wrap>
            <ElButton :disabled="当前预览媒体索引 <= 0" @click="切换预览媒体(-1)">上一项</ElButton>
            <ElButton :disabled="当前预览媒体索引 >= 可预览媒体文件列表.length - 1" @click="切换预览媒体(1)">下一项</ElButton>
            <ElButton @click="打开文件(当前预览媒体.url)">新窗口打开</ElButton>
            <ElButton v-if="是否文章图片(当前预览媒体)" @click="复制文章图片链接(当前预览媒体.url)">复制文章图片链接</ElButton>
          </ElSpace>
        </div>
      </template>
    </BaseDialog>

    <div
      v-if="右键菜单.visible"
      class="context-menu"
      :style="{ left: `${右键菜单.x}px`, top: `${右键菜单.y}px` }"
      @click.stop
    >
      <template v-if="右键菜单.scope === 'blank'">
        <button type="button" class="context-menu__item" @click="在右侧新建文件夹">新建文件夹</button>
        <button type="button" class="context-menu__item" @click="触发文件上传">上传文件</button>
        <button type="button" class="context-menu__item" @click="触发目录上传">上传目录</button>
        <button
          v-if="已选资源总数 > 0"
          type="button"
          class="context-menu__item"
          @click="下载资源()"
        >
          {{ 已选资源下载菜单文案 }}
        </button>
        <button
          v-if="已选资源总数 > 0 && 当前选择可移动"
          type="button"
          class="context-menu__item"
          @click="打开移动对话框()"
        >
          {{ 已选资源移动菜单文案 }}
        </button>
        <button
          v-if="已选资源总数 > 0 && !是否全局搜索模式"
          type="button"
          class="context-menu__item"
          @click="打开批量重命名对话框"
        >
          {{ 已选资源重命名文案 }}
        </button>
        <button
          v-if="已选资源总数 > 0"
          type="button"
          class="context-menu__item is-danger"
          @click="批量删除资源()"
        >
          {{ 已选资源删除菜单文案 }}
        </button>
      </template>

      <template v-else-if="右键菜单.scope === 'folder' && 右键菜单文件夹">
        <button type="button" class="context-menu__item" @click="进入文件夹(右键菜单文件夹.id)">打开文件夹</button>
        <button type="button" class="context-menu__item" @click="下载资源({ type: 'folder', id: 右键菜单文件夹.id })">打包下载</button>
        <button type="button" class="context-menu__item" @click="重命名文件夹(右键菜单文件夹)">重命名</button>
        <button
          type="button"
          class="context-menu__item"
          @click="打开移动对话框({ type: 'folder', id: 右键菜单文件夹.id })"
        >
          移动到
        </button>
        <button
          type="button"
          class="context-menu__item"
          @click="设置文件夹选中(右键菜单文件夹.id, !是否选中文件夹(右键菜单文件夹.id)); 关闭右键菜单()"
        >
          {{ 是否选中文件夹(右键菜单文件夹.id) ? '取消选择' : '选择此文件夹' }}
        </button>
        <button type="button" class="context-menu__item is-danger" @click="确认删除文件夹(右键菜单文件夹)">
          删除
        </button>
      </template>

      <template v-else-if="右键菜单.scope === 'file' && 右键菜单文件">
        <button
          v-if="是否可预览媒体(右键菜单文件)"
          type="button"
          class="context-menu__item"
          @click="打开媒体预览(右键菜单文件)"
        >
          预览媒体
        </button>
        <button type="button" class="context-menu__item" @click="打开文件(右键菜单文件.url)">打开文件</button>
        <button
          v-if="是否文章图片(右键菜单文件) && 右键菜单文件.article_id"
          type="button"
          class="context-menu__item"
          @click="打开文章编辑器(右键菜单文件.article_id)"
        >
          编辑文章
        </button>
        <button
          v-else-if="是否全局搜索模式"
          type="button"
          class="context-menu__item"
          @click="进入文件夹(右键菜单文件.folder_id)"
        >
          打开所在目录
        </button>
        <button type="button" class="context-menu__item" @click="下载资源({ type: 'file', id: 右键菜单文件.id })">直接下载</button>
        <button type="button" class="context-menu__item" @click="重命名文件(右键菜单文件)">重命名</button>
        <button
          v-if="是否可移动文件(右键菜单文件)"
          type="button"
          class="context-menu__item"
          @click="打开移动对话框({ type: 'file', id: 右键菜单文件.id })"
        >
          移动到
        </button>
        <button
          v-if="是否文章图片(右键菜单文件)"
          type="button"
          class="context-menu__item"
          @click="复制文章图片链接(右键菜单文件.url)"
        >
          复制文章图片链接
        </button>
        <button
          type="button"
          class="context-menu__item"
          @click="设置文件选中(右键菜单文件.id, !是否选中文件(右键菜单文件.id)); 关闭右键菜单()"
        >
          {{ 是否选中文件(右键菜单文件.id) ? '取消选择' : '选择此文件' }}
        </button>
        <button type="button" class="context-menu__item is-danger" @click="批量删除资源({ type: 'file', id: 右键菜单文件.id })">
          删除
        </button>
      </template>
    </div>
  </div>
</template>

<style scoped>
.page-container {
  position: relative;
  height: 100%;
  min-height: 0;
  overflow: hidden;
  padding: 14px 24px 24px;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
}

.hidden-input {
  display: none;
}

.page-body {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.page-skeleton {
  height: 100%;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 10px;
  flex-shrink: 0;
}

.page-heading {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
}

.page-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.page-action-icon {
  width: 16px;
  height: 16px;
  margin-right: 6px;
  flex-shrink: 0;
}

.explorer-shell {
  border-radius: 18px;
  height: 100%;
  min-height: 0;
}

.explorer-shell :deep(.el-card__body) {
  display: flex;
  flex-direction: column;
  padding: 4px 24px 12px;
  height: 100%;
  overflow: hidden;
  box-sizing: border-box;
}

.explorer-layout {
  display: grid;
  grid-template-columns: clamp(220px, var(--explorer-sidebar-width), 520px) 20px minmax(0, 1fr);
  gap: 0;
  align-items: stretch;
  flex: 1;
  min-height: 0;
}

.explorer-sidebar,
.explorer-main {
  min-width: 0;
  min-height: 0;
}

.explorer-sidebar {
  display: flex;
  flex-direction: column;
  padding-top: 12px;
  padding-right: 20px;
}

.explorer-tree {
  flex: 1;
  min-height: 0;
  overflow: auto;
  padding-right: 4px;
}

.explorer-main {
  display: flex;
  flex-direction: column;
  padding-top: 12px;
  padding-left: 20px;
  overflow: hidden;
}

.explorer-resizer {
  position: relative;
  width: 20px;
  padding: 0;
  border: none;
  background: transparent;
  cursor: col-resize;
  touch-action: none;
}

.explorer-resizer::before {
  content: '';
  position: absolute;
  top: 0;
  bottom: 0;
  left: 50%;
  width: 1px;
  transform: translateX(-50%);
  background: var(--el-border-color);
  transition: background-color 0.2s ease, box-shadow 0.2s ease;
}

.explorer-resizer__handle {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 6px;
  height: 128px;
  border-radius: 999px;
  transform: translate(-50%, -50%);
  background: linear-gradient(
    180deg,
    rgba(24, 160, 88, 0.18),
    rgba(24, 160, 88, 0.5),
    rgba(24, 160, 88, 0.18)
  );
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.explorer-resizer:hover::before,
.explorer-resizer.is-dragging::before {
  background: rgba(24, 160, 88, 0.56);
  box-shadow: 0 0 0 1px rgba(24, 160, 88, 0.12);
}

.explorer-resizer:hover .explorer-resizer__handle,
.explorer-resizer.is-dragging .explorer-resizer__handle {
  transform: translate(-50%, -50%) scaleX(1.1);
}

.sidebar-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 18px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.sidebar-card__actions {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.sidebar-action-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  padding: 0;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--el-text-color-secondary);
  cursor: pointer;
  transition: background-color 0.18s ease, color 0.18s ease;
}

.sidebar-action-button:hover {
  background: var(--el-fill-color-light);
  color: var(--el-text-color-primary);
}

.sidebar-action-button:focus-visible {
  outline: 2px solid rgba(24, 160, 88, 0.28);
  outline-offset: 2px;
}

.sidebar-action-button:disabled {
  opacity: 0.48;
  cursor: not-allowed;
}

.sidebar-action-button__icon {
  width: 16px;
  height: 16px;
}

.explorer-content {
  flex: 1;
  min-height: 0;
  overflow: auto;
  padding-right: 4px;
}

.explorer-content--with-selection {
  padding-bottom: 108px;
}

.sidebar-card__title,
.resource-section__title {
  margin: 0;
}

.sidebar-card__desc,
.resource-section__desc {
  margin: 6px 0 0;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.tree-node {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  min-width: 0;
  padding: 4px 0;
}

.tree-node--draft {
  padding-right: 6px;
}

.tree-node--editing {
  padding-right: 6px;
}

.tree-node__icon {
  color: #18a058;
  flex-shrink: 0;
}

.tree-node__label {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tree-node__input {
  width: 100%;
  min-width: 0;
  height: 22px;
  padding: 0 6px;
  border: 1px solid rgba(24, 160, 88, 0.32);
  border-radius: 4px;
  background: var(--el-fill-color-blank);
  color: var(--el-text-color-primary);
  font: inherit;
  line-height: 22px;
}

.tree-node__input::placeholder {
  color: var(--el-text-color-placeholder);
}

.tree-node__input:focus {
  outline: none;
  border-color: rgba(24, 160, 88, 0.78);
  box-shadow: 0 0 0 1px rgba(24, 160, 88, 0.16);
}

.tree-node__input:disabled {
  opacity: 0.7;
  cursor: progress;
}

.explorer-toolbar {
  display: block;
  min-width: 0;
  line-height: 1;
}

.breadcrumb-trail {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
  min-height: 28px;
}

.breadcrumb-trail :deep(.el-breadcrumb) {
  display: flex;
  align-items: center;
  min-width: 0;
  line-height: 1;
}

.breadcrumb-trail :deep(.el-breadcrumb__item) {
  display: flex;
  align-items: center;
}

.breadcrumb-trail :deep(.el-breadcrumb__inner) {
  display: inline-flex;
  align-items: center;
  line-height: 1;
}

.breadcrumb-trail :deep(.el-breadcrumb__separator) {
  display: inline-flex;
  align-items: center;
  line-height: 1;
}

.breadcrumb-button,
.resource-row__name {
  padding: 0;
  border: none;
  background: transparent;
  color: inherit;
  font: inherit;
  text-align: left;
  cursor: pointer;
}

.breadcrumb-button {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 2px;
  border-radius: 8px;
}

.breadcrumb-button:hover,
.resource-row__name:hover {
  color: var(--el-color-primary);
}

.filter-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 8px;
  flex-wrap: wrap;
}

.page-filter-toolbar {
  margin-top: 0;
  margin-bottom: 14px;
  flex-shrink: 0;
}

.filter-toolbar__search {
  flex: 1;
  min-width: 220px;
}

.filter-toolbar__scope {
  width: 140px;
}

.filter-toolbar__sort {
  width: 180px;
}

.selection-toolbar {
  position: fixed;
  left: 50%;
  bottom: calc(24px + var(--app-safe-area-bottom));
  transform: translateX(-50%);
  z-index: 1200;
  width: min(960px, calc(100vw - 48px));
  padding: 14px 16px;
  border: 1px solid rgba(24, 160, 88, 0.22);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(18px);
  box-shadow: 0 18px 48px rgba(15, 23, 42, 0.16);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.selection-toolbar__summary {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
  color: var(--el-text-color-primary);
  font-size: 14px;
  font-weight: 600;
}

.selection-toolbar__actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  flex-wrap: wrap;
}

.resource-section {
  margin-top: 24px;
}

.resource-section__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.resource-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.resource-row {
  position: relative;
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px;
  border: 1px solid var(--el-border-color);
  border-radius: 16px;
  background: var(--el-fill-color-blank);
  transition: border-color 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease, background-color 0.2s ease;
}

.resource-row--folder {
  cursor: pointer;
}

.resource-row--editing {
  cursor: default;
}

.resource-row:hover {
  border-color: rgba(24, 160, 88, 0.35);
  transform: translateY(-1px);
  box-shadow: 0 14px 28px rgba(15, 23, 42, 0.08);
}

.resource-row.is-selected {
  border-color: rgba(24, 160, 88, 0.45);
  background: rgba(24, 160, 88, 0.06);
}

.resource-selector {
  display: flex;
  align-items: center;
  align-self: flex-start;
  flex-shrink: 0;
}

.resource-row__preview,
.resource-row__icon {
  width: 72px;
  height: 72px;
  border-radius: 16px;
  overflow: hidden;
  flex-shrink: 0;
  background: var(--el-fill-color-light);
}

.resource-row__preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  cursor: zoom-in;
}

.resource-row__preview--video {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 0;
  border: none;
  color: #fff;
  background:
    linear-gradient(160deg, rgba(15, 23, 42, 0.92), rgba(30, 41, 59, 0.82)),
    radial-gradient(circle at top, rgba(24, 160, 88, 0.36), transparent 60%);
  cursor: pointer;
}

.resource-row__preview--video .el-icon {
  font-size: 26px;
}

.resource-row__preview-badge {
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.12);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.resource-row__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--el-color-primary);
  font-size: 28px;
}

.resource-row__icon--folder {
  background: rgba(24, 160, 88, 0.12);
  color: #18a058;
}

.resource-row__body {
  min-width: 0;
  flex: 1;
}

.resource-row__name {
  display: inline-block;
  max-width: 100%;
  font-size: 15px;
  font-weight: 600;
}

.resource-row__input {
  width: min(420px, 100%);
  max-width: 100%;
  height: 32px;
  padding: 0 10px;
  border: 1px solid rgba(24, 160, 88, 0.32);
  border-radius: 8px;
  background: var(--el-fill-color-blank);
  color: var(--el-text-color-primary);
  font: inherit;
  font-size: 15px;
  font-weight: 600;
  line-height: 32px;
}

.resource-row__input::placeholder {
  color: var(--el-text-color-placeholder);
}

.resource-row__input:focus {
  outline: none;
  border-color: rgba(24, 160, 88, 0.78);
  box-shadow: 0 0 0 1px rgba(24, 160, 88, 0.16);
}

.resource-row__input:disabled {
  opacity: 0.7;
  cursor: progress;
}

.resource-row__path {
  margin-top: 8px;
  color: var(--el-text-color-secondary);
  font-size: 13px;
  line-height: 1.5;
  word-break: break-all;
}

.resource-row__meta {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 8px;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.explorer-footer {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 12px;
  padding-top: 8px;
  border-top: 1px solid var(--el-border-color-lighter);
  color: var(--el-text-color-secondary);
  font-size: 12px;
  flex-wrap: wrap;
  flex-shrink: 0;
}

.explorer-footer__text {
  min-width: 0;
}

.explorer-footer__status {
  margin-left: auto;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  min-height: 20px;
}

.explorer-footer__spinner {
  font-size: 14px;
  color: #18a058;
}

.explorer-footer__divider {
  width: 1px;
  height: 10px;
  background: var(--el-border-color);
}

.dark .selection-toolbar {
  background: rgba(24, 24, 28, 0.92);
  border-color: rgba(64, 158, 255, 0.32);
  box-shadow: 0 18px 48px rgba(0, 0, 0, 0.36);
}

.dark .sidebar-action-button:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
}

.dark .tree-node__input {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(64, 158, 255, 0.34);
  color: #fff;
}

.dark .tree-node__input:focus {
  border-color: rgba(64, 158, 255, 0.88);
  box-shadow: 0 0 0 1px rgba(64, 158, 255, 0.22);
}

.dark .resource-row__input {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(64, 158, 255, 0.34);
  color: #fff;
}

.dark .resource-row__input:focus {
  border-color: rgba(64, 158, 255, 0.88);
  box-shadow: 0 0 0 1px rgba(64, 158, 255, 0.22);
}

.dark .selection-toolbar__summary {
  color: #fff;
}

.move-dialog__summary {
  margin-bottom: 14px;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.batch-rename-form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.batch-rename-form__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.batch-rename-form__row {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.batch-rename-form__label {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.move-dialog__picker {
  border: 1px solid var(--el-border-color);
  border-radius: 16px;
  padding: 12px;
  max-height: 360px;
  overflow: auto;
}

.move-dialog__root {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  margin-bottom: 10px;
  padding: 10px 12px;
  border: 1px solid var(--el-border-color);
  border-radius: 12px;
  background: var(--el-fill-color-blank);
  cursor: pointer;
}

.move-dialog__root.is-active {
  border-color: rgba(24, 160, 88, 0.45);
  background: rgba(24, 160, 88, 0.08);
}

.image-preview {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
  border-radius: 16px;
  background:
    radial-gradient(circle at top, rgba(24, 160, 88, 0.12), transparent 48%),
    linear-gradient(135deg, rgba(15, 23, 42, 0.05), rgba(15, 23, 42, 0.12));
  overflow: hidden;
}

.image-preview img {
  max-width: 100%;
  max-height: 72vh;
  object-fit: contain;
  display: block;
}

.image-preview video {
  width: 100%;
  max-height: 72vh;
  border-radius: 16px;
  background: rgba(15, 23, 42, 0.92);
}

.image-preview__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-top: 14px;
  flex-wrap: wrap;
}

.image-preview__meta {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.context-menu {
  position: fixed;
  z-index: 3000;
  min-width: 180px;
  padding: 8px;
  border: 1px solid var(--el-border-color);
  border-radius: 14px;
  background: var(--el-bg-color);
  box-shadow: 0 20px 40px rgba(15, 23, 42, 0.18);
}

.context-menu__item {
  display: block;
  width: 100%;
  padding: 9px 12px;
  border: none;
  border-radius: 10px;
  background: transparent;
  text-align: left;
  color: var(--el-text-color-regular);
  cursor: pointer;
}

.context-menu__item:hover {
  background: var(--el-fill-color-light);
}

.context-menu__item.is-danger {
  color: var(--el-color-danger);
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 220px;
}

.empty-state--inner {
  min-height: 160px;
  border: 1px dashed var(--el-border-color);
  border-radius: 16px;
  background: var(--el-fill-color-lighter);
}

@media (max-width: 960px) {
  .explorer-layout {
    grid-template-columns: 1fr;
    grid-template-rows: minmax(220px, 280px) minmax(0, 1fr);
  }

  .explorer-sidebar {
    padding-right: 0;
    padding-bottom: 20px;
    border-bottom: 1px solid var(--el-border-color-lighter);
  }

  .explorer-resizer {
    display: none;
  }

  .explorer-main {
    padding-left: 0;
    padding-top: 20px;
  }
}

@media (max-width: 768px) {
  .page-container {
    padding: 12px 16px 16px;
  }

  .page-header {
    flex-direction: column;
    align-items: stretch;
  }

  .page-actions {
    justify-content: flex-start;
  }

  .page-filter-toolbar {
    margin-bottom: 12px;
  }

  .explorer-content--with-selection {
    padding-bottom: 168px;
  }

  .explorer-shell :deep(.el-card__body) {
    padding: 4px 16px 10px;
  }

  .resource-row {
    flex-direction: column;
    align-items: stretch;
  }

  .resource-selector {
    align-self: flex-start;
  }

  .explorer-footer__divider {
    display: none;
  }

  .selection-toolbar {
    width: calc(100vw - 20px);
    bottom: calc(12px + var(--app-safe-area-bottom));
    padding: 12px;
    border-radius: 14px;
    flex-direction: column;
    align-items: stretch;
  }

  .selection-toolbar__actions {
    justify-content: stretch;
  }

  .selection-toolbar__actions :deep(.el-button) {
    flex: 1 1 calc(50% - 4px);
    min-width: 0;
    margin-left: 0;
  }
}
</style>
