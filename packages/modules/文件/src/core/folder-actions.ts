import { ElMessage, ElMessageBox } from 'element-plus'
import { 获取API错误消息 } from '@personal-system/api'
import type { 文件夹展示项 } from './shared'

interface 文件夹删除编排参数 {
  folder: 文件夹展示项
  当前目录ID: string | null
  关闭右键菜单: () => void
  执行文件夹删除: (folderId: string) => Promise<unknown>
  进入文件夹: (folderId: string | null) => Promise<void>
  刷新当前视图: () => Promise<void>
}

interface 文件夹删除确认编排参数 extends 文件夹删除编排参数 {
  是否消息框取消: (error: unknown) => boolean
}

export async function 执行文件夹删除编排({
  folder,
  当前目录ID,
  关闭右键菜单,
  执行文件夹删除,
  进入文件夹,
  刷新当前视图,
}: 文件夹删除编排参数) {
  关闭右键菜单()
  try {
    await 执行文件夹删除(folder.id)
    ElMessage.success('文件夹已删除')
    if (当前目录ID === folder.id) {
      await 进入文件夹(folder.parent_id)
      return
    }
    await 刷新当前视图()
  } catch (error) {
    ElMessage.error(获取API错误消息(error, '删除文件夹失败'))
  }
}

export async function 执行文件夹删除确认编排({
  folder,
  当前目录ID,
  关闭右键菜单,
  执行文件夹删除,
  进入文件夹,
  刷新当前视图,
  是否消息框取消,
}: 文件夹删除确认编排参数) {
  关闭右键菜单()
  try {
    await ElMessageBox.confirm(
      '确定删除此文件夹？仅空文件夹可删除。',
      '删除文件夹',
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
    ElMessage.error(获取API错误消息(error, '删除文件夹失败'))
    return
  }

  await 执行文件夹删除编排({
    folder,
    当前目录ID,
    关闭右键菜单,
    执行文件夹删除,
    进入文件夹,
    刷新当前视图,
  })
}

