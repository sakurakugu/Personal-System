import { ElMessage } from 'element-plus'
import { getApiErrorMessage } from '../../../shared/api'
import type { 上传执行结果 } from './files-explorer.upload'

interface 上传流程参数<TFile extends globalThis.File> {
  files: TFile[]
  关闭右键菜单: () => void
  设置正在上传: (value: boolean) => void
  执行上传: (files: TFile[]) => Promise<上传执行结果>
  获取成功提示: (successCount: number) => string
  获取失败提示: (failedCount: number) => string
  刷新当前视图: () => Promise<void>
}

export function 触发上传选择(input: globalThis.HTMLInputElement | null) {
  input?.click()
}

export function 读取并清空上传文件<TFile extends globalThis.File = globalThis.File>(event: globalThis.Event) {
  const input = event.target as globalThis.HTMLInputElement | null
  const files = Array.from(input?.files ?? []) as TFile[]
  if (input) {
    input.value = ''
  }
  return files
}

export async function 执行上传流程<TFile extends globalThis.File>({
  files,
  关闭右键菜单,
  设置正在上传,
  执行上传,
  获取成功提示,
  获取失败提示,
  刷新当前视图,
}: 上传流程参数<TFile>) {
  if (files.length === 0) {
    return
  }

  关闭右键菜单()
  设置正在上传(true)
  try {
    const result = await 执行上传(files)

    if (result.成功数量 > 0) {
      ElMessage.success(获取成功提示(result.成功数量))
    }
    if (result.失败原因.length > 0) {
      ElMessage.error(getApiErrorMessage(result.失败原因[0], 获取失败提示(result.失败原因.length)))
    }

    await 刷新当前视图()
  } finally {
    设置正在上传(false)
  }
}

