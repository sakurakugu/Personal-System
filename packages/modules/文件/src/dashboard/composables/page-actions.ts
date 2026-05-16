import { ElMessage } from 'element-plus'
import type { ComputedRef, Ref } from 'vue'
import type {
  FileFolderItem,
  FileItem,
} from '../../types'
import {
  执行批量删除编排,
  执行批量移动编排,
  执行批量重命名编排,
  打开批量重命名对话框编排,
  打开移动对话框编排,
} from '../../core/batch-actions'
import { 执行文件夹删除确认编排 } from '../../core/folder-actions'
import { 执行资源下载 } from '../../core/preview'
import {
  构建批量文件名 as 构建批量文件名工具,
  获取批量重命名资源列表 as 获取批量重命名资源列表工具,
  获取操作资源列表 as 获取操作资源列表工具,
} from '../../core/selection'
import type {
  排序方式,
  文件夹展示项,
  文件展示项,
  资源标识,
} from '../../core/shared'
import type {
  批量删除执行结果,
  批量执行结果,
} from '../../core/actions'

export function 使用文件页面操作(options: {
  当前目录: Ref<FileFolderItem | null> | ComputedRef<FileFolderItem | null>
  当前目录ID: Ref<string | null> | ComputedRef<string | null>
  当前目录名称: Ref<string> | ComputedRef<string>
  当前排序: Ref<排序方式> | ComputedRef<排序方式>
  是否全局搜索模式: Ref<boolean> | ComputedRef<boolean>
  当前展示文件夹列表: Ref<文件夹展示项[]> | ComputedRef<文件夹展示项[]>
  当前展示文件列表: Ref<文件展示项[]> | ComputedRef<文件展示项[]>
  原始子文件夹列表: Ref<FileFolderItem[]> | ComputedRef<FileFolderItem[]>
  原始文件列表: Ref<FileItem[]> | ComputedRef<FileItem[]>
  已选文件夹: Ref<Set<string>>
  已选文件: Ref<Set<string>>
  待移动资源列表: Ref<资源标识[]>
  移动目标目录ID: Ref<string | null>
  批量重命名前缀: Ref<string>
  批量重命名起始序号: Ref<number>
  批量重命名位数: Ref<number>
  批量重命名保留扩展名: Ref<boolean>
  关闭右键菜单: () => void
  刷新当前视图: () => Promise<void>
  进入文件夹: (folderId: string | null) => Promise<void>
  是否消息框取消: (error: unknown) => boolean
  获取不可移动资源数量: (resources: 资源标识[]) => number
  查找文件夹展示项: (id: string) => 文件夹展示项 | null
  查找文件展示项: (id: string) => 文件展示项 | null
  设置移动对话框可见: (visible: boolean) => void
  设置批量重命名对话框可见: (visible: boolean) => void
  执行文件夹删除: (folderId: string) => Promise<unknown>
  执行批量删除: (
    resources: 资源标识[],
    currentFolderId: string | null,
  ) => Promise<批量删除执行结果>
  执行批量移动: (
    resources: 资源标识[],
    targetFolderId: string | null,
  ) => Promise<批量执行结果>
  执行批量重命名: (
    resources: 资源标识[],
    nameBuilder: (resource: 资源标识, index: number) => string,
  ) => Promise<批量执行结果>
}) {
  function 读取当前已选资源() {
    return [
      ...[...options.已选文件夹.value].map((id) => ({ type: 'folder', id } as const)),
      ...[...options.已选文件.value].map((id) => ({ type: 'file', id } as const)),
    ]
  }

  function 获取操作资源列表(resource?: 资源标识) {
    const targetResources = 获取操作资源列表工具(resource, 读取当前已选资源())
    if (targetResources.length === 0) {
      ElMessage.warning('请先选择资源')
      return null
    }
    return targetResources
  }

  async function 确认删除文件夹(folder: 文件夹展示项) {
    await 执行文件夹删除确认编排({
      folder,
      当前目录ID: options.当前目录.value?.id ?? null,
      关闭右键菜单: options.关闭右键菜单,
      执行文件夹删除: options.执行文件夹删除,
      进入文件夹: options.进入文件夹,
      刷新当前视图: options.刷新当前视图,
      是否消息框取消: options.是否消息框取消,
    })
  }

  async function 批量删除资源(resource?: 资源标识) {
    const targetResources = 获取操作资源列表(resource)
    if (!targetResources) {
      return
    }

    await 执行批量删除编排({
      targetResources,
      当前目录ID: options.当前目录.value?.id ?? null,
      当前目录父级ID: options.当前目录.value?.parent_id ?? null,
      关闭右键菜单: options.关闭右键菜单,
      是否消息框取消: options.是否消息框取消,
      执行删除: options.执行批量删除,
      进入文件夹: options.进入文件夹,
      刷新当前视图: options.刷新当前视图,
    })
  }

  function 打开移动对话框(resource?: 资源标识) {
    const targetResources = 获取操作资源列表(resource)
    if (!targetResources) {
      return
    }

    打开移动对话框编排({
      targetResources,
      当前目录ID: options.当前目录ID.value,
      不可移动资源数量: options.获取不可移动资源数量(targetResources),
      关闭右键菜单: options.关闭右键菜单,
      设置待移动资源列表: (resources) => {
        options.待移动资源列表.value = resources
      },
      设置移动目标目录ID: (folderId) => {
        options.移动目标目录ID.value = folderId
      },
      设置移动对话框可见: options.设置移动对话框可见,
    })
  }

  function 打开批量重命名对话框() {
    打开批量重命名对话框编排({
      targetResources: 读取当前已选资源(),
      关闭右键菜单: options.关闭右键菜单,
      设置批量重命名对话框可见: options.设置批量重命名对话框可见,
    })
  }

  function 构建批量文件名(resource: 资源标识, offset: number) {
    return 构建批量文件名工具(resource, offset, options.原始文件列表.value, {
      前缀: options.批量重命名前缀.value,
      起始序号: options.批量重命名起始序号.value,
      位数: options.批量重命名位数.value,
      保留扩展名: options.批量重命名保留扩展名.value,
    })
  }

  function 获取批量重命名资源列表() {
    return 获取批量重命名资源列表工具(
      options.原始子文件夹列表.value,
      options.原始文件列表.value,
      options.已选文件夹.value,
      options.已选文件.value,
      options.当前排序.value,
    )
  }

  async function 确认批量重命名() {
    await 执行批量重命名编排({
      targetResources: 获取批量重命名资源列表(),
      构建批量文件名,
      执行重命名: options.执行批量重命名,
      设置批量重命名对话框可见: options.设置批量重命名对话框可见,
      刷新当前视图: options.刷新当前视图,
    })
  }

  async function 确认移动资源() {
    await 执行批量移动编排({
      targetResources: options.待移动资源列表.value,
      移动目标目录ID: options.移动目标目录ID.value,
      不可移动资源数量: options.获取不可移动资源数量(options.待移动资源列表.value),
      执行移动: options.执行批量移动,
      设置移动对话框可见: options.设置移动对话框可见,
      设置待移动资源列表: (resources) => {
        options.待移动资源列表.value = resources
      },
      刷新当前视图: options.刷新当前视图,
    })
  }

  async function 下载资源(resource?: 资源标识) {
    const targetResources = 获取操作资源列表(resource)
    if (!targetResources) {
      return
    }

    options.关闭右键菜单()
    await 执行资源下载({
      资源列表: targetResources,
      当前目录名称: options.当前目录名称.value,
      是否全局搜索模式: options.是否全局搜索模式.value,
      查找文件夹展示项: options.查找文件夹展示项,
      查找文件展示项: options.查找文件展示项,
    })
  }

  return {
    确认删除文件夹,
    批量删除资源,
    打开移动对话框,
    打开批量重命名对话框,
    确认批量重命名,
    确认移动资源,
    下载资源,
  }
}
