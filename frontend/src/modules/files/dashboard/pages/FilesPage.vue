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
  ElOption,
  ElSelect,
  ElSkeleton,
  ElSpace,
  ElText,
  ElTree,
} from 'element-plus'
import {
  Folder,
  FolderOpened,
  Loading,
  Picture,
  Search,
} from '@element-plus/icons-vue'
import BaseDialog from '../../../../components/BaseDialog.vue'
import FilesResourceRow from '../components/FilesResourceRow.vue'
import type {
  FileBreadcrumbItem,
  FileExplorerData,
  FileFolderItem,
  FileItem,
  FileSearchData,
  FileSearchFileItem,
  FileSearchFolderItem,
} from '../../types'
import {
  从目录树节点构建文件夹,
  分隔线宽度,
  右侧新建文件夹临时资源键,
  获取资源时间,
  排序文件列表,
  排序文件夹列表,
  排序资源列表,
  排序选项,
  搜索范围选项,
  新建目录临时节点键,
  插入新建目录节点,
  是否匹配搜索关键词,
  最大目录树宽度,
  最小主区域宽度,
  最小目录树宽度,
  文章图片标签,
  文章图片节点键,
  根目录名称,
  根目录节点键,
  收集目录树节点,
  桌面端初始渲染资源数量,
  桌面端增量渲染资源数量,
  移动端初始渲染资源数量,
  移动端增量渲染资源数量,
} from '../../explorer/files-explorer.shared'
import type {
  右侧新建文件夹草稿,
  右键菜单状态,
  目录树节点,
  列表重命名草稿,
  拉取资源选项,
  排序方式,
  搜索范围,
  新建目录草稿,
  文件夹展示项,
  文件展示项,
  资源展示项,
  资源标识,
  重命名目录草稿,
} from '../../explorer/files-explorer.shared'
import {
  解析链接,
  获取可预览文件链接,
  获取图片缩略图链接,
  获取原始文件路径,
  格式化大小,
  格式化时间,
  是否文章图片,
  是否普通文件,
  是否可移动文件,
  是否图片,
  是否视频,
  是否可预览媒体,
  获取文件图标,
  是否文件夹资源,
  是否文件资源,
  获取资源附加说明,
  获取资源路径,
  获取资源主标签,
  获取资源用途标签,
  是否可拖拽资源,
} from '../../explorer/files-explorer.resource'
import {
  创建关闭右键菜单状态,
} from '../../explorer/files-explorer.context-menu'
import {
  执行批量删除资源,
  执行批量移动资源,
  执行批量重命名资源,
  执行文件夹创建,
  执行文件夹删除,
  执行资源移动,
  执行资源重命名,
} from '../../explorer/files-explorer.actions'
import {
  创建列表文件夹重命名草稿,
  创建列表文件重命名草稿,
  创建新建目录草稿,
  创建右侧新建文件夹草稿,
  创建重命名目录草稿,
  是否资源处于右侧编辑态 as 是否资源处于右侧编辑态工具,
  是否资源是右侧新建文件夹草稿 as 是否资源是右侧新建文件夹草稿工具,
  是否资源正在右侧重命名 as 是否资源正在右侧重命名工具,
} from '../../explorer/files-explorer.editing'
import {
  保存文件夹创建草稿,
  保存资源重命名草稿,
  尝试聚焦现有编辑输入框,
} from '../../explorer/files-explorer.editing-actions'
import {
  处理编辑输入框失焦,
  处理编辑输入框键盘事件,
  提取输入框元素,
  聚焦输入框,
  聚焦资源行输入框,
} from '../../explorer/files-explorer.input'
import {
  执行文件上传 as 执行文件上传动作,
  执行目录上传 as 执行目录上传动作,
} from '../../explorer/files-explorer.upload'
import {
  执行上传流程,
  触发上传选择,
  读取并清空上传文件,
} from '../../explorer/files-explorer.upload-actions'
import {
  是否资源已选中 as 是否集合已选中,
  切换当前页资源全选,
  更新选中集合,
  读取当前已选资源 as 读取当前已选资源工具,
  获取操作资源列表 as 获取操作资源列表工具,
  构建批量文件名 as 构建批量文件名工具,
  获取批量重命名资源列表 as 获取批量重命名资源列表工具,
} from '../../explorer/files-explorer.selection'
import {
  创建媒体预览状态,
  执行资源下载,
  计算切换后的预览媒体ID,
} from '../../explorer/files-explorer.preview'
import {
  刷新当前视图数据,
  执行全局搜索 as 执行全局搜索动作,
  应用资源数据 as 应用资源数据动作,
  拉取资源数据,
  重置全局搜索结果 as 重置全局搜索结果动作,
} from '../../explorer/files-explorer.data-actions'
import {
  获取关闭右键菜单后的状态,
  处理目录树文件夹右键菜单触发,
  处理空白右键菜单触发,
  处理资源行右键菜单触发,
} from '../../explorer/files-explorer.context-menu-actions'
import {
  打开批量重命名对话框编排,
  打开移动对话框编排,
  执行批量删除编排,
  执行批量移动编排,
  执行批量重命名编排,
} from '../../explorer/files-explorer.batch-actions'
import {
  执行文件夹删除确认编排,
} from '../../explorer/files-explorer.folder-actions'
import {
  写入拖拽资源 as 写入拖拽资源工具,
  处理拖放到目录 as 处理拖放到目录工具,
  是否可拖拽目录树节点 as 是否可拖拽目录树节点工具,
} from '../../explorer/files-explorer.drag'

