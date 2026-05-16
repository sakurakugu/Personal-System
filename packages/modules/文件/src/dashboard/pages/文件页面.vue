<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from 'vue'
import { useRouter } from 'vue-router'
import type { TreeInstance } from 'element-plus'
import FilesBatchRenameDialog from '../components/文件批量重命名.vue'
import FilesBreadcrumbTrail from '../components/文件面包屑.vue'
import FilesContextMenu from '../components/文件右键菜单.vue'
import FilesExplorerFooter from '../components/文件浏览页脚.vue'
import FilesExplorerMainSection from '../components/文件浏览主区域.vue'
import FilesExplorerShell from '../components/文件浏览器外壳.vue'
import FilesMediaPreviewDialog from '../components/文件媒体预览.vue'
import FilesMoveDialog from '../components/文件移动弹窗.vue'
import FilesPageToolbar from '../components/文件页面工具栏.vue'
import FilesResourceListSection from '../components/文件资源列表.vue'
import FilesSelectionToolbar from '../components/文件选择工具栏.vue'
import FilesSidebarTree from '../components/文件侧边栏树.vue'
import FilesUploadInputs from '../components/文件上传输入.vue'
import type {
  FileBreadcrumbItem,
  FileFolderItem,
  FileItem,
  FileSearchFileItem,
  FileSearchFolderItem,
} from '../../types'
import {
  从目录树节点构建文件夹,
  排序文件列表,
  排序文件夹列表,
  排序资源列表,
  排序选项,
  搜索范围选项,
  插入新建目录节点,
  是否匹配搜索关键词,
  文章图片标签,
  文章图片节点键,
  动态图片标签,
  动态图片节点键,
  根目录名称,
  根目录节点键,
  收集目录树节点,
} from '../../core/shared'
import type {
  右键菜单状态,
  目录树节点,
  排序方式,
  搜索范围,
  文件夹展示项,
  文件展示项,
  资源展示项,
} from '../../core/shared'
import {
  关闭图片预览,
  打开图片预览,
} from '../../core/preview'
import {
  是否普通文件,
  是否图片,
  是否视频,
} from '../../core/resource'
import {
  创建关闭右键菜单状态,
} from '../../core/context-menu'
import {
  执行批量删除资源,
  执行批量移动资源,
  执行批量重命名资源,
  执行文件夹创建,
  执行文件夹删除,
  执行资源移动,
  执行资源重命名,
} from '../../core/actions'
import {
  获取关闭右键菜单后的状态,
} from '../../core/context-menu-actions'
import { useFilesPageActions } from '../composables/page-actions'
import { useFilesPageData } from '../composables/page-data'
import { useFilesPageDialogs } from '../composables/page-dialogs'
import { useFilesPageEditing } from '../composables/page-editing'
import { useFilesPageInteractions } from '../composables/page-interactions'
import { useFilesPageBridges } from '../composables/page-bridges'
import { useFilesPageNavigationUpload } from '../composables/page-navigation-upload'
import { useFilesPageSelection } from '../composables/page-selection'
import { useFilesPageViewport } from '../composables/page-viewport'

const 正在上传 = ref(false)
const 搜索关键词 = ref('')
const 搜索范围值 = ref<搜索范围>('current')
const 当前排序 = ref<排序方式>('name-asc')
const 文件上传输入框 = ref<globalThis.HTMLInputElement | null>(null)
const 目录上传输入框 = ref<globalThis.HTMLInputElement | null>(null)
const 目录树引用 = ref<TreeInstance | null>(null)
const 目录树引用透传 = { ref: 目录树引用 }
const 当前资源视图 = ref<'files' | 'article-images' | 'moment-images'>('files')
const 右键菜单 = ref<右键菜单状态>({
  ...创建关闭右键菜单状态(),
})
const 路由 = useRouter()

const 页面选择 = useFilesPageSelection({
  获取资源数据: () => 资源数据.value,
  获取当前目录: () => 当前目录.value,
  获取当前展示文件夹列表: () => 当前展示文件夹列表.value,
  获取当前展示文件列表: () => 当前展示文件列表.value,
  获取原始子文件夹列表: () => 原始子文件夹列表.value,
  获取原始文件列表: () => 原始文件列表.value,
  获取当前排序: () => 当前排序.value,
  从目录树节点构建文件夹,
  收集目录树节点,
  是否普通文件,
})
const {
  已选文件夹,
  已选文件,
  清空选择,
  是否选中文件夹,
  是否选中文件,
  设置文件夹选中,
  设置文件选中,
  切换当前页全选: 切换当前页全选动作,
  读取当前已选资源,
  查找文件夹展示项,
  查找文件展示项,
  是否资源支持移动,
  获取不可移动资源数量,
  是否资源已选中,
  设置资源选中,
} = 页面选择

