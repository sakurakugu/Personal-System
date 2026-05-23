import { execFile } from 'node:child_process'

import {
  isPlainObject,
  normalizeStringArray,
  requireTrimmedString,
} from '../shared/request-utils.mjs'
import { buildLocalFileUrl } from '../shared/dev-file-protocol.mjs'
import {
  createPythonCommandArgs,
  resolveImageToolsPaths,
  resolvePythonCommand,
} from './python-runtime.mjs'

function parseJsonCommandError(stderr, fallbackMessage) {
  const trimmed = stderr.trim()
  if (!trimmed) {
    return fallbackMessage
  }

  try {
    const parsed = JSON.parse(trimmed)
    if (parsed && typeof parsed === 'object' && typeof parsed.error === 'string' && parsed.error.trim()) {
      return parsed.error.trim()
    }
  } catch {
    // 保留原始错误文本
  }

  return trimmed
}

async function runImageToolsJsonCommand(args, errorPrefix) {
  const pythonCommand = resolvePythonCommand()
  const { toolDir } = resolveImageToolsPaths()

  return await new Promise((resolve, reject) => {
    execFile(
      pythonCommand.program,
      [...pythonCommand.leadingArgs, ...args],
      { cwd: toolDir },
      (error, stdout, stderr) => {
        if (error) {
          reject(new Error(parseJsonCommandError(stderr, `${errorPrefix}。`)))
          return
        }

        try {
          resolve(JSON.parse(stdout.trim()))
        } catch (parseError) {
          reject(new Error(`${errorPrefix}结果 JSON 解析失败：${parseError instanceof Error ? parseError.message : String(parseError)}`))
        }
      },
    )
  })
}

async function getImageToolCapabilities() {
  const pythonCommand = resolvePythonCommand()
  const { entryScript } = resolveImageToolsPaths()

  return await runImageToolsJsonCommand(
    createPythonCommandArgs(entryScript, pythonCommand, 'capabilities-json'),
    '获取桌面图片工具能力失败',
  )
}

async function buildPreviewUrl(previewPath) {
  return buildLocalFileUrl(previewPath)
}

async function importImagesFromPaths(paths) {
  const normalizedPaths = normalizeStringArray(paths)
  if (!normalizedPaths.length) {
    return []
  }

  const pythonCommand = resolvePythonCommand()
  const { entryScript } = resolveImageToolsPaths()
  const result = await runImageToolsJsonCommand(
    [...createPythonCommandArgs(entryScript, pythonCommand, 'import-json'), ...normalizedPaths],
    '导入桌面图片失败',
  )

  if (!Array.isArray(result)) {
    throw new Error('桌面图片工具返回了无效的导入结果。')
  }

  return await Promise.all(result.map(async (item) => ({
    ...item,
    预览地址: await buildPreviewUrl(item.预览地址),
  })))
}

async function convertImageResource(request) {
  const resourceId = requireTrimmedString(request?.resourceId, '桌面图片工具缺少资源标识。')
  const outputMimeType = requireTrimmedString(request?.output?.mimeType, '桌面图片工具缺少目标格式。')
  const outputPath = requireTrimmedString(request?.output?.outputPath, '桌面图片工具缺少输出路径。')

  const pythonCommand = resolvePythonCommand()
  const { entryScript } = resolveImageToolsPaths()
  const args = [
    ...createPythonCommandArgs(entryScript, pythonCommand, 'convert-json'),
    '--resource-id',
    resourceId,
    '--mime-type',
    outputMimeType,
    '--output-path',
    outputPath,
  ]

  if (typeof request?.output?.quality === 'number' && Number.isFinite(request.output.quality)) {
    args.push('--quality', String(request.output.quality))
  }

  return await runImageToolsJsonCommand(args, '桌面图片工具转换失败')
}

async function editImageResource(request) {
  const resourceId = requireTrimmedString(request?.resourceId, '桌面图片工具缺少编辑资源标识。')
  const editPayload = request?.edit
  const outputMimeType = requireTrimmedString(request?.output?.mimeType, '桌面图片工具缺少编辑目标格式。')
  const outputPath = requireTrimmedString(request?.output?.outputPath, '桌面图片工具缺少编辑输出路径。')

  if (!isPlainObject(editPayload)) {
    throw new Error('桌面图片工具缺少编辑参数。')
  }

  const pythonCommand = resolvePythonCommand()
  const { entryScript } = resolveImageToolsPaths()
  const args = [
    ...createPythonCommandArgs(entryScript, pythonCommand, 'edit-json'),
    '--resource-id',
    resourceId,
    '--mime-type',
    outputMimeType,
    '--output-path',
    outputPath,
    '--edit-json',
    JSON.stringify(editPayload),
  ]

  const quality = request?.output?.quality
  if (typeof quality === 'number' && Number.isFinite(quality)) {
    args.push('--quality', String(quality))
  }

  return await runImageToolsJsonCommand(args, '桌面图片工具编辑导出失败')
}

async function stitchImageResources(request) {
  const resourceIds = normalizeStringArray(request?.resourceIds)
  const stitchPayload = request?.stitch
  const outputMimeType = requireTrimmedString(request?.output?.mimeType, '桌面图片工具缺少拼接目标格式。')
  const outputPath = requireTrimmedString(request?.output?.outputPath, '桌面图片工具缺少拼接输出路径。')

  if (!resourceIds.length) {
    throw new Error('桌面图片工具缺少拼接资源列表。')
  }
  if (!isPlainObject(stitchPayload)) {
    throw new Error('桌面图片工具缺少拼接参数。')
  }

  const pythonCommand = resolvePythonCommand()
  const { entryScript } = resolveImageToolsPaths()
  const args = [
    ...createPythonCommandArgs(entryScript, pythonCommand, 'stitch-json'),
    '--resource-ids',
    ...resourceIds,
    '--mime-type',
    outputMimeType,
    '--output-path',
    outputPath,
    '--stitch-json',
    JSON.stringify(stitchPayload),
  ]

  const quality = request?.output?.quality
  if (typeof quality === 'number' && Number.isFinite(quality)) {
    args.push('--quality', String(quality))
  }

  return await runImageToolsJsonCommand(args, '桌面图片工具拼接导出失败')
}

async function releaseImageResources(resourceIds) {
  const normalizedResourceIds = normalizeStringArray(resourceIds)
  if (!normalizedResourceIds.length) {
    return
  }

  const pythonCommand = resolvePythonCommand()
  const { entryScript } = resolveImageToolsPaths()
  await runImageToolsJsonCommand(
    [...createPythonCommandArgs(entryScript, pythonCommand, 'release-json'), ...normalizedResourceIds],
    '释放桌面图片资源失败',
  )
}

export {
  convertImageResource,
  editImageResource,
  getImageToolCapabilities,
  importImagesFromPaths,
  releaseImageResources,
  stitchImageResources,
}