addCollection(codiconIcons)

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
const 资源列表底部哨兵 = ref<globalThis.HTMLDivElement | null>(null)
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
const 当前渲染资源数量 = ref(桌面端初始渲染资源数量)
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
  ...创建关闭右键菜单状态(),
})
let 全局搜索定时器: number | null = null
let 全局搜索序号 = 0
let 资源列表观察器: globalThis.IntersectionObserver | null = null
const 路由 = useRouter()

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

const 子文件夹列表 = computed<FileFolderItem[]>(() => (
  当前是文章图片视图.value
    ? []
    : 排序文件夹列表(
      原始子文件夹列表.value.filter((folder) => 是否匹配搜索关键词(folder.name, 搜索关键词.value)),
      当前排序.value,
    )
))
const 文件列表 = computed<FileItem[]>(() => 排序文件列表(
  原始文件列表.value.filter((file) => 是否匹配搜索关键词(file.original_name, 搜索关键词.value)),
  当前排序.value,
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
  const list = 排序资源列表(当前展示文件夹列表.value, 当前展示文件列表.value, 当前排序.value)
  return 右侧新建文件夹资源.value ? [右侧新建文件夹资源.value, ...list] : list
})
const 当前渲染资源列表 = computed<资源展示项[]>(() => 当前展示资源列表.value.slice(0, 当前渲染资源数量.value))
const 当前目录文件夹总数 = computed(() => (当前是文章图片视图.value ? 0 : 原始子文件夹列表.value.length))
const 当前目录文件总数 = computed(() => 原始文件列表.value.length)
const 当前页资源总数 = computed(() => 当前展示资源列表.value.length)
const 当前已渲染资源总数 = computed(() => 当前渲染资源列表.value.length)
const 是否还有更多资源待渲染 = computed(() => 当前已渲染资源总数.value < 当前页资源总数.value)
const 剩余待渲染资源数 = computed(() => Math.max(0, 当前页资源总数.value - 当前已渲染资源总数.value))
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

function 获取初始渲染资源数量() {
  if (typeof window !== 'undefined' && window.innerWidth <= 768) {
    return 移动端初始渲染资源数量
  }
  return 桌面端初始渲染资源数量
}

function 获取增量渲染资源数量() {
  if (typeof window !== 'undefined' && window.innerWidth <= 768) {
    return 移动端增量渲染资源数量
  }
  return 桌面端增量渲染资源数量
}

function 重置资源列表渲染进度() {
  当前渲染资源数量.value = 获取初始渲染资源数量()
}

function 加载更多资源() {
  if (!是否还有更多资源待渲染.value) {
    return
  }
  当前渲染资源数量.value = Math.min(
    当前页资源总数.value,
    当前渲染资源数量.value + 获取增量渲染资源数量(),
  )
}

function 销毁资源列表观察器() {
  资源列表观察器?.disconnect()
  资源列表观察器 = null
}

function 更新资源列表观察器() {
  销毁资源列表观察器()
  if (!是否还有更多资源待渲染.value || !资源列表底部哨兵.value || typeof window.IntersectionObserver === 'undefined') {
    return
  }

  资源列表观察器 = new window.IntersectionObserver((entries) => {
    if (entries.some((entry) => entry.isIntersecting)) {
      加载更多资源()
    }
  }, {
    root: null,
    rootMargin: '240px 0px',
    threshold: 0,
  })
  资源列表观察器.observe(资源列表底部哨兵.value)
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
  销毁资源列表观察器()
})

