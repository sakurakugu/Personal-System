import { Channel, invoke, isTauri } from '@tauri-apps/api/core'

export type 图片分类后端 = 'mock' | 'ollama' | 'openai_compatible'
export type 图片分类输入选择模式 = 'file' | 'folder'
export type 图片分类输出选择模式 = 'csv' | 'json' | 'folder'

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

export type 图片分类动作消息 = {
  message: string
}

export type 图片分类Ollama模型状态 = {
  loaded: boolean
}

export type 图片分类动作请求 = {
  action: 'test_connection' | 'start_ollama' | 'toggle_ollama_model' | 'get_ollama_model_state'
  backend?: 图片分类后端
  baseUrl?: string | null
  model?: string | null
  apiKey?: string | null
  shouldLoad?: boolean
}

export type 图片分类动作结果 = {
  message?: string | null
  loaded?: boolean | null
}

export type 图片分类结果处理动作 = 'export_csv' | 'export_json' | 'move_results'

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

export type 图片分类结果处理结果 = {
  message: string
  results?: 图片分类结果项[] | null
  skipped?: 图片分类跳过项[] | null
}

export type 图片分类进度事件 =
  | { type: 'started'; total: number }
  | { type: 'result'; completed: number; total: number; result: 图片分类结果项 }
  | { type: 'skipped'; completed: number; total: number; item: 图片分类跳过项 }
  | { type: 'completed'; summary: 图片分类结果摘要 }

function assertDesktopRuntime() {
  if (!isTauri()) {
    throw new Error('当前环境不支持本地图像分类')
  }
}

export async function 检查图片分类环境(): Promise<图片分类环境状态> {
  assertDesktopRuntime()
  return await invoke<图片分类环境状态>('check_image_classifier_environment')
}

export async function 选择图片分类输入(mode: 图片分类输入选择模式): Promise<string[]> {
  assertDesktopRuntime()
  return await invoke<string[]>('select_image_classifier_inputs', {
    request: { mode },
  })
}

export async function 选择图片分类输出路径(mode: 图片分类输出选择模式): Promise<string | null> {
  assertDesktopRuntime()
  return await invoke<string | null>('select_image_classifier_output_path', { mode })
}

export async function 发现图片分类输入(inputs: string[], recursive: boolean): Promise<string[]> {
  assertDesktopRuntime()
  if (!inputs.length) {
    return []
  }
  const result = await invoke<{ inputs: string[] }>('discover_image_classifier_inputs', {
    request: { inputs, recursive },
  })
  return result.inputs
}

export async function 停止图片分类(): Promise<void> {
  assertDesktopRuntime()
  await invoke('stop_image_classifier')
}

export async function 执行图片分类动作(request: 图片分类动作请求): Promise<图片分类动作结果> {
  assertDesktopRuntime()
  return await invoke<图片分类动作结果>('image_classifier_action', {
    request: {
      action: request.action,
      backend: request.backend ?? null,
      baseUrl: request.baseUrl?.trim() || null,
      model: request.model?.trim() || null,
      apiKey: request.apiKey?.trim() || null,
      shouldLoad: request.shouldLoad ?? null,
    },
  })
}

export async function 测试图片分类连接(request: {
  backend: 图片分类后端
  baseUrl?: string | null
  model?: string | null
  apiKey?: string | null
}): Promise<图片分类动作消息> {
  const result = await 执行图片分类动作({
    action: 'test_connection',
    backend: request.backend,
    baseUrl: request.baseUrl?.trim() || null,
    model: request.model?.trim() || null,
    apiKey: request.apiKey?.trim() || null,
  })
  return { message: result.message ?? '' }
}

export async function 启动图片分类Ollama(baseUrl: string): Promise<图片分类动作消息> {
  const result = await 执行图片分类动作({
    action: 'start_ollama',
    baseUrl: baseUrl.trim(),
  })
  return { message: result.message ?? '' }
}

export async function 切换图片分类Ollama模型(request: {
  baseUrl: string
  model: string
  shouldLoad: boolean
}): Promise<图片分类动作消息> {
  const result = await 执行图片分类动作({
    action: 'toggle_ollama_model',
    baseUrl: request.baseUrl.trim(),
    model: request.model.trim(),
    shouldLoad: request.shouldLoad,
  })
  return { message: result.message ?? '' }
}

export async function 获取图片分类Ollama模型状态(request: {
  baseUrl: string
  model: string
}): Promise<图片分类Ollama模型状态> {
  const result = await 执行图片分类动作({
    action: 'get_ollama_model_state',
    baseUrl: request.baseUrl.trim(),
    model: request.model.trim(),
  })
  return { loaded: Boolean(result.loaded) }
}

export async function 流式执行图片分类(
  request: 图片分类请求,
  onEvent: (event: 图片分类进度事件) => void,
): Promise<void> {
  assertDesktopRuntime()
  const onEventChannel = new Channel<图片分类进度事件>()
  onEventChannel.onmessage = onEvent
  await invoke('run_image_classifier_stream', {
    inputs: request.inputs,
    recursive: request.recursive ?? false,
    backend: request.backend ?? 'ollama',
    baseUrl: request.baseUrl?.trim() || null,
    model: request.model?.trim() || null,
    apiKey: request.apiKey?.trim() || null,
    videoFrameCount: request.videoFrameCount ?? 5,
    failOnEmpty: request.failOnEmpty ?? false,
    onEvent: onEventChannel,
  })
}

export async function 执行图片分类(request: 图片分类请求): Promise<图片分类结果> {
  assertDesktopRuntime()
  return await invoke<图片分类结果>('run_image_classifier', {
    request: {
      inputs: request.inputs,
      recursive: request.recursive ?? false,
      backend: request.backend ?? 'ollama',
      baseUrl: request.baseUrl?.trim() || null,
      model: request.model?.trim() || null,
      apiKey: request.apiKey?.trim() || null,
      videoFrameCount: request.videoFrameCount ?? 5,
      failOnEmpty: request.failOnEmpty ?? false,
    },
  })
}

export async function 执行图片分类结果处理(request: {
  action: 图片分类结果处理动作
  payload: Pick<图片分类结果, 'results' | 'skipped'>
  outputPath: string
}): Promise<图片分类结果处理结果> {
  assertDesktopRuntime()
  return await invoke<图片分类结果处理结果>('image_classifier_result_action', {
    request: {
      action: request.action,
      payload: {
        results: request.payload.results,
        skipped: request.payload.skipped,
      },
      outputPath: request.outputPath,
    },
  })
}