const 是否全局搜索模式 = computed(() => 搜索范围值.value === 'global' && 搜索关键词.value.trim().length > 0)
const {
  资源数据,
  首次加载中,
  刷新中,
  全局搜索中,
  全局搜索结果,
  当前目录ID,
  拉取资源,
  刷新当前视图,
} = useFilesPageData({
  搜索关键词,
  搜索范围值,
  是否全局搜索模式,
  清空选择,
})

const 当前目录 = computed(() => 资源数据.value?.current_folder ?? null)
const 是否显示骨架屏 = computed(() => 首次加载中.value && 资源数据.value === null)
const 当前是文章图片视图 = computed(() => 当前资源视图.value === 'article-images')
const 当前是动态图片视图 = computed(() => 当前资源视图.value === 'moment-images')
const 当前是内容图片视图 = computed(() => 当前是文章图片视图.value || 当前是动态图片视图.value)
const 导航栏列表 = computed<FileBreadcrumbItem[]>(() => (
  当前是文章图片视图.value
    ? [{ id: 文章图片节点键, name: 文章图片标签 }]
    : (当前是动态图片视图.value
      ? [{ id: 动态图片节点键, name: 动态图片标签 }]
      : (资源数据.value?.breadcrumbs ?? [{ id: null, name: 根目录名称 }]))
))
const 原始子文件夹列表 = computed<FileFolderItem[]>(() => 资源数据.value?.folders ?? [])
const 全部普通文件列表 = computed<FileItem[]>(() => (
  (资源数据.value?.files ?? []).filter((file) => file.purpose === 'file')
))
const 全部文章图片列表 = computed<FileItem[]>(() => (
  (资源数据.value?.files ?? []).filter((file) => file.purpose === 'article_image')
))
const 全部动态图片列表 = computed<FileItem[]>(() => (
  (资源数据.value?.files ?? []).filter((file) => file.purpose === 'moment_image')
))
const 原始文件列表 = computed<FileItem[]>(() => (
  当前是文章图片视图.value
    ? 全部文章图片列表.value
    : (当前是动态图片视图.value ? 全部动态图片列表.value : 全部普通文件列表.value)
))
const 当前目录名称 = computed(() => (
  当前是文章图片视图.value
    ? 文章图片标签
    : (当前是动态图片视图.value ? 动态图片标签 : (当前目录.value?.name ?? 根目录名称))
))
const 选中目录树节点键 = computed(() => (
  当前是文章图片视图.value
    ? 文章图片节点键
    : (当前是动态图片视图.value ? 动态图片节点键 : (当前目录ID.value ?? 根目录节点键))
))
const 页面编辑 = useFilesPageEditing({
  当前目录ID,
  当前是内容图片视图,
  当前可在右侧新建文件夹: computed(() => !当前是内容图片视图.value && !是否全局搜索模式.value),
  当前展示资源列表: computed(() => 当前展示资源列表.value),
  目录树引用,
  获取右键菜单来源: () => 右键菜单.value.source,
  关闭右键菜单,
  刷新当前视图,
  创建文件夹: 执行文件夹创建,
  重命名资源: 执行资源重命名,
})
const {
  新建目录草稿状态,
  正在提交新建目录,
  正在提交右侧新建文件夹,
  重命名目录草稿状态,
  正在提交重命名目录,
  正在提交列表重命名,
  新建目录名称,
  右侧新建文件夹名称,
  重命名目录名称,
  列表重命名名称,
  右侧新建文件夹资源,
  新建文件夹,
  在右侧新建文件夹,
  设置右侧新建文件夹输入框引用,
  设置列表重命名输入框引用,
  处理新建目录输入框失焦,
  处理右侧新建文件夹输入框失焦,
  处理新建目录键盘事件,
  处理右侧新建文件夹键盘事件,
  重命名文件夹,
  处理重命名目录输入框失焦,
  处理重命名目录键盘事件,
  是否资源正在右侧重命名,
  是否资源是右侧新建文件夹草稿,
  是否资源处于右侧编辑态,
  处理右侧重命名输入框失焦,
  处理右侧重命名键盘事件,
  重命名文件,
} = 页面编辑
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
  {
    id: 动态图片节点键,
    parent_id: null,
    name: 动态图片标签,
    isMomentImages: true,
    children: [],
  },
]))

