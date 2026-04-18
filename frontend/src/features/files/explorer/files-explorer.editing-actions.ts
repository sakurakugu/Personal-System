import { ElMessage } from 'element-plus'
import { getApiErrorMessage } from '../../../utils/api'
import type {
  列表重命名草稿,
  右侧新建文件夹草稿,
  新建目录草稿,
  资源展示项,
  资源标识,
  重命名目录草稿,
} from './files-explorer.shared'

interface 聚焦现有编辑输入参数 {
  当前目录ID: string | null
  当前可在右侧新建文件夹: boolean
  当前展示资源列表: 资源展示项[]
  右侧新建文件夹草稿: 右侧新建文件夹草稿 | null
  新建目录草稿: 新建目录草稿 | null
  重命名目录草稿: 重命名目录草稿 | null
  列表重命名草稿: 列表重命名草稿 | null
  聚焦右侧新建文件夹输入框: () => Promise<void>
  聚焦新建目录输入框: () => Promise<void>
  聚焦重命名目录输入框: () => Promise<void>
  聚焦列表重命名输入框: () => Promise<void>
  取消右侧新建文件夹: () => void
  取消列表重命名: () => void
}

interface 保存文件夹创建草稿参数<TDraft extends { name: string, parentId: string | null }> {
  草稿: TDraft | null
  正在提交: boolean
  设置正在提交: (value: boolean) => void
  取消编辑: () => void
  清空草稿: () => void
  创建文件夹: (name: string, parentId: string | null) => Promise<unknown>
  刷新当前视图: () => Promise<void>
  重新聚焦输入框: () => Promise<void>
}

interface 保存资源重命名草稿参数<TDraft extends { id: string, name: string, originalName: string }> {
  草稿: TDraft | null
  正在提交: boolean
  设置正在提交: (value: boolean) => void
  取消编辑: () => void
  清空草稿: () => void
  获取资源类型: (draft: TDraft) => 资源标识['type']
  获取成功文案: (draft: TDraft) => string
  获取失败文案: (draft: TDraft) => string
  重命名资源: (resource: 资源标识, name: string) => Promise<unknown>
  刷新当前视图: () => Promise<void>
  重新聚焦输入框: () => Promise<void>
}

export async function 尝试聚焦现有编辑输入框({
  当前目录ID,
  当前可在右侧新建文件夹,
  当前展示资源列表,
  右侧新建文件夹草稿,
  新建目录草稿,
  重命名目录草稿,
  列表重命名草稿,
  聚焦右侧新建文件夹输入框,
  聚焦新建目录输入框,
  聚焦重命名目录输入框,
  聚焦列表重命名输入框,
  取消右侧新建文件夹,
  取消列表重命名,
}: 聚焦现有编辑输入参数) {
  if (右侧新建文件夹草稿) {
    if (当前可在右侧新建文件夹 && 右侧新建文件夹草稿.parentId === 当前目录ID) {
      await 聚焦右侧新建文件夹输入框()
      return true
    }
    取消右侧新建文件夹()
  }

  if (新建目录草稿) {
    await 聚焦新建目录输入框()
    return true
  }

  if (重命名目录草稿) {
    await 聚焦重命名目录输入框()
    return true
  }

  if (列表重命名草稿) {
    const 当前资源仍可见 = 当前展示资源列表.some((resource) => (
      resource.id === 列表重命名草稿.id && resource.type === 列表重命名草稿.type
    ))
    if (当前资源仍可见) {
      await 聚焦列表重命名输入框()
      return true
    }
    取消列表重命名()
  }

  return false
}

export async function 保存文件夹创建草稿<TDraft extends { name: string, parentId: string | null }>({
  草稿,
  正在提交,
  设置正在提交,
  取消编辑,
  清空草稿,
  创建文件夹,
  刷新当前视图,
  重新聚焦输入框,
}: 保存文件夹创建草稿参数<TDraft>) {
  if (!草稿 || 正在提交) {
    return
  }

  const name = 草稿.name.trim()
  if (!name) {
    取消编辑()
    return
  }

  设置正在提交(true)
  try {
    await 创建文件夹(name, 草稿.parentId)
    清空草稿()
    ElMessage.success('文件夹已创建')
    await 刷新当前视图()
  } catch (error) {
    设置正在提交(false)
    ElMessage.error(getApiErrorMessage(error, '创建文件夹失败'))
    await 重新聚焦输入框()
    return
  }

  设置正在提交(false)
}

export async function 保存资源重命名草稿<TDraft extends { id: string, name: string, originalName: string }>({
  草稿,
  正在提交,
  设置正在提交,
  取消编辑,
  清空草稿,
  获取资源类型,
  获取成功文案,
  获取失败文案,
  重命名资源,
  刷新当前视图,
  重新聚焦输入框,
}: 保存资源重命名草稿参数<TDraft>) {
  if (!草稿 || 正在提交) {
    return
  }

  const name = 草稿.name.trim()
  if (!name || name === 草稿.originalName.trim()) {
    取消编辑()
    return
  }

  设置正在提交(true)
  try {
    await 重命名资源({ type: 获取资源类型(草稿), id: 草稿.id }, name)
    清空草稿()
    ElMessage.success(获取成功文案(草稿))
    await 刷新当前视图()
  } catch (error) {
    设置正在提交(false)
    ElMessage.error(getApiErrorMessage(error, 获取失败文案(草稿)))
    await 重新聚焦输入框()
    return
  }

  设置正在提交(false)
}
