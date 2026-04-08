<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import {
  ElBreadcrumb,
  ElBreadcrumbItem,
  ElButton,
  ElCard,
  ElCheckbox,
  ElDialog,
  ElEmpty,
  ElIcon,
  ElInput,
  ElInputNumber,
  ElMessage,
  ElMessageBox,
  ElOption,
  ElPopconfirm,
  ElSelect,
  ElSkeleton,
  ElSpace,
  ElTag,
  ElText,
  ElTree,
} from 'element-plus'
import {
  Delete,
  Document,
  EditPen,
  Folder,
  FolderOpened,
  Link,
  Picture,
  Plus,
  UploadFilled,
} from '@element-plus/icons-vue'
import {
  createFolder as requestCreateFolder,
  deleteFile as requestDeleteFile,
  deleteFolder as requestDeleteFolder,
  downloadArchive as requestDownloadArchive,
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

type 资源类型 = 'folder' | 'file'
type 右键菜单范围 = 'blank' | 'folder' | 'file'
type 排序方式 = 'name-asc' | 'name-desc' | 'time-desc' | 'time-asc' | 'size-desc' | 'size-asc'
type 搜索范围 = 'current' | 'global'
type 文件夹展示项 = FileFolderItem | FileSearchFolderItem
type 文件展示项 = FileItem | FileSearchFileItem
type 带目录路径文件 = globalThis.File & {
  webkitRelativePath?: string
}

interface 资源标识 {
  type: 资源类型
  id: string
}

interface 目录树节点 extends FileTreeNode {
  isRoot?: boolean
}

interface 右键菜单状态 {
  visible: boolean
  x: number
  y: number
  scope: 右键菜单范围
  resource: 资源标识 | null
}

const 根目录节点键 = '__root__'
const 拖拽数据类型 = 'application/x-web-system-resource'
const 根目录名称 = '全部文件'
const 资源数据 = ref<FileExplorerData | null>(null)
const 加载中 = ref(true)
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
const 图片预览对话框可见 = ref(false)
const 移动目标目录ID = ref<string | null>(null)
const 当前预览图片ID = ref<string | null>(null)
const 待移动资源列表 = ref<资源标识[]>([])
const 文件上传输入框 = ref<globalThis.HTMLInputElement | null>(null)
const 目录上传输入框 = ref<globalThis.HTMLInputElement | null>(null)
const 批量重命名前缀 = ref('资源-')
const 批量重命名起始序号 = ref(1)
const 批量重命名位数 = ref(2)
const 批量重命名保留扩展名 = ref(true)
const 右键菜单 = ref<右键菜单状态>({
  visible: false,
  x: 0,
  y: 0,
  scope: 'blank',
  resource: null,
})
let 全局搜索定时器: ReturnType<typeof window.setTimeout> | null = null
let 全局搜索序号 = 0

const 当前目录 = computed(() => 资源数据.value?.current_folder ?? null)
const 面包屑列表 = computed<FileBreadcrumbItem[]>(() => (
  资源数据.value?.breadcrumbs ?? [{ id: null, name: 根目录名称 }]
))
const 原始子文件夹列表 = computed<FileFolderItem[]>(() => 资源数据.value?.folders ?? [])
const 原始文件列表 = computed<FileItem[]>(() => 资源数据.value?.files ?? [])
const 当前目录名称 = computed(() => 当前目录.value?.name ?? 根目录名称)
const 选中目录树节点键 = computed(() => 当前目录ID.value ?? 根目录节点键)
const 目录树数据 = computed<目录树节点[]>(() => ([
  {
    id: 根目录节点键,
    parent_id: null,
    name: 根目录名称,
    isRoot: true,
    children: 资源数据.value?.tree ?? [],
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

const 子文件夹列表 = computed<FileFolderItem[]>(() => 排序文件夹列表(
  原始子文件夹列表.value.filter((folder) => 是否匹配搜索关键词(folder.name)),
))
const 文件列表 = computed<FileItem[]>(() => 排序文件列表(
  原始文件列表.value.filter((file) => 是否匹配搜索关键词(file.original_name)),
))
const 当前展示文件夹列表 = computed<文件夹展示项[]>(() => (
  是否全局搜索模式.value ? 全局搜索文件夹结果.value : 子文件夹列表.value
))
const 当前展示文件列表 = computed<文件展示项[]>(() => (
  是否全局搜索模式.value ? 全局搜索文件结果.value : 文件列表.value
))
const 当前目录文件夹总数 = computed(() => 原始子文件夹列表.value.length)
const 当前目录文件总数 = computed(() => 原始文件列表.value.length)
const 当前页资源总数 = computed(() => 当前展示文件夹列表.value.length + 当前展示文件列表.value.length)
const 已选资源总数 = computed(() => 已选文件夹.value.size + 已选文件.value.size)
const 当前空状态描述 = computed(() => {
  if (是否全局搜索模式.value) {
    return 全局搜索中.value ? '正在跨目录搜索...' : '没有找到匹配的资源'
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
const 图片文件列表 = computed<文件展示项[]>(() => 当前展示文件列表.value.filter((file) => 是否图片(file)))
const 搜索框占位文案 = computed(() => (
  搜索范围值.value === 'global' ? '跨目录搜索文件夹和文件' : '搜索当前目录中的文件夹和文件'
))
const 统计文案 = computed(() => {
  if (搜索范围值.value === 'global') {
    if (!搜索关键词.value.trim()) {
      return '输入关键词后会在全部目录内搜索'
    }
    if (全局搜索中.value) {
      return `正在搜索“${搜索关键词.value.trim()}”`
    }
    return `共找到 ${全局搜索文件夹结果.value.length} 个文件夹、${全局搜索文件结果.value.length} 个文件`
  }
  return `当前显示 ${子文件夹列表.value.length} 个文件夹、${文件列表.value.length} 个文件`
})
const 主区域标题 = computed(() => (是否全局搜索模式.value ? '跨目录搜索结果' : 当前目录名称.value))
const 主区域描述 = computed(() => {
  if (是否全局搜索模式.value) {
    return `关键词“${搜索关键词.value.trim()}”共匹配 ${全局搜索结果总数.value} 项资源。`
  }
  return `当前目录包含 ${当前目录文件夹总数.value} 个文件夹、${当前目录文件总数.value} 个文件。`
})
const 当前预览图片索引 = computed(() => 图片文件列表.value.findIndex((file) => file.id === 当前预览图片ID.value))
const 当前预览图片 = computed(() => {
  const currentIndex = 当前预览图片索引.value
  if (currentIndex < 0) {
    return null
  }
  return 图片文件列表.value[currentIndex] ?? null
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
  return 当前展示文件夹列表.value.find((folder) => folder.id === 右键菜单.value.resource?.id) ?? null
})

onMounted(() => {
  window.addEventListener('click', 关闭右键菜单)
  window.addEventListener('resize', 关闭右键菜单)
  window.addEventListener('blur', 关闭右键菜单)
  void 拉取资源()
})

onBeforeUnmount(() => {
  window.removeEventListener('click', 关闭右键菜单)
  window.removeEventListener('resize', 关闭右键菜单)
  window.removeEventListener('blur', 关闭右键菜单)
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

async function 拉取资源(folderId: string | null = 当前目录ID.value) {
  加载中.value = true
  try {
    const data = await fetchExplorer(folderId)
    应用资源数据(data)
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '加载资源失败'))
  } finally {
    加载中.value = false
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
  await 拉取资源(folderId)
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

function 处理树节点点击(data: 目录树节点) {
  void 进入文件夹(data.isRoot ? null : data.id)
}

async function 打开文件夹(folderId: string | null) {
  关闭右键菜单()
  await 拉取资源(folderId)
}

async function 进入文件夹(folderId: string | null) {
  搜索范围值.value = 'current'
  await 打开文件夹(folderId)
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
  try {
    const { value } = await ElMessageBox.prompt('请输入文件夹名称', '新建文件夹', {
      confirmButtonText: '创建',
      cancelButtonText: '取消',
      inputPlaceholder: '例如：素材库',
    })
    await requestCreateFolder(value, 当前目录ID.value)
    ElMessage.success('文件夹已创建')
    await 刷新当前视图()
  } catch (error) {
    if (是否消息框取消(error)) {
      return
    }
    ElMessage.error(getApiErrorMessage(error, '创建文件夹失败'))
  }
}

async function 重命名文件夹(folder: 文件夹展示项) {
  关闭右键菜单()
  try {
    const { value } = await ElMessageBox.prompt('请输入新的文件夹名称', '重命名文件夹', {
      confirmButtonText: '保存',
      cancelButtonText: '取消',
      inputValue: folder.name,
    })
    await requestRenameFolder(folder.id, value)
    ElMessage.success('文件夹已重命名')
    await 刷新当前视图()
  } catch (error) {
    if (是否消息框取消(error)) {
      return
    }
    ElMessage.error(getApiErrorMessage(error, '重命名文件夹失败'))
  }
}

async function 重命名文件(file: 文件展示项) {
  关闭右键菜单()
  try {
    const { value } = await ElMessageBox.prompt('请输入新的文件名称', '重命名文件', {
      confirmButtonText: '保存',
      cancelButtonText: '取消',
      inputValue: file.original_name,
    })
    await requestRenameFile(file.id, value)
    ElMessage.success('文件已重命名')
    await 刷新当前视图()
  } catch (error) {
    if (是否消息框取消(error)) {
      return
    }
    ElMessage.error(getApiErrorMessage(error, '重命名文件失败'))
  }
}

async function 删除文件夹(folder: 文件夹展示项) {
  关闭右键菜单()
  try {
    await requestDeleteFolder(folder.id)
    ElMessage.success('文件夹已删除')
    await 刷新当前视图()
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '删除文件夹失败'))
  }
}

async function 删除当前文件夹() {
  关闭右键菜单()
  if (!当前目录.value) {
    return
  }
  const targetFolder = 当前目录.value
  try {
    await requestDeleteFolder(targetFolder.id)
    ElMessage.success('文件夹已删除')
    await 进入文件夹(targetFolder.parent_id)
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '删除文件夹失败'))
  }
}

async function 删除文件(id: string) {
  关闭右键菜单()
  try {
    await requestDeleteFile(id)
    ElMessage.success('文件已删除')
    await 刷新当前视图()
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '删除文件失败'))
  }
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
  const results = [
    ...(await Promise.allSettled(files.map((item) => requestDeleteFile(item.id)))),
    ...(await Promise.allSettled(folders.map((item) => requestDeleteFolder(item.id)))),
  ]
  const failResults = results.filter((result) => result.status === 'rejected')
  const successCount = results.length - failResults.length

  if (successCount > 0) {
    ElMessage.success(`已删除 ${successCount} 项资源`)
  }
  if (failResults.length > 0) {
    const firstError = failResults[0]
    if (firstError.status === 'rejected') {
      ElMessage.error(getApiErrorMessage(firstError.reason, `有 ${failResults.length} 项资源删除失败`))
    }
  }

  await 刷新当前视图()
}

function 打开移动对话框(resource?: 资源标识) {
  const targetResources = 获取操作资源列表(resource)
  if (!targetResources) {
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

function 查找文件夹展示项(id: string) {
  if (当前目录.value?.id === id) {
    return 当前目录.value
  }
  return 当前展示文件夹列表.value.find((item) => item.id === id)
    ?? 原始子文件夹列表.value.find((item) => item.id === id)
    ?? 资源数据.value?.tree.flatMap((node) => 收集目录树节点(node)).find((item) => item.id === id)
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

async function 打包下载资源(resource?: 资源标识) {
  const targetResources = 获取操作资源列表(resource)
  if (!targetResources) {
    return
  }

  关闭右键菜单()
  const folderIds = targetResources.filter((item) => item.type === 'folder').map((item) => item.id)
  const fileIds = targetResources.filter((item) => item.type === 'file').map((item) => item.id)
  const archiveName = 构建压缩包名称(targetResources)

  try {
    const blob = await requestDownloadArchive(folderIds, fileIds, archiveName)
    const downloadUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = `${archiveName}.zip`
    document.body.append(link)
    link.click()
    link.remove()
    window.setTimeout(() => {
      window.URL.revokeObjectURL(downloadUrl)
    }, 0)
    ElMessage.success('压缩包已开始下载')
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '打包下载失败'))
  }
}

function 打开图片预览(file: 文件展示项) {
  关闭右键菜单()
  当前预览图片ID.value = file.id
  图片预览对话框可见.value = true
}

function 切换预览图片(step: number) {
  const currentIndex = 当前预览图片索引.value
  if (currentIndex < 0) {
    return
  }
  const nextIndex = currentIndex + step
  if (nextIndex < 0 || nextIndex >= 图片文件列表.value.length) {
    return
  }
  当前预览图片ID.value = 图片文件列表.value[nextIndex]?.id ?? null
}

function 开始拖拽文件夹(folder: FileFolderItem, event: globalThis.DragEvent) {
  写入拖拽资源(event, {
    type: 'folder',
    id: folder.id,
  })
}

function 开始拖拽文件(file: FileItem, event: globalThis.DragEvent) {
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

  try {
    if (resource.type === 'file') {
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
  return /^https?:\/\//.test(url) ? url : new window.URL(url, window.location.origin).href
}

function 打开文件(url: string) {
  关闭右键菜单()
  window.open(解析链接(url), '_blank', 'noopener,noreferrer')
}

async function 复制链接(url: string) {
  关闭右键菜单()
  try {
    await navigator.clipboard.writeText(解析链接(url))
    ElMessage.success('链接已复制')
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

function 是否图片(file: 文件展示项) {
  return file.mime_type.startsWith('image/')
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

function 显示文件右键菜单(file: 文件展示项, event: globalThis.MouseEvent) {
  event.preventDefault()
  event.stopPropagation()
  右键菜单.value = {
    visible: true,
    x: event.clientX,
    y: event.clientY,
    scope: 'file',
    resource: { type: 'file', id: file.id },
  }
}

function 显示文件夹右键菜单(folder: 文件夹展示项, event: globalThis.MouseEvent) {
  event.preventDefault()
  event.stopPropagation()
  右键菜单.value = {
    visible: true,
    x: event.clientX,
    y: event.clientY,
    scope: 'folder',
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
      <div>
        <h2 class="page-title">
          <ElIcon><FolderOpened /></ElIcon>
          <span>资源管理器</span>
        </h2>
        <p class="page-subtitle">
          现在支持真实文件夹、跨目录搜索、压缩包下载、批量操作和目录上传。文章图片仍走文章编辑器上传，不会出现在这里。
        </p>
      </div>
      <div class="page-actions">
        <ElButton :disabled="正在上传" @click="新建文件夹">
          <ElIcon style="margin-right: 6px"><Plus /></ElIcon>
          <span>新建文件夹</span>
        </ElButton>
        <ElButton :loading="正在上传" @click="触发目录上传">
          <ElIcon style="margin-right: 6px"><Folder /></ElIcon>
          <span>上传目录</span>
        </ElButton>
        <ElButton type="primary" :loading="正在上传" @click="触发文件上传">
          <ElIcon style="margin-right: 6px"><UploadFilled /></ElIcon>
          <span>上传文件</span>
        </ElButton>
      </div>
    </div>

    <ElSkeleton :loading="加载中" animated>
      <div class="explorer-layout">
        <aside class="explorer-sidebar">
          <ElCard shadow="never" class="sidebar-card">
            <template #header>
              <div class="sidebar-card__header">
                <div>
                  <h3 class="sidebar-card__title">目录树</h3>
                  <p class="sidebar-card__desc">可把文件或文件夹拖到任意目录完成移动</p>
                </div>
              </div>
            </template>

            <ElTree
              :data="目录树数据"
              node-key="id"
              default-expand-all
              highlight-current
              :current-node-key="选中目录树节点键"
              :expand-on-click-node="false"
              empty-text="暂无文件夹"
              @node-click="处理树节点点击"
            >
              <template #default="{ data }">
                <div
                  class="tree-node"
                  @dragover.prevent
                  @drop="处理拖放到目录(data.isRoot ? null : data.id, $event)"
                >
                  <ElIcon class="tree-node__icon">
                    <component :is="data.isRoot || data.id === 当前目录ID ? FolderOpened : Folder" />
                  </ElIcon>
                  <span class="tree-node__label">{{ data.name }}</span>
                </div>
              </template>
            </ElTree>
          </ElCard>
        </aside>

        <section class="explorer-main">
          <ElCard shadow="never" class="explorer-card" @contextmenu="显示空白右键菜单">
            <div class="explorer-toolbar">
              <div class="explorer-toolbar__main">
                <ElBreadcrumb separator="/">
                  <ElBreadcrumbItem v-for="item in 面包屑列表" :key="item.id ?? 'root'">
                    <button
                      type="button"
                      class="breadcrumb-button"
                      @click="进入文件夹(item.id)"
                      @dragover.prevent
                      @drop="处理拖放到目录(item.id, $event)"
                    >
                      {{ item.name }}
                    </button>
                  </ElBreadcrumbItem>
                </ElBreadcrumb>
                <h3 class="explorer-title">{{ 主区域标题 }}</h3>
                <p class="explorer-description">
                  {{ 主区域描述 }}
                </p>
              </div>

              <ElSpace v-if="当前目录 && !是否全局搜索模式" wrap>
                <ElButton text @click="重命名文件夹(当前目录)">重命名目录</ElButton>
                <ElPopconfirm @confirm="删除当前文件夹">
                  <template #reference>
                    <ElButton text type="danger">删除当前目录</ElButton>
                  </template>
                  确定删除当前文件夹？仅空文件夹可删除。
                </ElPopconfirm>
              </ElSpace>
            </div>

            <div class="explorer-tip">
              <ElIcon><Link /></ElIcon>
              <span>支持右键菜单、批量选择、跨目录搜索，以及把文件或文件夹拖到左侧目录树、面包屑或下方文件夹卡片中完成移动。</span>
            </div>

            <div class="filter-toolbar">
              <ElInput
                v-model="搜索关键词"
                clearable
                :placeholder="搜索框占位文案"
                class="filter-toolbar__search"
              />
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
              <ElText type="info" class="filter-toolbar__count">
                {{ 统计文案 }}
              </ElText>
            </div>

            <div v-if="当前页资源总数 > 0" class="selection-toolbar">
              <ElSpace wrap>
                <ElTag effect="plain">已选 {{ 已选资源总数 }} 项</ElTag>
                <ElButton size="small" @click="切换当前页全选">
                  {{ 是否已全选当前页 ? '取消全选当前结果' : '全选当前结果' }}
                </ElButton>
                <ElButton size="small" :disabled="已选资源总数 === 0" @click="打包下载资源()">
                  打包下载
                </ElButton>
                <ElButton size="small" :disabled="已选资源总数 === 0" @click="打开移动对话框()">
                  批量移动
                </ElButton>
                <ElButton
                  v-if="!是否全局搜索模式"
                  size="small"
                  :disabled="已选资源总数 === 0"
                  @click="打开批量重命名对话框"
                >
                  批量重命名
                </ElButton>
                <ElButton size="small" type="danger" plain :disabled="已选资源总数 === 0" @click="批量删除资源()">
                  批量删除
                </ElButton>
                <ElButton size="small" text :disabled="已选资源总数 === 0" @click="清空选择">
                  清空选择
                </ElButton>
              </ElSpace>
            </div>

            <div v-if="当前页资源总数 === 0" class="empty-state empty-state--inner">
              <ElEmpty :description="当前空状态描述" />
            </div>

            <template v-else-if="是否全局搜索模式">
              <section class="resource-section">
                <div class="resource-section__header">
                  <div>
                    <h4 class="resource-section__title">匹配的文件夹</h4>
                    <p class="resource-section__desc">可直接打开目录、移动、删除或打包下载</p>
                  </div>
                  <ElTag effect="plain">{{ 全局搜索文件夹结果.length }} 个</ElTag>
                </div>

                <div v-if="全局搜索文件夹结果.length === 0" class="empty-state empty-state--inner">
                  <ElEmpty description="没有匹配到文件夹" />
                </div>

                <div v-else class="folder-grid">
                  <div
                    v-for="folder in 全局搜索文件夹结果"
                    :key="folder.id"
                    class="folder-card"
                    :class="{ 'is-selected': 是否选中文件夹(folder.id) }"
                    @click="进入文件夹(folder.id)"
                    @contextmenu="显示文件夹右键菜单(folder, $event)"
                  >
                    <div class="resource-selector" @click.stop>
                      <ElCheckbox
                        :model-value="是否选中文件夹(folder.id)"
                        @change="(checked) => 设置文件夹选中(folder.id, Boolean(checked))"
                      />
                    </div>

                    <div class="folder-card__icon">
                      <ElIcon><Folder /></ElIcon>
                    </div>

                    <div class="folder-card__body">
                      <div class="folder-card__title-row">
                        <strong class="folder-card__title">{{ folder.name }}</strong>
                        <ElText type="info" class="folder-card__time">{{ 格式化时间(folder.updated_at) }}</ElText>
                      </div>
                      <ElText type="info">跨目录搜索命中，可直接定位到该目录。</ElText>
                      <div class="resource-path">{{ folder.path }}</div>
                    </div>

                    <ElSpace size="small" class="folder-card__actions">
                      <ElButton text @click.stop="进入文件夹(folder.id)">打开目录</ElButton>
                      <ElButton text @click.stop="打包下载资源({ type: 'folder', id: folder.id })">下载</ElButton>
                      <ElButton text @click.stop="打开移动对话框({ type: 'folder', id: folder.id })">移动到</ElButton>
                      <ElPopconfirm @confirm="删除文件夹(folder)">
                        <template #reference>
                          <ElButton text type="danger" @click.stop>删除</ElButton>
                        </template>
                        确定删除此文件夹？仅空文件夹可删除。
                      </ElPopconfirm>
                    </ElSpace>
                  </div>
                </div>
              </section>

              <section class="resource-section">
                <div class="resource-section__header">
                  <div>
                    <h4 class="resource-section__title">匹配的文件</h4>
                    <p class="resource-section__desc">可直接打开文件、定位所在目录、复制链接或打包下载</p>
                  </div>
                  <ElTag effect="plain">{{ 全局搜索文件结果.length }} 个</ElTag>
                </div>

                <div v-if="全局搜索文件结果.length === 0" class="empty-state empty-state--inner">
                  <ElEmpty description="没有匹配到文件" />
                </div>

                <div v-else class="file-list">
                  <div
                    v-for="file in 全局搜索文件结果"
                    :key="file.id"
                    class="file-row"
                    :class="{ 'is-selected': 是否选中文件(file.id) }"
                    @contextmenu="显示文件右键菜单(file, $event)"
                  >
                    <div class="resource-selector" @click.stop>
                      <ElCheckbox
                        :model-value="是否选中文件(file.id)"
                        @change="(checked) => 设置文件选中(file.id, Boolean(checked))"
                      />
                    </div>

                    <div v-if="是否图片(file)" class="file-row__preview">
                      <img :src="file.url" :alt="file.original_name" @click.stop="打开图片预览(file)">
                    </div>
                    <div v-else class="file-row__icon">
                      <ElIcon><component :is="获取文件图标(file)" /></ElIcon>
                    </div>

                    <div class="file-row__body">
                      <button type="button" class="file-row__name" @click="打开文件(file.url)">
                        {{ file.original_name }}
                      </button>
                      <div class="file-row__path">{{ file.path }}</div>
                      <div class="file-row__meta">
                        <ElTag size="small" effect="plain">{{ 获取文件标签(file) }}</ElTag>
                        <span>{{ 格式化大小(file.size) }}</span>
                        <span>{{ file.mime_type }}</span>
                        <span>{{ 格式化时间(file.created_at) }}</span>
                      </div>
                    </div>

                    <ElSpace size="small" wrap class="file-row__actions">
                      <ElButton size="small" @click="打开文件(file.url)">打开</ElButton>
                      <ElButton size="small" @click="进入文件夹(file.folder_id)">所在目录</ElButton>
                      <ElButton size="small" @click="打包下载资源({ type: 'file', id: file.id })">打包下载</ElButton>
                      <ElButton size="small" @click="打开移动对话框({ type: 'file', id: file.id })">移动到</ElButton>
                      <ElButton size="small" @click="复制链接(file.url)">复制链接</ElButton>
                      <ElPopconfirm @confirm="删除文件(file.id)">
                        <template #reference>
                          <ElButton size="small" type="danger" text>删除</ElButton>
                        </template>
                        确定删除此文件？
                      </ElPopconfirm>
                    </ElSpace>
                  </div>
                </div>
              </section>
            </template>

            <template v-else>
              <section class="resource-section">
                <div class="resource-section__header">
                  <div>
                    <h4 class="resource-section__title">文件夹</h4>
                    <p class="resource-section__desc">点击进入，拖放可移动资源，右键可快速操作</p>
                  </div>
                  <ElTag effect="plain">{{ 子文件夹列表.length }} 个</ElTag>
                </div>

                <div v-if="子文件夹列表.length === 0" class="empty-state empty-state--inner">
                  <ElEmpty description="当前目录下暂无文件夹" />
                </div>

                <div v-else class="folder-grid">
                  <div
                    v-for="folder in 子文件夹列表"
                    :key="folder.id"
                    class="folder-card"
                    :class="{ 'is-selected': 是否选中文件夹(folder.id) }"
                    draggable="true"
                    @click="进入文件夹(folder.id)"
                    @contextmenu="显示文件夹右键菜单(folder, $event)"
                    @dragstart="开始拖拽文件夹(folder, $event)"
                    @dragend="结束拖拽资源"
                    @dragover.prevent
                    @drop="处理拖放到目录(folder.id, $event)"
                  >
                    <div class="resource-selector" @click.stop>
                      <ElCheckbox
                        :model-value="是否选中文件夹(folder.id)"
                        @change="(checked) => 设置文件夹选中(folder.id, Boolean(checked))"
                      />
                    </div>

                    <div class="folder-card__icon">
                      <ElIcon><Folder /></ElIcon>
                    </div>

                    <div class="folder-card__body">
                      <div class="folder-card__title-row">
                        <strong class="folder-card__title">{{ folder.name }}</strong>
                        <ElText type="info" class="folder-card__time">{{ 格式化时间(folder.updated_at) }}</ElText>
                      </div>
                      <ElText type="info">点击可进入目录，也可直接拖放资源到这里</ElText>
                    </div>

                    <ElSpace size="small" class="folder-card__actions">
                      <ElButton text @click.stop="进入文件夹(folder.id)">打开</ElButton>
                      <ElButton text @click.stop="打包下载资源({ type: 'folder', id: folder.id })">下载</ElButton>
                      <ElButton text @click.stop="重命名文件夹(folder)">
                        <ElIcon><EditPen /></ElIcon>
                      </ElButton>
                      <ElButton text @click.stop="打开移动对话框({ type: 'folder', id: folder.id })">
                        <ElIcon><Link /></ElIcon>
                      </ElButton>
                      <ElPopconfirm @confirm="删除文件夹(folder)">
                        <template #reference>
                          <ElButton text type="danger" @click.stop>
                            <ElIcon><Delete /></ElIcon>
                          </ElButton>
                        </template>
                        确定删除此文件夹？仅空文件夹可删除。
                      </ElPopconfirm>
                    </ElSpace>
                  </div>
                </div>
              </section>

              <section class="resource-section">
                <div class="resource-section__header">
                  <div>
                    <h4 class="resource-section__title">文件</h4>
                    <p class="resource-section__desc">图片会显示缩略图，支持重命名、批量移动和右键快捷操作</p>
                  </div>
                  <ElTag effect="plain">{{ 文件列表.length }} 个</ElTag>
                </div>

                <div v-if="文件列表.length === 0" class="empty-state empty-state--inner">
                  <ElEmpty description="当前目录下暂无文件" />
                </div>

                <div v-else class="file-list">
                  <div
                    v-for="file in 文件列表"
                    :key="file.id"
                    class="file-row"
                    :class="{ 'is-selected': 是否选中文件(file.id) }"
                    draggable="true"
                    @contextmenu="显示文件右键菜单(file, $event)"
                    @dragstart="开始拖拽文件(file, $event)"
                    @dragend="结束拖拽资源"
                  >
                    <div class="resource-selector" @click.stop>
                      <ElCheckbox
                        :model-value="是否选中文件(file.id)"
                        @change="(checked) => 设置文件选中(file.id, Boolean(checked))"
                      />
                    </div>

                    <div v-if="是否图片(file)" class="file-row__preview">
                      <img :src="file.url" :alt="file.original_name" @click.stop="打开图片预览(file)">
                    </div>
                    <div v-else class="file-row__icon">
                      <ElIcon><component :is="获取文件图标(file)" /></ElIcon>
                    </div>

                    <div class="file-row__body">
                      <button type="button" class="file-row__name" @click="打开文件(file.url)">
                        {{ file.original_name }}
                      </button>
                      <div class="file-row__meta">
                        <ElTag size="small" effect="plain">{{ 获取文件标签(file) }}</ElTag>
                        <span>{{ 格式化大小(file.size) }}</span>
                        <span>{{ file.mime_type }}</span>
                        <span>{{ 格式化时间(file.created_at) }}</span>
                      </div>
                    </div>

                    <ElSpace size="small" wrap class="file-row__actions">
                      <ElButton size="small" @click="打开文件(file.url)">打开</ElButton>
                      <ElButton size="small" @click="打包下载资源({ type: 'file', id: file.id })">打包下载</ElButton>
                      <ElButton size="small" @click="重命名文件(file)">重命名</ElButton>
                      <ElButton size="small" @click="打开移动对话框({ type: 'file', id: file.id })">移动到</ElButton>
                      <ElButton size="small" @click="复制链接(file.url)">复制链接</ElButton>
                      <ElPopconfirm @confirm="删除文件(file.id)">
                        <template #reference>
                          <ElButton size="small" type="danger" text>删除</ElButton>
                        </template>
                        确定删除此文件？
                      </ElPopconfirm>
                    </ElSpace>
                  </div>
                </div>
              </section>
            </template>
          </ElCard>
        </section>
      </div>
    </ElSkeleton>

    <ElDialog v-model="移动对话框可见" title="移动资源" width="420px">
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
    </ElDialog>

    <ElDialog v-model="批量重命名对话框可见" title="批量重命名" width="460px">
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
    </ElDialog>

    <ElDialog
      v-model="图片预览对话框可见"
      title="图片预览"
      width="min(980px, 94vw)"
      top="4vh"
      class="image-preview-dialog"
    >
      <template v-if="当前预览图片">
        <div class="image-preview">
          <img :src="当前预览图片.url" :alt="当前预览图片.original_name">
        </div>
        <div class="image-preview__footer">
          <div class="image-preview__meta">
            <strong>{{ 当前预览图片.original_name }}</strong>
            <ElText type="info">
              {{ 当前预览图片索引 + 1 }} / {{ 图片文件列表.length }} · {{ 格式化大小(当前预览图片.size) }}
            </ElText>
          </div>
          <ElSpace wrap>
            <ElButton :disabled="当前预览图片索引 <= 0" @click="切换预览图片(-1)">上一张</ElButton>
            <ElButton :disabled="当前预览图片索引 >= 图片文件列表.length - 1" @click="切换预览图片(1)">下一张</ElButton>
            <ElButton @click="打开文件(当前预览图片.url)">新窗口打开</ElButton>
            <ElButton @click="复制链接(当前预览图片.url)">复制链接</ElButton>
          </ElSpace>
        </div>
      </template>
    </ElDialog>

    <div
      v-if="右键菜单.visible"
      class="context-menu"
      :style="{ left: `${右键菜单.x}px`, top: `${右键菜单.y}px` }"
      @click.stop
    >
      <template v-if="右键菜单.scope === 'blank'">
        <button type="button" class="context-menu__item" @click="新建文件夹">新建文件夹</button>
        <button type="button" class="context-menu__item" @click="触发文件上传">上传文件</button>
        <button type="button" class="context-menu__item" @click="触发目录上传">上传目录</button>
        <button
          v-if="已选资源总数 > 0"
          type="button"
          class="context-menu__item"
          @click="打包下载资源()"
        >
          下载已选资源
        </button>
        <button
          v-if="已选资源总数 > 0"
          type="button"
          class="context-menu__item"
          @click="打开移动对话框()"
        >
          移动已选资源
        </button>
        <button
          v-if="已选资源总数 > 0 && !是否全局搜索模式"
          type="button"
          class="context-menu__item"
          @click="打开批量重命名对话框"
        >
          批量重命名
        </button>
        <button
          v-if="已选资源总数 > 0"
          type="button"
          class="context-menu__item is-danger"
          @click="批量删除资源()"
        >
          删除已选资源
        </button>
      </template>

      <template v-else-if="右键菜单.scope === 'folder' && 右键菜单文件夹">
        <button type="button" class="context-menu__item" @click="进入文件夹(右键菜单文件夹.id)">打开文件夹</button>
        <button type="button" class="context-menu__item" @click="打包下载资源({ type: 'folder', id: 右键菜单文件夹.id })">打包下载</button>
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
        <button type="button" class="context-menu__item is-danger" @click="批量删除资源({ type: 'folder', id: 右键菜单文件夹.id })">
          删除
        </button>
      </template>

      <template v-else-if="右键菜单.scope === 'file' && 右键菜单文件">
        <button
          v-if="是否图片(右键菜单文件)"
          type="button"
          class="context-menu__item"
          @click="打开图片预览(右键菜单文件)"
        >
          预览图片
        </button>
        <button type="button" class="context-menu__item" @click="打开文件(右键菜单文件.url)">打开文件</button>
        <button
          v-if="是否全局搜索模式"
          type="button"
          class="context-menu__item"
          @click="进入文件夹(右键菜单文件.folder_id)"
        >
          打开所在目录
        </button>
        <button type="button" class="context-menu__item" @click="打包下载资源({ type: 'file', id: 右键菜单文件.id })">打包下载</button>
        <button type="button" class="context-menu__item" @click="重命名文件(右键菜单文件)">重命名</button>
        <button
          type="button"
          class="context-menu__item"
          @click="打开移动对话框({ type: 'file', id: 右键菜单文件.id })"
        >
          移动到
        </button>
        <button type="button" class="context-menu__item" @click="复制链接(右键菜单文件.url)">复制链接</button>
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
  overflow-y: auto;
  padding: 24px;
  box-sizing: border-box;
}

.hidden-input {
  display: none;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 24px;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
}

.page-subtitle {
  margin: 8px 0 0;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.page-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.explorer-layout {
  display: grid;
  grid-template-columns: minmax(240px, 280px) minmax(0, 1fr);
  gap: 20px;
  align-items: start;
}

.explorer-sidebar,
.explorer-main {
  min-width: 0;
}

.sidebar-card,
.explorer-card {
  border-radius: 18px;
}

.sidebar-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.sidebar-card__title,
.explorer-title,
.resource-section__title {
  margin: 0;
}

.sidebar-card__desc,
.explorer-description,
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

.tree-node__icon {
  color: #18a058;
}

.tree-node__label {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.explorer-toolbar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.explorer-toolbar__main {
  min-width: 0;
}

.breadcrumb-button,
.file-row__name {
  padding: 0;
  border: none;
  background: transparent;
  color: inherit;
  font: inherit;
  text-align: left;
  cursor: pointer;
}

.breadcrumb-button:hover,
.file-row__name:hover {
  color: var(--el-color-primary);
}

.explorer-title {
  margin-top: 12px;
  font-size: 24px;
}

.explorer-tip {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 16px;
  padding: 12px 14px;
  border-radius: 14px;
  background: rgba(24, 160, 88, 0.08);
  color: #1c7d46;
  font-size: 13px;
}

.filter-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 16px;
  flex-wrap: wrap;
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

.filter-toolbar__count {
  font-size: 13px;
}

.selection-toolbar {
  margin-top: 16px;
  padding: 12px 14px;
  border: 1px solid var(--el-border-color);
  border-radius: 14px;
  background: var(--el-fill-color-lighter);
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

.folder-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 14px;
}

.folder-card,
.file-row {
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

.folder-card {
  cursor: pointer;
}

.folder-card:hover,
.file-row:hover {
  border-color: rgba(24, 160, 88, 0.35);
  transform: translateY(-1px);
  box-shadow: 0 14px 28px rgba(15, 23, 42, 0.08);
}

.folder-card.is-selected,
.file-row.is-selected {
  border-color: rgba(24, 160, 88, 0.45);
  background: rgba(24, 160, 88, 0.06);
}

.resource-selector {
  display: flex;
  align-items: center;
  align-self: flex-start;
  flex-shrink: 0;
}

.folder-card__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 46px;
  height: 46px;
  border-radius: 14px;
  background: rgba(24, 160, 88, 0.12);
  color: #18a058;
  font-size: 22px;
  flex-shrink: 0;
}

.folder-card__body {
  min-width: 0;
  flex: 1;
}

.folder-card__title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 6px;
}

.folder-card__title {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.folder-card__time {
  flex-shrink: 0;
  font-size: 12px;
}

.folder-card__actions {
  flex-shrink: 0;
}

.resource-path,
.file-row__path {
  margin-top: 8px;
  color: var(--el-text-color-secondary);
  font-size: 13px;
  line-height: 1.5;
  word-break: break-all;
}

.file-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.file-row__preview,
.file-row__icon {
  width: 72px;
  height: 72px;
  border-radius: 16px;
  overflow: hidden;
  flex-shrink: 0;
  background: var(--el-fill-color-light);
}

.file-row__preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  cursor: zoom-in;
}

.file-row__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--el-color-primary);
  font-size: 28px;
}

.file-row__body {
  min-width: 0;
  flex: 1;
}

.file-row__name {
  display: inline-block;
  max-width: 100%;
  font-size: 15px;
  font-weight: 600;
}

.file-row__meta {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 8px;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.file-row__actions {
  flex-shrink: 0;
  justify-content: flex-end;
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
  }
}

@media (max-width: 768px) {
  .page-container {
    padding: 16px;
  }

  .page-header {
    flex-direction: column;
    align-items: stretch;
  }

  .page-actions {
    justify-content: flex-start;
  }

  .folder-card,
  .file-row {
    flex-direction: column;
    align-items: stretch;
  }

  .resource-selector {
    align-self: flex-start;
  }

  .folder-card__actions,
  .file-row__actions {
    width: 100%;
    justify-content: flex-start;
  }

  .folder-card__title-row {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
