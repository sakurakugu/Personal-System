import { ElMessage } from 'element-plus'
import { ref, type ComputedRef, type Ref } from 'vue'
import type { Router } from 'vue-router'
import {
  处理目录树文件夹右键菜单触发,
  处理空白右键菜单触发,
  处理资源行右键菜单触发,
} from '../../core/context-menu-actions'
import {
  写入拖拽资源 as 写入拖拽资源工具,
  处理拖放到目录 as 处理拖放到目录工具,
  是否可拖拽目录树节点 as 是否可拖拽目录树节点工具,
} from '../../core/drag'
import {
  获取原始文件路径,
  是否可移动文件,
  解析链接,
} from '../../core/resource'
import type {
  右键菜单状态,
  目录树节点,
  文件夹展示项,
  文件展示项,
  资源展示项,
  资源标识,
  重命名目录草稿,
} from '../../core/shared'

export function 使用文件页面交互(options: {
  路由: Router
  右键菜单: Ref<右键菜单状态>
  重命名目录草稿状态: Ref<重命名目录草稿 | null> | ComputedRef<重命名目录草稿 | null>
  是否资源处于右侧编辑态: (resource: 资源展示项) => boolean
  关闭右键菜单: () => void
  查找文件展示项: (id: string) => 文件展示项 | null
  执行资源移动: (resource: 资源标识, targetFolderId: string | null) => Promise<unknown>
  刷新当前视图: () => Promise<void>
}) {
  const 当前拖拽资源 = ref<资源标识 | null>(null)

  function 显示目录树文件夹右键菜单(data: 目录树节点, event: globalThis.MouseEvent) {
    const nextMenu = 处理目录树文件夹右键菜单触发(
      data,
      event,
      options.重命名目录草稿状态.value?.id ?? null,
    )
    if (!nextMenu) {
      return
    }
    options.右键菜单.value = nextMenu
  }

  function 是否可拖拽目录树节点(node: 目录树节点) {
    return 是否可拖拽目录树节点工具(node, options.重命名目录草稿状态.value?.id ?? null)
  }

  function 写入拖拽资源(event: globalThis.DragEvent, resource: 资源标识) {
    当前拖拽资源.value = resource
    写入拖拽资源工具(event, resource)
  }

  function 开始拖拽文件夹(folder: 文件夹展示项, event: globalThis.DragEvent) {
    写入拖拽资源(event, {
      type: 'folder',
      id: folder.id,
    })
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
      查找文件展示项: options.查找文件展示项,
      执行资源移动: options.执行资源移动,
      刷新当前视图: options.刷新当前视图,
    })
  }

  function 打开文件(url: string) {
    options.关闭右键菜单()
    window.open(解析链接(url), '_blank', 'noopener,noreferrer')
  }

  function 打开文章编辑器(articleId: string) {
    options.关闭右键菜单()
    void options.路由.push(`/dashboard/articles/edit/${articleId}`)
  }

  function 打开作品推荐(mediaItemId: string) {
    options.关闭右键菜单()
    void options.路由.push({
      path: '/dashboard/media',
      query: { media_id: mediaItemId },
    })
  }

  async function 复制图片链接(url: string) {
    options.关闭右键菜单()
    try {
      await navigator.clipboard.writeText(获取原始文件路径(url))
      ElMessage.success('图片链接已复制')
    } catch {
      ElMessage.error('复制失败，请检查浏览器权限')
    }
  }

  function 开始拖拽资源(resource: 资源展示项, event: globalThis.DragEvent) {
    if (resource.type === 'folder') {
      开始拖拽文件夹(resource.item, event)
      return
    }
    if (resource.type === 'trash') {
      return
    }
    开始拖拽文件(resource.item, event)
  }

  function 处理资源行右键菜单(resource: 资源展示项, event: globalThis.MouseEvent) {
    if (resource.type === 'trash') {
      event.preventDefault()
      return
    }
    const nextMenu = 处理资源行右键菜单触发(
      resource,
      event,
      options.是否资源处于右侧编辑态(resource),
    )
    if (!nextMenu) {
      return
    }
    options.右键菜单.value = nextMenu
  }

  function 显示空白右键菜单(event: globalThis.MouseEvent) {
    const nextMenu = 处理空白右键菜单触发(event)
    if (!nextMenu) {
      return
    }
    options.右键菜单.value = nextMenu
  }

  return {
    显示目录树文件夹右键菜单,
    是否可拖拽目录树节点,
    开始拖拽目录树文件夹,
    结束拖拽资源,
    处理拖放到目录,
    打开文件,
    打开文章编辑器,
    打开作品推荐,
    复制图片链接,
    开始拖拽资源,
    处理资源行右键菜单,
    显示空白右键菜单,
  }
}
