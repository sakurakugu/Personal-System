import type { 资源标识 } from './files-explorer.shared'

export interface 文件资源标识 {
  type: 'file'
  id: string
}

export interface 文件夹资源标识 {
  type: 'folder'
  id: string
}

export interface 资源操作分组 {
  文件: 文件资源标识[]
  文件夹: 文件夹资源标识[]
}

export interface 批量操作汇总 {
  失败结果: PromiseRejectedResult[]
  成功数量: number
}

export function 拆分资源列表(source: 资源标识[]): 资源操作分组 {
  const 文件: 文件资源标识[] = []
  const 文件夹: 文件夹资源标识[] = []

  for (const item of source) {
    if (item.type === 'file') {
      文件.push({ type: 'file', id: item.id })
    } else {
      文件夹.push({ type: 'folder', id: item.id })
    }
  }

  return {
    文件,
    文件夹,
  }
}

export function 提取资源ID列表(source: 资源标识[]) {
  const grouped = 拆分资源列表(source)
  return {
    文件ID列表: grouped.文件.map((item) => item.id),
    文件夹ID列表: grouped.文件夹.map((item) => item.id),
  }
}

export function 汇总批量操作结果(results: PromiseSettledResult<unknown>[]): 批量操作汇总 {
  const 失败结果 = results.filter((result): result is PromiseRejectedResult => result.status === 'rejected')
  return {
    失败结果,
    成功数量: results.length - 失败结果.length,
  }
}
