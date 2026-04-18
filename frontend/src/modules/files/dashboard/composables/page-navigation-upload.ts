import type { ComputedRef, Ref } from 'vue'
import type {
  FileBreadcrumbItem,
  FileExplorerData,
} from '../../types'
import {
  执行文件上传 as 执行文件上传动作,
  执行目录上传 as 执行目录上传动作,
} from '../../core/upload'
import {
  执行上传流程,
  触发上传选择,
  读取并清空上传文件,
} from '../../core/upload-actions'
import {
  文章图片节点键,
  type 搜索范围,
  type 目录树节点,
} from '../../core/shared'

export function useFilesPageNavigationUpload(options: {
  当前目录ID: Ref<string | null> | ComputedRef<string | null>
  当前资源视图: Ref<'files' | 'article-images'>
  搜索范围值: Ref<搜索范围>
  资源数据: Ref<FileExplorerData | null> | ComputedRef<FileExplorerData | null>
  文件上传输入框: Ref<globalThis.HTMLInputElement | null>
  目录上传输入框: Ref<globalThis.HTMLInputElement | null>
  重命名目录ID: Ref<string | null> | ComputedRef<string | null>
  关闭右键菜单: () => void
  拉取资源: (folderId?: string | null, config?: { 静默?: boolean }) => Promise<void>
  刷新当前视图: (folderId?: string | null) => Promise<void>
  设置正在上传: (value: boolean) => void
}) {
  function 处理树节点点击(data: 目录树节点) {
    if (data.isDraft || options.重命名目录ID.value === data.id) {
      return
    }
    if (data.isArticleImages) {
      void 打开文章图片视图()
      return
    }
    void 进入文件夹(data.isRoot ? null : data.id)
  }

  async function 打开文件夹(folderId: string | null) {
    options.关闭右键菜单()
    options.当前资源视图.value = 'files'
    await options.拉取资源(folderId, { 静默: options.资源数据.value !== null })
  }

  async function 进入文件夹(folderId: string | null) {
    options.搜索范围值.value = 'current'
    await 打开文件夹(folderId)
  }

  async function 打开文章图片视图() {
    options.关闭右键菜单()
    options.搜索范围值.value = 'current'
    if (options.当前目录ID.value !== null || options.当前资源视图.value !== 'article-images') {
      await options.拉取资源(null, { 静默: options.资源数据.value !== null })
    }
    options.当前资源视图.value = 'article-images'
  }

  function 处理导航栏点击(item: FileBreadcrumbItem) {
    if (item.id === 文章图片节点键) {
      void 打开文章图片视图()
      return
    }
    void 进入文件夹(item.id)
  }

  function 触发文件上传() {
    options.关闭右键菜单()
    触发上传选择(options.文件上传输入框.value)
  }

  function 触发目录上传() {
    options.关闭右键菜单()
    触发上传选择(options.目录上传输入框.value)
  }

  async function 处理文件选择(event: globalThis.Event) {
    const files = 读取并清空上传文件(event)
    await 执行上传流程({
      files,
      关闭右键菜单: options.关闭右键菜单,
      设置正在上传: options.设置正在上传,
      执行上传: (selectedFiles) => 执行文件上传动作(selectedFiles, options.当前目录ID.value),
      获取成功提示: (successCount) => `已上传 ${successCount} 个文件`,
      获取失败提示: (failedCount) => `有 ${failedCount} 个文件上传失败`,
      刷新当前视图: options.刷新当前视图,
    })
  }

  async function 处理目录选择(event: globalThis.Event) {
    const files = 读取并清空上传文件(event)
    await 执行上传流程({
      files,
      关闭右键菜单: options.关闭右键菜单,
      设置正在上传: options.设置正在上传,
      执行上传: (selectedFiles) => (
        执行目录上传动作(selectedFiles, options.当前目录ID.value, options.资源数据.value?.tree ?? [])
      ),
      获取成功提示: (successCount) => `目录上传完成，共处理 ${successCount} 个文件`,
      获取失败提示: (failedCount) => `有 ${failedCount} 个文件上传失败`,
      刷新当前视图: options.刷新当前视图,
    })
  }

  return {
    处理树节点点击,
    打开文件夹,
    进入文件夹,
    打开文章图片视图,
    处理导航栏点击,
    触发文件上传,
    触发目录上传,
    处理文件选择,
    处理目录选择,
  }
}
