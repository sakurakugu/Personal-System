import { ElMessage } from 'element-plus'
import { getApiErrorMessage } from '../../../shared/api'
import { 拖拽数据类型 } from './shared'
import { 是否可移动文件 } from './resource'
import type {
  目录树节点,
  文件展示项,
  资源标识,
} from './shared'

interface 处理拖放到目录参数 {
  event: globalThis.DragEvent
  targetFolderId: string | null
  当前拖拽资源: 资源标识 | null
  清空当前拖拽资源: () => void
  查找文件展示项: (id: string) => 文件展示项 | null
  执行资源移动: (resource: 资源标识, targetFolderId: string | null) => Promise<unknown>
  刷新当前视图: () => Promise<void>
}

export function 是否可拖拽目录树节点(node: 目录树节点, 重命名目录ID: string | null) {
  return !node.isRoot && !node.isArticleImages && !node.isDraft && 重命名目录ID !== node.id
}

export function 写入拖拽资源(event: globalThis.DragEvent, resource: 资源标识) {
  event.dataTransfer?.setData(拖拽数据类型, JSON.stringify(resource))
  event.dataTransfer?.setData('text/plain', JSON.stringify(resource))
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move'
  }
}

export function 读取拖拽资源(event: globalThis.DragEvent, fallbackResource: 资源标识 | null) {
  const payload = event.dataTransfer?.getData(拖拽数据类型) || event.dataTransfer?.getData('text/plain')
  if (!payload) {
    return fallbackResource
  }

  try {
    return JSON.parse(payload) as 资源标识
  } catch {
    return fallbackResource
  }
}

export async function 处理拖放到目录({
  event,
  targetFolderId,
  当前拖拽资源,
  清空当前拖拽资源,
  查找文件展示项,
  执行资源移动,
  刷新当前视图,
}: 处理拖放到目录参数) {
  event.preventDefault()
  event.stopPropagation()

  const resource = 读取拖拽资源(event, 当前拖拽资源)
  清空当前拖拽资源()
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
    } else if (resource.id === targetFolderId) {
      return
    }

    await 执行资源移动(resource, targetFolderId)
    ElMessage.success('已移动')
    await 刷新当前视图()
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '移动失败'))
  }
}

