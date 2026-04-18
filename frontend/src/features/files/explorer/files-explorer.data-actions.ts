import { ElMessage } from 'element-plus'
import {
  fetchExplorer,
  searchFiles as requestSearchFiles,
} from '../api'
import type { FileExplorerData, FileSearchData } from '../types'
import { getApiErrorMessage } from '../../../utils/api'

interface 应用资源数据参数 {
  data: FileExplorerData
  设置资源数据: (data: FileExplorerData) => void
  设置当前目录ID: (folderId: string | null) => void
  清空选择: () => void
}

interface 拉取资源参数 {
  folderId: string | null
  静默: boolean
  应用资源数据: (data: FileExplorerData) => void
  设置刷新中: (value: boolean) => void
  设置首次加载中: (value: boolean) => void
}

interface 重置全局搜索结果参数 {
  设置全局搜索中: (value: boolean) => void
  设置全局搜索结果: (data: FileSearchData) => void
}

interface 执行全局搜索参数 extends 重置全局搜索结果参数 {
  keyword: string
  requestId: number
  获取当前请求序号: () => number
}

interface 刷新当前视图参数 {
  folderId: string | null
  是否全局搜索模式: boolean
  keyword: string
  拉取资源: (folderId: string | null, options?: { 静默?: boolean }) => Promise<void>
  重置全局搜索结果: () => void
  设置全局搜索中: (value: boolean) => void
  创建全局搜索请求: () => number
  执行全局搜索: (keyword: string, requestId: number) => Promise<void>
}

export function 应用资源数据({
  data,
  设置资源数据,
  设置当前目录ID,
  清空选择,
}: 应用资源数据参数) {
  设置资源数据(data)
  设置当前目录ID(data.current_folder?.id ?? null)
  清空选择()
}

export async function 拉取资源数据({
  folderId,
  静默,
  应用资源数据,
  设置刷新中,
  设置首次加载中,
}: 拉取资源参数) {
  if (静默) {
    设置刷新中(true)
  } else {
    设置首次加载中(true)
  }

  try {
    const data = await fetchExplorer(folderId)
    应用资源数据(data)
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '加载资源失败'))
  } finally {
    if (静默) {
      设置刷新中(false)
    } else {
      设置首次加载中(false)
    }
  }
}

export function 重置全局搜索结果({
  设置全局搜索中,
  设置全局搜索结果,
}: 重置全局搜索结果参数) {
  设置全局搜索中(false)
  设置全局搜索结果({ folders: [], files: [] })
}

export async function 执行全局搜索({
  keyword,
  requestId,
  获取当前请求序号,
  设置全局搜索中,
  设置全局搜索结果,
}: 执行全局搜索参数) {
  try {
    const data = await requestSearchFiles(keyword)
    if (requestId !== 获取当前请求序号()) {
      return
    }
    设置全局搜索结果(data)
  } catch (error) {
    if (requestId !== 获取当前请求序号()) {
      return
    }
    重置全局搜索结果({
      设置全局搜索中,
      设置全局搜索结果,
    })
    ElMessage.error(getApiErrorMessage(error, '跨目录搜索失败'))
    return
  }

  if (requestId === 获取当前请求序号()) {
    设置全局搜索中(false)
  }
}

export async function 刷新当前视图数据({
  folderId,
  是否全局搜索模式,
  keyword,
  拉取资源,
  重置全局搜索结果,
  设置全局搜索中,
  创建全局搜索请求,
  执行全局搜索,
}: 刷新当前视图参数) {
  await 拉取资源(folderId, { 静默: true })
  if (!是否全局搜索模式) {
    return
  }

  const normalizedKeyword = keyword.trim()
  if (!normalizedKeyword) {
    重置全局搜索结果()
    return
  }

  const requestId = 创建全局搜索请求()
  设置全局搜索中(true)
  await 执行全局搜索(normalizedKeyword, requestId)
}
