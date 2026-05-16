import { ElMessage, ElMessageBox } from 'element-plus'
import { 获取API错误消息 } from '@personal-system/api'
import type { 批量删除执行结果, 批量执行结果 } from './actions'
import type { 资源标识 } from './shared'

interface 批量删除编排参数 {
  targetResources: 资源标识[]
  当前目录ID: string | null
  当前目录父级ID: string | null
  关闭右键菜单: () => void
  是否消息框取消: (error: unknown) => boolean
  执行删除: (resources: 资源标识[], currentFolderId: string | null) => Promise<批量删除执行结果>
  进入文件夹: (folderId: string | null) => Promise<void>
  刷新当前视图: () => Promise<void>
}

interface 打开移动对话框参数 {
  targetResources: 资源标识[]
  当前目录ID: string | null
  不可移动资源数量: number
  关闭右键菜单: () => void
  设置待移动资源列表: (resources: 资源标识[]) => void
  设置移动目标目录ID: (folderId: string | null) => void
  设置移动对话框可见: (visible: boolean) => void
}

interface 打开批量重命名对话框参数 {
  targetResources: 资源标识[]
  关闭右键菜单: () => void
  设置批量重命名对话框可见: (visible: boolean) => void
}

interface 批量重命名编排参数 {
  targetResources: 资源标识[]
  构建批量文件名: (resource: 资源标识, index: number) => string
  执行重命名: (
    resources: 资源标识[],
    nameBuilder: (resource: 资源标识, index: number) => string,
  ) => Promise<批量执行结果>
  设置批量重命名对话框可见: (visible: boolean) => void
  刷新当前视图: () => Promise<void>
}

interface 批量移动编排参数 {
  targetResources: 资源标识[]
  移动目标目录ID: string | null
  不可移动资源数量: number
  执行移动: (resources: 资源标识[], targetFolderId: string | null) => Promise<批量执行结果>
  设置移动对话框可见: (visible: boolean) => void
  设置待移动资源列表: (resources: 资源标识[]) => void
  刷新当前视图: () => Promise<void>
}

export async function 执行批量删除编排({
  targetResources,
  当前目录ID,
  当前目录父级ID,
  关闭右键菜单,
  是否消息框取消,
  执行删除,
  进入文件夹,
  刷新当前视图,
}: 批量删除编排参数) {
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
    ElMessage.error(获取API错误消息(error, '删除资源失败'))
    return
  }

  const { 失败结果, 成功数量, 当前目录已删除 } = await 执行删除(targetResources, 当前目录ID)

  if (成功数量 > 0) {
    ElMessage.success(`已删除 ${成功数量} 项资源`)
  }
  if (失败结果.length > 0) {
    ElMessage.error(获取API错误消息(失败结果[0].reason, `有 ${失败结果.length} 项资源删除失败`))
  }

  if (当前目录已删除) {
    await 进入文件夹(当前目录父级ID)
    return
  }
  await 刷新当前视图()
}

export function 打开移动对话框编排({
  targetResources,
  当前目录ID,
  不可移动资源数量,
  关闭右键菜单,
  设置待移动资源列表,
  设置移动目标目录ID,
  设置移动对话框可见,
}: 打开移动对话框参数) {
  if (不可移动资源数量 > 0) {
    ElMessage.warning(`当前选中内容中有 ${不可移动资源数量} 项内容图片，暂不支持移动`)
    return
  }

  关闭右键菜单()
  设置待移动资源列表(targetResources)
  设置移动目标目录ID(当前目录ID)
  设置移动对话框可见(true)
}

export function 打开批量重命名对话框编排({
  targetResources,
  关闭右键菜单,
  设置批量重命名对话框可见,
}: 打开批量重命名对话框参数) {
  if (targetResources.length === 0) {
    ElMessage.warning('请先选择资源')
    return
  }

  关闭右键菜单()
  设置批量重命名对话框可见(true)
}

export async function 执行批量重命名编排({
  targetResources,
  构建批量文件名,
  执行重命名,
  设置批量重命名对话框可见,
  刷新当前视图,
}: 批量重命名编排参数) {
  if (targetResources.length === 0) {
    ElMessage.warning('请先选择资源')
    设置批量重命名对话框可见(false)
    return
  }

  const { 失败结果, 成功数量 } = await 执行重命名(
    targetResources,
    (resource, index) => 构建批量文件名(resource, index),
  )

  if (成功数量 > 0) {
    ElMessage.success(`已重命名 ${成功数量} 项资源`)
  }
  if (失败结果.length > 0) {
    ElMessage.error(获取API错误消息(失败结果[0].reason, `有 ${失败结果.length} 项资源重命名失败`))
  }

  设置批量重命名对话框可见(false)
  await 刷新当前视图()
}

export async function 执行批量移动编排({
  targetResources,
  移动目标目录ID,
  不可移动资源数量,
  执行移动,
  设置移动对话框可见,
  设置待移动资源列表,
  刷新当前视图,
}: 批量移动编排参数) {
  if (targetResources.length === 0) {
    设置移动对话框可见(false)
    return
  }
  if (不可移动资源数量 > 0) {
    ElMessage.warning(`当前选中内容中有 ${不可移动资源数量} 项内容图片，暂不支持移动`)
    设置移动对话框可见(false)
    设置待移动资源列表([])
    return
  }

  const { 失败结果, 成功数量 } = await 执行移动(targetResources, 移动目标目录ID)

  if (成功数量 > 0) {
    ElMessage.success(`已移动 ${成功数量} 项资源`)
  }
  if (失败结果.length > 0) {
    ElMessage.error(获取API错误消息(失败结果[0].reason, `有 ${失败结果.length} 项资源移动失败`))
  }

  设置移动对话框可见(false)
  设置待移动资源列表([])
  await 刷新当前视图()
}
