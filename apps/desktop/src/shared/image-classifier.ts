import { invoke, isTauri } from '@tauri-apps/api/core'

export type 图片分类后端 = 'mock' | 'ollama' | 'openai_compatible'

export type 图片分类环境状态 = {
  available: boolean
  workspaceRoot: string | null
  classifierDir: string | null
  entryScript: string | null
  pythonCommand: string | null
  pythonAvailable: boolean
  ffmpegAvailable: boolean
  ffprobeAvailable: boolean
  missingDependencies: string[]
  detail: string
}

export type 图片分类请求 = {
  inputs: string[]
  recursive?: boolean
  backend?: 图片分类后端
  baseUrl?: string | null
  model?: string | null
  apiKey?: string | null
  videoFrameCount?: number
  failOnEmpty?: boolean
}

export type 图片分类结果摘要 = {
  total: number
  classified: number
  skipped: number
  durationMs: number
}

export type 图片分类结果项 = {
  path: string
  sourceKind: string
  label: string
  labelZh: string
  confidence: number
  reason: string
  rawResponse: string
}

export type 图片分类跳过项 = {
  path: string
  reason: string
}

export type 图片分类结果 = {
  summary: 图片分类结果摘要
  results: 图片分类结果项[]
  skipped: 图片分类跳过项[]
}

function assertDesktopRuntime() {
  if (!isTauri()) {
    throw new Error('当前环境不支持本地图像分类')
  }
}

export async function 检查图片分类环境(): Promise<图片分类环境状态> {
  assertDesktopRuntime()
  return await invoke<图片分类环境状态>('check_image_classifier_environment')
}

export async function 执行图片分类(request: 图片分类请求): Promise<图片分类结果> {
  assertDesktopRuntime()
  return await invoke<图片分类结果>('run_image_classifier', {
    request: {
      inputs: request.inputs,
      recursive: request.recursive ?? true,
      backend: request.backend ?? 'mock',
      baseUrl: request.baseUrl?.trim() || null,
      model: request.model?.trim() || null,
      apiKey: request.apiKey?.trim() || null,
      videoFrameCount: request.videoFrameCount ?? 5,
      failOnEmpty: request.failOnEmpty ?? false,
    },
  })
}