const 子文件夹列表 = computed<FileFolderItem[]>(() => (
  当前是内容图片视图.value
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
const 当前展示文件夹列表 = computed<文件夹展示项[]>(() => (
  是否全局搜索模式.value ? 全局搜索文件夹结果.value : 子文件夹列表.value
))
const 当前展示文件列表 = computed<文件展示项[]>(() => (
  是否全局搜索模式.value ? 全局搜索文件结果.value : 文件列表.value
))
const 当前展示资源列表 = computed<资源展示项[]>(() => {
  const list = 排序资源列表(当前展示文件夹列表.value, 当前展示文件列表.value, 当前排序.value)
  return 右侧新建文件夹资源.value ? [右侧新建文件夹资源.value, ...list] : list
})
const 页面视口 = useFilesPageViewport({
  当前展示资源列表,
  当前排序,
  关闭右键菜单,
  初始化加载: () => 拉取资源(),
})
const {
  正在拖动分隔线,
  当前渲染资源列表,
  当前页资源总数,
  当前已渲染资源总数,
  是否还有更多资源待渲染,
  剩余待渲染资源数,
  浏览器布局样式,
  获取增量渲染资源数量,
  加载更多资源,
  开始拖动分隔线,
} = 页面视口
const 当前目录文件夹总数 = computed(() => (当前是内容图片视图.value ? 0 : 原始子文件夹列表.value.length))
const 当前目录文件总数 = computed(() => 原始文件列表.value.length)
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
  if (当前是动态图片视图.value) {
    return 搜索关键词.value.trim() ? '当前动态图片筛选无结果' : '当前还没有动态图片'
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
const 全局搜索文件夹结果 = computed<FileSearchFolderItem[]>(() => 全局搜索结果.value.folders)
const 全局搜索文件结果 = computed<FileSearchFileItem[]>(() => 全局搜索结果.value.files)
const 全局搜索结果总数 = computed(() => 全局搜索文件夹结果.value.length + 全局搜索文件结果.value.length)
const 可预览图片文件列表 = computed<文件展示项[]>(() => 当前展示文件列表.value.filter((file) => 是否图片(file)))
const 可预览视频文件列表 = computed<文件展示项[]>(() => 当前展示文件列表.value.filter((file) => 是否视频(file)))
const {
  移动对话框可见,
  批量重命名对话框可见,
  媒体预览对话框可见,
  移动目标目录ID,
  待移动资源列表,
  批量重命名前缀,
  批量重命名起始序号,
  批量重命名位数,
  批量重命名保留扩展名,
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
  打开媒体预览: 打开媒体预览对话框,
  切换预览媒体,
} = useFilesPageDialogs({
  当前展示文件列表,
  可预览媒体文件列表: 可预览视频文件列表,
  已选资源总数,
  已选文件夹,
  已选文件,
})
const 搜索框占位文案 = computed(() => (
  搜索范围值.value === 'global'
    ? '跨目录搜索文件夹和文件'
    : (当前是文章图片视图.value
      ? '搜索当前文章图片'
      : (当前是动态图片视图.value ? '搜索当前动态图片' : '搜索当前目录中的文件夹和文件'))
))
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
  if (当前是动态图片视图.value) {
    return `当前显示 ${文件列表.value.length} 个动态图片`
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
  if (当前是动态图片视图.value) {
    return `这里汇总动态编辑器上传的 ${当前目录文件总数.value} 个图片资源。`
  }
  return `当前目录包含 ${当前目录文件夹总数.value} 个文件夹、${当前目录文件总数.value} 个文件。`
})
const 底部状态文案 = computed(() => (是否搜索中.value ? 搜索统计文案.value : 主区域描述.value))
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
const 当前右键菜单文件夹已选中 = computed(() => (
  右键菜单文件夹.value ? 是否选中文件夹(右键菜单文件夹.value.id) : false
))
const 当前右键菜单文件已选中 = computed(() => (
  右键菜单文件.value ? 是否选中文件(右键菜单文件.value.id) : false
))

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

const 页面交互 = useFilesPageInteractions({
  路由,
  右键菜单,
  重命名目录草稿状态,
  是否资源处于右侧编辑态,
  关闭右键菜单,
  查找文件展示项,
  执行资源移动,
  刷新当前视图,
})
const {
  显示目录树文件夹右键菜单,
  是否可拖拽目录树节点,
  开始拖拽目录树文件夹,
  结束拖拽资源,
  处理拖放到目录,
  打开文件,
  打开文章编辑器,
  复制图片链接,
  开始拖拽资源,
  处理资源行右键菜单,
  显示空白右键菜单,
} = 页面交互

const 页面导航上传 = useFilesPageNavigationUpload({
  当前目录ID,
  当前资源视图,
  搜索范围值,
  资源数据,
  文件上传输入框,
  目录上传输入框,
  重命名目录ID: computed(() => 重命名目录草稿状态.value?.id ?? null),
  关闭右键菜单,
  拉取资源,
  刷新当前视图,
  设置正在上传: (value) => {
    正在上传.value = value
  },
})
const {
  处理树节点点击,
  进入文件夹,
  处理导航栏点击,
  触发文件上传,
  触发目录上传,
  处理文件选择,
  处理目录选择,
} = 页面导航上传

const 页面动作 = useFilesPageActions({
  当前目录,
  当前目录ID,
  当前目录名称,
  当前排序,
  是否全局搜索模式,
  当前展示文件夹列表,
  当前展示文件列表,
  原始子文件夹列表,
  原始文件列表,
  已选文件夹,
  已选文件,
  待移动资源列表,
  移动目标目录ID,
  批量重命名前缀,
  批量重命名起始序号,
  批量重命名位数,
  批量重命名保留扩展名,
  关闭右键菜单,
  刷新当前视图,
  进入文件夹,
  是否消息框取消,
  获取不可移动资源数量,
  查找文件夹展示项,
  查找文件展示项,
  设置移动对话框可见: (visible) => {
    移动对话框可见.value = visible
  },
  设置批量重命名对话框可见: (visible) => {
    批量重命名对话框可见.value = visible
  },
  执行文件夹删除,
  执行批量删除: 执行批量删除资源,
  执行批量移动: 执行批量移动资源,
  执行批量重命名: 执行批量重命名资源,
})
const {
  确认删除文件夹,
  批量删除资源,
  打开移动对话框,
  打开批量重命名对话框,
  确认批量重命名,
  确认移动资源,
  下载资源,
} = 页面动作

function 打开媒体预览(file: 文件展示项) {
  关闭右键菜单()
  if (是否图片(file)) {
    void 打开图片预览(file, 可预览图片文件列表.value)
    return
  }
  打开媒体预览对话框(file)
}

function 关闭右键菜单() {
  右键菜单.value = 获取关闭右键菜单后的状态(右键菜单.value)
}

onBeforeUnmount(() => {
  关闭图片预览()
})

const 页面桥接 = useFilesPageBridges({
  搜索范围值,
  当前排序,
  是否已全选当前页,
  切换当前页全选动作,
  文件上传输入框,
  目录上传输入框,
  浏览器布局容器: 页面视口.浏览器布局容器,
  资源列表底部哨兵: 页面视口.资源列表底部哨兵,
  设置文件夹选中,
  是否选中文件夹,
  设置文件选中,
  是否选中文件,
  关闭右键菜单,
})

const {
  更新搜索范围,
  更新当前排序,
  切换当前页全选,
  设置文件上传输入框引用,
  设置目录上传输入框引用,
  设置资源列表底部哨兵引用,
  设置浏览器布局容器引用,
  切换右键菜单文件夹选中,
  切换右键菜单文件选中,
} = 页面桥接
</script>

<template>
  <div class="page-container">
    <FilesUploadInputs
      :设置文件上传输入框引用="设置文件上传输入框引用"
      :设置目录上传输入框引用="设置目录上传输入框引用"
      @file-change="处理文件选择"
      @folder-change="处理目录选择"
    />

    <FilesPageToolbar
      :正在上传="正在上传"
      :搜索关键词="搜索关键词"
      :搜索框占位文案="搜索框占位文案"
      :搜索范围值="搜索范围值"
      :当前排序="当前排序"
      :搜索范围选项="搜索范围选项"
      :排序选项="排序选项"
      :是否禁用排序="是否全局搜索模式"
      @update:search-keyword="搜索关键词 = $event"
      @update:search-scope="更新搜索范围"
      @update:sort-value="更新当前排序"
      @upload-files="触发文件上传"
      @upload-folders="触发目录上传"
    />

    <FilesExplorerShell
      :loading="是否显示骨架屏"
      :布局样式="浏览器布局样式"
      :正在拖动分隔线="正在拖动分隔线"
      :设置布局容器引用="设置浏览器布局容器引用"
      @resizer-pointerdown="开始拖动分隔线"
    >
      <template #sidebar>
        <FilesSidebarTree
          :正在上传="正在上传"
          :目录树数据="目录树数据"
          :选中目录树节点键="选中目录树节点键"
          :当前目录-id="当前目录ID"
          :重命名目录-id="重命名目录草稿状态?.id ?? null"
          :新建目录名称="新建目录名称"
          :正在提交新建目录="正在提交新建目录"
          :重命名目录名称="重命名目录名称"
          :正在提交重命名目录="正在提交重命名目录"
          :目录树引用="目录树引用透传.ref"
          :新建目录输入框="页面编辑.新建目录输入框"
          :重命名目录输入框="页面编辑.重命名目录输入框"
          :是否可拖拽目录树节点="是否可拖拽目录树节点"
          @create-folder="新建文件夹"
          @node-click="处理树节点点击"
          @folder-contextmenu="显示目录树文件夹右键菜单"
          @tree-folder-dragstart="开始拖拽目录树文件夹"
          @drag-end="结束拖拽资源"
          @drop-to-folder="处理拖放到目录"
          @update:new-folder-name="新建目录名称 = $event"
          @update:rename-folder-name="重命名目录名称 = $event"
          @create-keydown="处理新建目录键盘事件"
          @create-blur="处理新建目录输入框失焦"
          @rename-keydown="处理重命名目录键盘事件"
          @rename-blur="处理重命名目录输入框失焦"
        />
      </template>

      <FilesExplorerMainSection
        :已选中资源="已选资源总数 > 0"
        @blank-contextmenu="显示空白右键菜单"
      >
        <template #breadcrumb>
          <FilesBreadcrumbTrail
            :导航栏列表="导航栏列表"
            :禁止拖放节点键列表="[文章图片节点键, 动态图片节点键]"
            @navigate="处理导航栏点击"
            @drop="处理拖放到目录($event.folderId, $event.dragEvent)"
          />
        </template>

        <FilesResourceListSection
          :当前页资源总数="当前页资源总数"
          :当前空状态描述="当前空状态描述"
          :当前渲染资源列表="当前渲染资源列表"
          :是否全局搜索模式="是否全局搜索模式"
          :右侧新建文件夹名称="右侧新建文件夹名称"
          :列表重命名名称="列表重命名名称"
          :正在提交右侧新建文件夹="正在提交右侧新建文件夹"
          :正在提交列表重命名="正在提交列表重命名"
          :是否还有更多资源待渲染="是否还有更多资源待渲染"
          :当前已渲染资源总数="当前已渲染资源总数"
          :剩余待渲染资源数="剩余待渲染资源数"
          :获取增量渲染资源数量="获取增量渲染资源数量"
          :是否资源已选中="是否资源已选中"
          :是否资源处于右侧编辑态="是否资源处于右侧编辑态"
          :是否资源是右侧新建文件夹草稿="是否资源是右侧新建文件夹草稿"
          :是否资源正在右侧重命名="是否资源正在右侧重命名"
          :设置右侧新建文件夹输入框引用="设置右侧新建文件夹输入框引用"
          :设置列表重命名输入框引用="设置列表重命名输入框引用"
          :设置加载更多哨兵引用="设置资源列表底部哨兵引用"
          @select-change="设置资源选中($event.resource, $event.selected)"
          @folder-click="进入文件夹"
          @contextmenu="处理资源行右键菜单($event.resource, $event.mouseEvent)"
          @dragstart="开始拖拽资源($event.resource, $event.dragEvent)"
          @dragend="结束拖拽资源"
          @drop-to-folder="处理拖放到目录($event.folderId, $event.dragEvent)"
          @open-preview="打开媒体预览"
          @open-file="打开文件"
          @update:creating-name="右侧新建文件夹名称 = $event"
          @update:renaming-name="列表重命名名称 = $event"
          @creating-keydown="处理右侧新建文件夹键盘事件"
          @creating-blur="处理右侧新建文件夹输入框失焦"
          @renaming-keydown="处理右侧重命名键盘事件"
          @renaming-blur="处理右侧重命名输入框失焦"
          @load-more="加载更多资源"
        />
      </FilesExplorerMainSection>

      <template #footer>
        <FilesExplorerFooter :状态文案="底部状态文案" :刷新中="刷新中" />
      </template>
    </FilesExplorerShell>

    <FilesSelectionToolbar
      :已选资源总数="已选资源总数"
      :是否已全选当前页="是否已全选当前页"
      :当前选择可移动="当前选择可移动"
      :是否全局搜索模式="是否全局搜索模式"
      :下载操作按钮文案="下载操作按钮文案"
      :已选资源移动文案="已选资源移动文案"
      :已选资源重命名文案="已选资源重命名文案"
      :已选资源删除文案="已选资源删除文案"
      @toggle-select-page="切换当前页全选"
      @clear-selection="清空选择"
      @download="下载资源()"
      @open-move="打开移动对话框()"
      @open-batch-rename="打开批量重命名对话框"
      @delete="批量删除资源()"
    />

    <FilesMoveDialog
      :visible="移动对话框可见"
      :待移动资源数量="待移动资源列表.length"
      :目录树数据="目录树数据"
      :移动目标目录-id="移动目标目录ID"
      :根目录名称="根目录名称"
      :根目录节点键="根目录节点键"
      @update:visible="移动对话框可见 = $event"
      @update:target-folder-id="移动目标目录ID = $event"
      @confirm="确认移动资源"
    />

    <FilesBatchRenameDialog
      :visible="批量重命名对话框可见"
      :标题="重命名对话框标题"
      :名称前缀="批量重命名前缀"
      :起始序号="批量重命名起始序号"
      :补零位数="批量重命名位数"
      :保留扩展名="批量重命名保留扩展名"
      @update:visible="批量重命名对话框可见 = $event"
      @update:prefix="批量重命名前缀 = $event"
      @update:start-index="批量重命名起始序号 = $event"
      @update:digits="批量重命名位数 = $event"
      @update:keep-extension="批量重命名保留扩展名 = $event"
      @confirm="确认批量重命名"
    />

    <FilesMediaPreviewDialog
      :visible="媒体预览对话框可见"
      :当前预览媒体="当前预览媒体"
      :当前预览媒体索引="当前预览媒体索引"
      :可预览媒体总数="可预览视频文件列表.length"
      @update:visible="媒体预览对话框可见 = $event"
      @switch="切换预览媒体"
      @open-file="打开文件"
      @copy-image-link="复制图片链接"
    />

    <FilesContextMenu
      :右键菜单="右键菜单"
      :右键菜单文件夹="右键菜单文件夹"
      :右键菜单文件="右键菜单文件"
      :已选资源总数="已选资源总数"
      :当前选择可移动="当前选择可移动"
      :是否全局搜索模式="是否全局搜索模式"
      :已选资源下载菜单文案="已选资源下载菜单文案"
      :已选资源移动菜单文案="已选资源移动菜单文案"
      :已选资源重命名文案="已选资源重命名文案"
      :已选资源删除菜单文案="已选资源删除菜单文案"
      :当前右键菜单文件夹已选中="当前右键菜单文件夹已选中"
      :当前右键菜单文件已选中="当前右键菜单文件已选中"
      @create-folder="在右侧新建文件夹"
      @upload-files="触发文件上传"
      @upload-folders="触发目录上传"
      @download-selected="下载资源()"
      @move-selected="打开移动对话框()"
      @batch-rename="打开批量重命名对话框"
      @delete-selected="批量删除资源()"
      @open-folder="进入文件夹"
      @download-folder="下载资源({ type: 'folder', id: $event })"
      @rename-folder="重命名文件夹"
      @move-folder="打开移动对话框({ type: 'folder', id: $event })"
      @toggle-folder-select="切换右键菜单文件夹选中"
      @delete-folder="确认删除文件夹"
      @open-preview="打开媒体预览"
      @open-file="打开文件"
      @open-article="打开文章编辑器"
      @open-file-folder="进入文件夹"
      @download-file="下载资源({ type: 'file', id: $event })"
      @rename-file="重命名文件"
      @move-file="打开移动对话框({ type: 'file', id: $event })"
      @copy-image-link="复制图片链接"
      @toggle-file-select="切换右键菜单文件选中"
      @delete-file="批量删除资源({ type: 'file', id: $event })"
    />
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

@media (max-width: 768px) {
  .page-container {
    padding: 12px 16px 16px;
  }
}
</style>
