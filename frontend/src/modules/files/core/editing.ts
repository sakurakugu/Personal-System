import type { 文件夹展示项, 文件展示项, 右侧新建文件夹草稿, 列表重命名草稿, 新建目录草稿, 重命名目录草稿, 资源展示项 } from './shared'

export function 创建新建目录草稿(id: string, parentId: string | null): 新建目录草稿 {
  return {
    id,
    parentId,
    name: '',
  }
}

export function 创建右侧新建文件夹草稿(id: string, parentId: string | null): 右侧新建文件夹草稿 {
  return {
    id,
    parentId,
    name: '',
  }
}

export function 创建重命名目录草稿(folder: 文件夹展示项): 重命名目录草稿 {
  return {
    id: folder.id,
    name: folder.name,
    originalName: folder.name,
  }
}

export function 创建列表文件夹重命名草稿(folder: 文件夹展示项): 列表重命名草稿 {
  return {
    type: 'folder',
    id: folder.id,
    name: folder.name,
    originalName: folder.name,
  }
}

export function 创建列表文件重命名草稿(file: 文件展示项): 列表重命名草稿 {
  return {
    type: 'file',
    id: file.id,
    name: file.original_name,
    originalName: file.original_name,
  }
}

export function 是否资源正在右侧重命名(resource: 资源展示项, draft: 列表重命名草稿 | null) {
  return draft?.id === resource.id && draft.type === resource.type
}

export function 是否资源是右侧新建文件夹草稿(resource: 资源展示项, draft: 右侧新建文件夹草稿 | null) {
  return resource.type === 'folder' && draft?.id === resource.id
}

export function 是否资源处于右侧编辑态(
  resource: 资源展示项,
  createDraft: 右侧新建文件夹草稿 | null,
  renameDraft: 列表重命名草稿 | null,
) {
  return 是否资源是右侧新建文件夹草稿(resource, createDraft)
    || 是否资源正在右侧重命名(resource, renameDraft)
}