function 清空选择() {
  已选文件夹.value = new Set()
  已选文件.value = new Set()
}

function 应用资源数据(data: FileExplorerData) {
  应用资源数据动作({
    data,
    设置资源数据: (nextData) => {
      资源数据.value = nextData
    },
    设置当前目录ID: (folderId) => {
      当前目录ID.value = folderId
    },
    清空选择,
  })
}

async function 拉取资源(folderId: string | null = 当前目录ID.value, options: 拉取资源选项 = {}) {
  await 拉取资源数据({
    folderId,
    静默: options.静默 ?? false,
    应用资源数据,
    设置刷新中: (value) => {
      刷新中.value = value
    },
    设置首次加载中: (value) => {
      首次加载中.value = value
    },
  })
}

function 重置全局搜索结果() {
  重置全局搜索结果动作({
    设置全局搜索中: (value) => {
      全局搜索中.value = value
    },
    设置全局搜索结果: (data) => {
      全局搜索结果.value = data
    },
  })
}

async function 执行全局搜索(keyword: string, requestId: number) {
  await 执行全局搜索动作({
    keyword,
    requestId,
    获取当前请求序号: () => 全局搜索序号,
    设置全局搜索中: (value) => {
      全局搜索中.value = value
    },
    设置全局搜索结果: (data) => {
      全局搜索结果.value = data
    },
  })
}

