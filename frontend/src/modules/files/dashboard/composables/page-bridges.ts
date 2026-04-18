import type {
  ComponentPublicInstance,
  ComputedRef,
  Ref,
} from 'vue'
import type {
  排序方式,
  搜索范围,
} from '../../core/shared'

export function useFilesPageBridges(options: {
  搜索范围值: Ref<搜索范围>
  当前排序: Ref<排序方式>
  是否已全选当前页: Ref<boolean> | ComputedRef<boolean>
  切换当前页全选动作: (selectedAll: boolean) => void
  文件上传输入框: Ref<globalThis.HTMLInputElement | null>
  目录上传输入框: Ref<globalThis.HTMLInputElement | null>
  浏览器布局容器: Ref<globalThis.HTMLElement | null>
  资源列表底部哨兵: Ref<globalThis.HTMLDivElement | null>
  设置文件夹选中: (folderId: string, selected: boolean) => void
  是否选中文件夹: (folderId: string) => boolean
  设置文件选中: (fileId: string, selected: boolean) => void
  是否选中文件: (fileId: string) => boolean
  关闭右键菜单: () => void
}) {
  function 更新搜索范围(value: string) {
    options.搜索范围值.value = value as 搜索范围
  }

  function 更新当前排序(value: string) {
    options.当前排序.value = value as 排序方式
  }

  function 切换当前页全选() {
    options.切换当前页全选动作(options.是否已全选当前页.value)
  }

  function 设置文件上传输入框引用(element: globalThis.Element | ComponentPublicInstance | null) {
    options.文件上传输入框.value = element instanceof globalThis.HTMLInputElement ? element : null
  }

  function 设置目录上传输入框引用(element: globalThis.Element | ComponentPublicInstance | null) {
    options.目录上传输入框.value = element instanceof globalThis.HTMLInputElement ? element : null
  }

  function 设置资源列表底部哨兵引用(element: globalThis.Element | ComponentPublicInstance | null) {
    options.资源列表底部哨兵.value = element instanceof globalThis.HTMLDivElement ? element : null
  }

  function 设置浏览器布局容器引用(element: globalThis.Element | ComponentPublicInstance | null) {
    options.浏览器布局容器.value = element instanceof globalThis.HTMLElement ? element : null
  }

  function 切换右键菜单文件夹选中(folderId: string) {
    options.设置文件夹选中(folderId, !options.是否选中文件夹(folderId))
    options.关闭右键菜单()
  }

  function 切换右键菜单文件选中(fileId: string) {
    options.设置文件选中(fileId, !options.是否选中文件(fileId))
    options.关闭右键菜单()
  }

  return {
    更新搜索范围,
    更新当前排序,
    切换当前页全选,
    设置文件上传输入框引用,
    设置目录上传输入框引用,
    设置资源列表底部哨兵引用,
    设置浏览器布局容器引用,
    切换右键菜单文件夹选中,
    切换右键菜单文件选中,
  }
}
