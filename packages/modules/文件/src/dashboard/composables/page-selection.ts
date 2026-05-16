import { ref } from 'vue'
import type {
  FileExplorerData,
  FileFolderItem,
  FileItem,
} from '../../types'
import {
  是否资源已选中 as 是否集合已选中,
  切换当前页资源全选,
  更新选中集合,
  读取当前已选资源 as 读取当前已选资源工具,
} from '../../core/selection'
import type {
  排序方式,
  文件夹展示项,
  文件展示项,
  资源展示项,
  资源标识,
} from '../../core/shared'

export function useFilesPageSelection(options: {
  获取资源数据: () => FileExplorerData | null
  获取当前目录: () => FileFolderItem | null
  获取当前展示文件夹列表: () => 文件夹展示项[]
  获取当前展示文件列表: () => 文件展示项[]
  获取原始子文件夹列表: () => FileFolderItem[]
  获取原始文件列表: () => FileItem[]
  获取当前排序: () => 排序方式
  从目录树节点构建文件夹: (node: FileExplorerData['tree'][number]) => FileFolderItem
  收集目录树节点: (node: FileExplorerData['tree'][number]) => FileExplorerData['tree']
  是否普通文件: (file: 文件展示项) => boolean
}) {
  const 已选文件夹 = ref<Set<string>>(new Set())
  const 已选文件 = ref<Set<string>>(new Set())

  function 清空选择() {
    已选文件夹.value = new Set()
    已选文件.value = new Set()
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

  function 切换当前页全选(是否已全选当前页: boolean) {
    const result = 切换当前页资源全选(
      已选文件夹.value,
      已选文件.value,
      options.获取当前展示文件夹列表(),
      options.获取当前展示文件列表(),
      是否已全选当前页,
    )
    已选文件夹.value = result.文件夹
    已选文件.value = result.文件
  }

  function 读取当前已选资源() {
    return 读取当前已选资源工具(已选文件夹.value, 已选文件.value)
  }

  function 查找文件夹展示项(id: string): 文件夹展示项 | null {
    const 当前目录 = options.获取当前目录()
    if (当前目录?.id === id) {
      return 当前目录
    }

    const treeFolder = options.获取资源数据()?.tree
      .flatMap((node) => options.收集目录树节点(node))
      .find((item) => item.id === id)

    return options.获取当前展示文件夹列表().find((item) => item.id === id)
      ?? options.获取原始子文件夹列表().find((item) => item.id === id)
      ?? (treeFolder ? options.从目录树节点构建文件夹(treeFolder) : null)
      ?? null
  }

  function 查找文件展示项(id: string) {
    return options.获取当前展示文件列表().find((item) => item.id === id)
      ?? options.获取原始文件列表().find((item) => item.id === id)
      ?? null
  }

  function 是否资源支持移动(resource: 资源标识) {
    if (resource.type === 'folder') {
      return true
    }
    const file = 查找文件展示项(resource.id)
    return file ? options.是否普通文件(file) : true
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

  return {
    已选文件夹,
    已选文件,
    清空选择,
    是否选中文件夹,
    是否选中文件,
    设置文件夹选中,
    设置文件选中,
    切换当前页全选,
    读取当前已选资源,
    查找文件夹展示项,
    查找文件展示项,
    是否资源支持移动,
    获取不可移动资源数量,
    是否资源已选中,
    设置资源选中,
  }
}