async function 刷新当前视图(folderId: string | null = 当前目录ID.value) {
  await 刷新当前视图数据({
    folderId,
    是否全局搜索模式: 是否全局搜索模式.value,
    keyword: 搜索关键词.value,
    拉取资源,
    重置全局搜索结果,
    设置全局搜索中: (value) => {
      全局搜索中.value = value
    },
    创建全局搜索请求: () => {
      全局搜索序号 += 1
      return 全局搜索序号
    },
    执行全局搜索,
  })
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

watch(
  [
    () => 当前展示资源列表.value,
    当前排序,
  ],
  async () => {
    重置资源列表渲染进度()
    await nextTick()
    更新资源列表观察器()
  },
  { immediate: true },
)

watch(
  [当前渲染资源数量, 资源列表底部哨兵],
  async () => {
    await nextTick()
    更新资源列表观察器()
  },
)

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
  const nextMenu = 处理目录树文件夹右键菜单触发(data, event, 重命名目录草稿状态.value?.id ?? null)
  if (!nextMenu) {
    return
  }
  右键菜单.value = nextMenu
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

function 触发文件上传() {
  关闭右键菜单()
  触发上传选择(文件上传输入框.value)
}

function 触发目录上传() {
  关闭右键菜单()
  触发上传选择(目录上传输入框.value)
}

async function 处理文件选择(event: globalThis.Event) {
  const files = 读取并清空上传文件(event)
  await 执行上传流程({
    files,
    关闭右键菜单,
    设置正在上传: (value) => {
      正在上传.value = value
    },
    执行上传: (selectedFiles) => 执行文件上传动作(selectedFiles, 当前目录ID.value),
    获取成功提示: (successCount) => `已上传 ${successCount} 个文件`,
    获取失败提示: (failedCount) => `有 ${failedCount} 个文件上传失败`,
    刷新当前视图,
  })
}

async function 处理目录选择(event: globalThis.Event) {
  const files = 读取并清空上传文件(event)
  await 执行上传流程({
    files,
    关闭右键菜单,
    设置正在上传: (value) => {
      正在上传.value = value
    },
    执行上传: (selectedFiles) => 执行目录上传动作(selectedFiles, 当前目录ID.value, 资源数据.value?.tree ?? []),
    获取成功提示: (successCount) => `目录上传完成，共处理 ${successCount} 个文件`,
    获取失败提示: (failedCount) => `有 ${failedCount} 个文件上传失败`,
    刷新当前视图,
  })
}

async function 新建文件夹() {
  关闭右键菜单()
  if (await 尝试聚焦现有编辑输入框({
    当前目录ID: 当前目录ID.value,
    当前可在右侧新建文件夹: 当前可在右侧新建文件夹.value,
    当前展示资源列表: 当前展示资源列表.value,
    右侧新建文件夹草稿: 右侧新建文件夹草稿状态.value,
    新建目录草稿: 新建目录草稿状态.value,
    重命名目录草稿: 重命名目录草稿状态.value,
    列表重命名草稿: 列表重命名草稿状态.value,
    聚焦右侧新建文件夹输入框,
    聚焦新建目录输入框,
    聚焦重命名目录输入框,
    聚焦列表重命名输入框,
    取消右侧新建文件夹,
    取消列表重命名,
  })) {
    return
  }

  const parentId = 当前是文章图片视图.value ? null : 当前目录ID.value
  新建目录草稿状态.value = 创建新建目录草稿(新建目录临时节点键, parentId)

  if (parentId) {
    await nextTick()
    目录树引用.value?.getNode(parentId)?.expand()
  }

  await 聚焦新建目录输入框()
}

async function 聚焦新建目录输入框() {
  await 聚焦输入框(新建目录输入框.value)
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
  if (await 尝试聚焦现有编辑输入框({
    当前目录ID: 当前目录ID.value,
    当前可在右侧新建文件夹: 当前可在右侧新建文件夹.value,
    当前展示资源列表: 当前展示资源列表.value,
    右侧新建文件夹草稿: 右侧新建文件夹草稿状态.value,
    新建目录草稿: 新建目录草稿状态.value,
    重命名目录草稿: 重命名目录草稿状态.value,
    列表重命名草稿: 列表重命名草稿状态.value,
    聚焦右侧新建文件夹输入框,
    聚焦新建目录输入框,
    聚焦重命名目录输入框,
    聚焦列表重命名输入框,
    取消右侧新建文件夹,
    取消列表重命名,
  })) {
    return
  }

  右侧新建文件夹草稿状态.value = 创建右侧新建文件夹草稿(
    右侧新建文件夹临时资源键,
    当前目录ID.value,
  )

  await 聚焦右侧新建文件夹输入框()
}

async function 聚焦右侧新建文件夹输入框() {
  await 聚焦资源行输入框(右侧新建文件夹输入框.value)
}

function 取消右侧新建文件夹() {
  右侧新建文件夹草稿状态.value = null
  正在提交右侧新建文件夹.value = false
}

async function 聚焦重命名目录输入框() {
  await 聚焦输入框(重命名目录输入框.value)
}

function 取消重命名目录() {
  重命名目录草稿状态.value = null
  正在提交重命名目录.value = false
}

async function 聚焦列表重命名输入框() {
  await 聚焦资源行输入框(列表重命名输入框.value)
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
  await 保存文件夹创建草稿({
    草稿: 右侧新建文件夹草稿状态.value,
    正在提交: 正在提交右侧新建文件夹.value,
    设置正在提交: (value) => {
      正在提交右侧新建文件夹.value = value
    },
    取消编辑: 取消右侧新建文件夹,
    清空草稿: () => {
      右侧新建文件夹草稿状态.value = null
    },
    创建文件夹: 执行文件夹创建,
    刷新当前视图,
    重新聚焦输入框: 聚焦右侧新建文件夹输入框,
  })
}

async function 保存新建文件夹() {
  await 保存文件夹创建草稿({
    草稿: 新建目录草稿状态.value,
    正在提交: 正在提交新建目录.value,
    设置正在提交: (value) => {
      正在提交新建目录.value = value
    },
    取消编辑: 取消新建文件夹,
    清空草稿: () => {
      新建目录草稿状态.value = null
    },
    创建文件夹: 执行文件夹创建,
    刷新当前视图,
    重新聚焦输入框: 聚焦新建目录输入框,
  })
}

async function 处理新建目录输入框失焦() {
  await 处理编辑输入框失焦(正在提交新建目录.value, 保存新建文件夹)
}

async function 处理右侧新建文件夹输入框失焦() {
  await 处理编辑输入框失焦(正在提交右侧新建文件夹.value, 保存右侧新建文件夹)
}

function 处理新建目录键盘事件(event: globalThis.KeyboardEvent) {
  处理编辑输入框键盘事件(event, () => {
    void 保存新建文件夹()
  }, 取消新建文件夹)
}

function 处理右侧新建文件夹键盘事件(event: globalThis.KeyboardEvent) {
  处理编辑输入框键盘事件(event, () => {
    void 保存右侧新建文件夹()
  }, 取消右侧新建文件夹)
}

async function 重命名文件夹(folder: 文件夹展示项) {
  const menuSource = 右键菜单.value.source
  关闭右键菜单()
  if (await 尝试聚焦现有编辑输入框({
    当前目录ID: 当前目录ID.value,
    当前可在右侧新建文件夹: 当前可在右侧新建文件夹.value,
    当前展示资源列表: 当前展示资源列表.value,
    右侧新建文件夹草稿: 右侧新建文件夹草稿状态.value,
    新建目录草稿: 新建目录草稿状态.value,
    重命名目录草稿: 重命名目录草稿状态.value,
    列表重命名草稿: 列表重命名草稿状态.value,
    聚焦右侧新建文件夹输入框,
    聚焦新建目录输入框,
    聚焦重命名目录输入框,
    聚焦列表重命名输入框,
    取消右侧新建文件夹,
    取消列表重命名,
  })) {
    return
  }
  if (menuSource === 'tree') {
    重命名目录草稿状态.value = 创建重命名目录草稿(folder)
    await 聚焦重命名目录输入框()
    return
  }
  列表重命名草稿状态.value = 创建列表文件夹重命名草稿(folder)
  await 聚焦列表重命名输入框()
}

async function 保存重命名目录() {
  await 保存资源重命名草稿({
    草稿: 重命名目录草稿状态.value,
    正在提交: 正在提交重命名目录.value,
    设置正在提交: (value) => {
      正在提交重命名目录.value = value
    },
    取消编辑: 取消重命名目录,
    清空草稿: () => {
      重命名目录草稿状态.value = null
    },
    获取资源类型: () => 'folder',
    获取成功文案: () => '文件夹已重命名',
    获取失败文案: () => '重命名文件夹失败',
    重命名资源: 执行资源重命名,
    刷新当前视图,
    重新聚焦输入框: 聚焦重命名目录输入框,
  })
}

async function 处理重命名目录输入框失焦() {
  await 处理编辑输入框失焦(正在提交重命名目录.value, 保存重命名目录)
}

function 处理重命名目录键盘事件(event: globalThis.KeyboardEvent) {
  处理编辑输入框键盘事件(event, () => {
    void 保存重命名目录()
  }, 取消重命名目录)
}

function 是否资源正在右侧重命名(resource: 资源展示项) {
  return 是否资源正在右侧重命名工具(resource, 列表重命名草稿状态.value)
}

function 是否资源是右侧新建文件夹草稿(resource: 资源展示项) {
  return 是否资源是右侧新建文件夹草稿工具(resource, 右侧新建文件夹草稿状态.value)
}

function 是否资源处于右侧编辑态(resource: 资源展示项) {
  return 是否资源处于右侧编辑态工具(
    resource,
    右侧新建文件夹草稿状态.value,
    列表重命名草稿状态.value,
  )
}

async function 保存右侧重命名() {
  await 保存资源重命名草稿({
    草稿: 列表重命名草稿状态.value,
    正在提交: 正在提交列表重命名.value,
    设置正在提交: (value) => {
      正在提交列表重命名.value = value
    },
    取消编辑: 取消列表重命名,
    清空草稿: () => {
      列表重命名草稿状态.value = null
    },
    获取资源类型: (draft) => draft.type,
    获取成功文案: (draft) => (draft.type === 'folder' ? '文件夹已重命名' : '文件已重命名'),
    获取失败文案: (draft) => (draft.type === 'folder' ? '重命名文件夹失败' : '重命名文件失败'),
    重命名资源: 执行资源重命名,
    刷新当前视图,
    重新聚焦输入框: 聚焦列表重命名输入框,
  })
}

async function 处理右侧重命名输入框失焦() {
  await 处理编辑输入框失焦(正在提交列表重命名.value, 保存右侧重命名)
}

function 处理右侧重命名键盘事件(event: globalThis.KeyboardEvent) {
  处理编辑输入框键盘事件(event, () => {
    void 保存右侧重命名()
  }, 取消列表重命名)
}

async function 重命名文件(file: 文件展示项) {
  关闭右键菜单()
  if (await 尝试聚焦现有编辑输入框({
    当前目录ID: 当前目录ID.value,
    当前可在右侧新建文件夹: 当前可在右侧新建文件夹.value,
    当前展示资源列表: 当前展示资源列表.value,
    右侧新建文件夹草稿: 右侧新建文件夹草稿状态.value,
    新建目录草稿: 新建目录草稿状态.value,
    重命名目录草稿: 重命名目录草稿状态.value,
    列表重命名草稿: 列表重命名草稿状态.value,
    聚焦右侧新建文件夹输入框,
    聚焦新建目录输入框,
    聚焦重命名目录输入框,
    聚焦列表重命名输入框,
    取消右侧新建文件夹,
    取消列表重命名,
  })) {
    return
  }
  列表重命名草稿状态.value = 创建列表文件重命名草稿(file)
  await 聚焦列表重命名输入框()
}

async function 确认删除文件夹(folder: 文件夹展示项) {
  await 执行文件夹删除确认编排({
    folder,
    当前目录ID: 当前目录.value?.id ?? null,
    关闭右键菜单,
    执行文件夹删除,
    进入文件夹,
    刷新当前视图,
    是否消息框取消,
  })
}

function 是否选中文件夹(id: string) {
  return 是否集合已选中(已选文件夹.value, id)
}

function 是否选中文件(id: string) {
  return 是否集合已选中(已选文件.value, id)
}

function 设置文件夹选中(id: string, selected: boolean) {
  已选文件夹.value = 更新选中集合(已选文件夹.value, id, selected)
}

function 设置文件选中(id: string, selected: boolean) {
  已选文件.value = 更新选中集合(已选文件.value, id, selected)
}

function 切换当前页全选() {
  const result = 切换当前页资源全选(
    已选文件夹.value,
    已选文件.value,
    当前展示文件夹列表.value,
    当前展示文件列表.value,
    是否已全选当前页.value,
  )
  已选文件夹.value = result.文件夹
  已选文件.value = result.文件
}

function 读取当前已选资源() {
  return 读取当前已选资源工具(已选文件夹.value, 已选文件.value)
}

function 获取操作资源列表(resource?: 资源标识) {
  const targetResources = 获取操作资源列表工具(resource, 读取当前已选资源())
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

  await 执行批量删除编排({
    targetResources,
    当前目录ID: 当前目录.value?.id ?? null,
    当前目录父级ID: 当前目录.value?.parent_id ?? null,
    关闭右键菜单,
    是否消息框取消,
    执行删除: 执行批量删除资源,
    进入文件夹,
    刷新当前视图,
  })
}

function 打开移动对话框(resource?: 资源标识) {
  const targetResources = 获取操作资源列表(resource)
  if (!targetResources) {
    return
  }

  打开移动对话框编排({
    targetResources,
    当前目录ID: 当前目录ID.value,
    不可移动资源数量: 获取不可移动资源数量(targetResources),
    关闭右键菜单,
    设置待移动资源列表: (resources) => {
      待移动资源列表.value = resources
    },
    设置移动目标目录ID: (folderId) => {
      移动目标目录ID.value = folderId
    },
    设置移动对话框可见: (visible) => {
      移动对话框可见.value = visible
    },
  })
}

function 打开批量重命名对话框() {
  打开批量重命名对话框编排({
    targetResources: 读取当前已选资源(),
    关闭右键菜单,
    设置批量重命名对话框可见: (visible) => {
      批量重命名对话框可见.value = visible
    },
  })
}

function 构建批量文件名(resource: 资源标识, offset: number) {
  return 构建批量文件名工具(resource, offset, 原始文件列表.value, {
    前缀: 批量重命名前缀.value,
    起始序号: 批量重命名起始序号.value,
    位数: 批量重命名位数.value,
    保留扩展名: 批量重命名保留扩展名.value,
  })
}

function 获取批量重命名资源列表() {
  return 获取批量重命名资源列表工具(
    原始子文件夹列表.value,
    原始文件列表.value,
    已选文件夹.value,
    已选文件.value,
    当前排序.value,
  )
}

async function 确认批量重命名() {
  await 执行批量重命名编排({
    targetResources: 获取批量重命名资源列表(),
    构建批量文件名,
    执行重命名: 执行批量重命名资源,
    设置批量重命名对话框可见: (visible) => {
      批量重命名对话框可见.value = visible
    },
    刷新当前视图,
  })
}

async function 确认移动资源() {
  await 执行批量移动编排({
    targetResources: 待移动资源列表.value,
    移动目标目录ID: 移动目标目录ID.value,
    不可移动资源数量: 获取不可移动资源数量(待移动资源列表.value),
    执行移动: 执行批量移动资源,
    设置移动对话框可见: (visible) => {
      移动对话框可见.value = visible
    },
    设置待移动资源列表: (resources) => {
      待移动资源列表.value = resources
    },
    刷新当前视图,
  })
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

async function 下载资源(resource?: 资源标识) {
  const targetResources = 获取操作资源列表(resource)
  if (!targetResources) {
    return
  }

  关闭右键菜单()
  await 执行资源下载({
    资源列表: targetResources,
    当前目录名称: 当前目录名称.value,
    是否全局搜索模式: 是否全局搜索模式.value,
    查找文件夹展示项,
    查找文件展示项,
  })
}

function 打开媒体预览(file: 文件展示项) {
  关闭右键菜单()
  const previewState = 创建媒体预览状态(file)
  当前预览媒体ID.value = previewState.当前预览媒体ID
  媒体预览对话框可见.value = previewState.媒体预览对话框可见
}

function 切换预览媒体(step: number) {
  const nextPreviewMediaId = 计算切换后的预览媒体ID(
    当前预览媒体索引.value,
    step,
    可预览媒体文件列表.value,
  )
  if (!nextPreviewMediaId) {
    return
  }
  当前预览媒体ID.value = nextPreviewMediaId
}

function 开始拖拽文件夹(folder: 文件夹展示项, event: globalThis.DragEvent) {
  写入拖拽资源(event, {
    type: 'folder',
    id: folder.id,
  })
}

function 是否可拖拽目录树节点(node: 目录树节点) {
  return 是否可拖拽目录树节点工具(node, 重命名目录草稿状态.value?.id ?? null)
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
  写入拖拽资源工具(event, resource)
}

function 结束拖拽资源() {
  当前拖拽资源.value = null
}

async function 处理拖放到目录(targetFolderId: string | null, event: globalThis.DragEvent) {
  await 处理拖放到目录工具({
    event,
    targetFolderId,
    当前拖拽资源: 当前拖拽资源.value,
    清空当前拖拽资源: () => {
      当前拖拽资源.value = null
    },
    查找文件展示项,
    执行资源移动,
    刷新当前视图,
  })
}

function 打开文件(url: string) {
  关闭右键菜单()
  window.open(解析链接(url), '_blank', 'noopener,noreferrer')
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

function 开始拖拽资源(resource: 资源展示项, event: globalThis.DragEvent) {
  if (resource.type === 'folder') {
    开始拖拽文件夹(resource.item, event)
    return
  }
  开始拖拽文件(resource.item, event)
}

function 处理资源行右键菜单(resource: 资源展示项, event: globalThis.MouseEvent) {
  const nextMenu = 处理资源行右键菜单触发(
    resource,
    event,
    是否资源处于右侧编辑态(resource),
  )
  if (!nextMenu) {
    return
  }
  右键菜单.value = nextMenu
}

function 显示空白右键菜单(event: globalThis.MouseEvent) {
  const nextMenu = 处理空白右键菜单触发(event)
  if (!nextMenu) {
    return
  }
  右键菜单.value = nextMenu
}

function 关闭右键菜单() {
  右键菜单.value = 获取关闭右键菜单后的状态(右键菜单.value)
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
                      <FilesResourceRow
                        v-for="resource in 当前渲染资源列表"
                        :key="`${resource.type}-${resource.id}`"
                        :resource="resource"
                        :selected="是否资源已选中(resource)"
                        :is-folder="是否文件夹资源(resource)"
                        :is-editing="是否资源处于右侧编辑态(resource)"
                        :is-creating-draft="是否资源是右侧新建文件夹草稿(resource)"
                        :is-renaming="是否资源正在右侧重命名(resource)"
                        :can-drag="是否可拖拽资源(resource, 是否全局搜索模式)"
                        :allow-drop-on-folder="!是否全局搜索模式"
                        :is-image="是否文件资源(resource) && 是否图片(resource.item)"
                        :is-video="是否文件资源(resource) && 是否视频(resource.item)"
                        :thumbnail-url="是否文件资源(resource) ? 获取图片缩略图链接(resource.item) : ''"
                        :display-name="是否文件夹资源(resource) ? resource.item.name : resource.item.original_name"
                        :extra-description="获取资源附加说明(resource)"
                        :resource-path="获取资源路径(resource, 是否全局搜索模式)"
                        :primary-tag="获取资源主标签(resource)"
                        :purpose-tag="获取资源用途标签(resource)"
                        :file-size-text="是否文件资源(resource) ? 格式化大小(resource.item.size) : ''"
                        :file-mime-type="是否文件资源(resource) ? resource.item.mime_type : ''"
                        :time-text="格式化时间(获取资源时间(resource))"
                        :file-icon="是否文件资源(resource) ? 获取文件图标(resource.item) : undefined"
                        :creating-name="右侧新建文件夹名称"
                        :renaming-name="列表重命名名称"
                        :creating-disabled="正在提交右侧新建文件夹"
                        :renaming-disabled="正在提交列表重命名"
                        :set-creating-input-ref="设置右侧新建文件夹输入框引用"
                        :set-renaming-input-ref="设置列表重命名输入框引用"
                        @select-change="设置资源选中(resource, $event)"
                        @row-click="是否文件夹资源(resource) ? void 进入文件夹(resource.item.id) : null"
                        @contextmenu="处理资源行右键菜单(resource, $event)"
                        @dragstart="开始拖拽资源(resource, $event)"
                        @dragend="结束拖拽资源"
                        @drop-folder="是否文件夹资源(resource) ? 处理拖放到目录(resource.item.id, $event) : null"
                        @open-preview="是否文件资源(resource) ? 打开媒体预览(resource.item) : null"
                        @open-file="是否文件资源(resource) ? 打开文件(resource.item.url) : null"
                        @update:creating-name="右侧新建文件夹名称 = $event"
                        @update:renaming-name="列表重命名名称 = $event"
                        @creating-keydown="处理右侧新建文件夹键盘事件"
                        @creating-blur="处理右侧新建文件夹输入框失焦"
                        @renaming-keydown="处理右侧重命名键盘事件"
                        @renaming-blur="处理右侧重命名输入框失焦"
                      />

                      <div
                        v-if="是否还有更多资源待渲染"
                        ref="资源列表底部哨兵"
                        class="resource-list__load-more"
                      >
                        <ElButton @click="加载更多资源">
                          继续加载 {{ Math.min(获取增量渲染资源数量(), 剩余待渲染资源数) }} 项
                        </ElButton>
                        <span class="resource-list__load-more-text">
                          已渲染 {{ 当前已渲染资源总数 }} / {{ 当前页资源总数 }} 项
                        </span>
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
    rgb(var(--el-color-primary-rgb) / 0.18),
    rgb(var(--el-color-primary-rgb) / 0.5),
    rgb(var(--el-color-primary-rgb) / 0.18)
  );
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.explorer-resizer:hover::before,
.explorer-resizer.is-dragging::before {
  background: rgb(var(--el-color-primary-rgb) / 0.56);
  box-shadow: 0 0 0 1px rgb(var(--el-color-primary-rgb) / 0.12);
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
  outline: 2px solid rgb(var(--el-color-primary-rgb) / 0.28);
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
  color: var(--el-color-primary);
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
  border: 1px solid rgb(var(--el-color-primary-rgb) / 0.32);
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
  border-color: rgb(var(--el-color-primary-rgb) / 0.78);
  box-shadow: 0 0 0 1px rgb(var(--el-color-primary-rgb) / 0.16);
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

.breadcrumb-button {
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

.breadcrumb-button:hover {
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
  border: 1px solid rgb(var(--el-color-primary-rgb) / 0.22);
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

.resource-list__load-more {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 8px 0 4px;
  flex-wrap: wrap;
}

.resource-list__load-more-text {
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
  color: var(--el-color-primary);
}

.explorer-footer__divider {
  width: 1px;
  height: 10px;
  background: var(--el-border-color);
}

.dark .selection-toolbar {
  background: rgba(24, 24, 28, 0.92);
  border-color: rgb(var(--el-color-primary-rgb) / 0.32);
  box-shadow: 0 18px 48px rgba(0, 0, 0, 0.36);
}

.dark .sidebar-action-button:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
}

.dark .tree-node__input {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgb(var(--el-color-primary-rgb) / 0.34);
  color: #fff;
}

.dark .tree-node__input:focus {
  border-color: rgb(var(--el-color-primary-rgb) / 0.88);
  box-shadow: 0 0 0 1px rgb(var(--el-color-primary-rgb) / 0.22);
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
  border-color: rgb(var(--el-color-primary-rgb) / 0.45);
  background: rgb(var(--el-color-primary-rgb) / 0.08);
}

.image-preview {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
  border-radius: 16px;
  background:
    radial-gradient(circle at top, rgb(var(--el-color-primary-rgb) / 0.12), transparent 48%),
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
