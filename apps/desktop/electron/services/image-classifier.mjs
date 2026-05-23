import { execFile, spawn } from 'node:child_process'
import fs from 'node:fs/promises'
import os from 'node:os'
import path from 'node:path'
import process from 'node:process'
import readline from 'node:readline'

import {
  IMAGE_CLASSIFIER_STOP_ENV_KEY,
  IMAGE_CLASSIFIER_STOP_MESSAGE,
} from '../shared/constants.mjs'
import {
  normalizeStringArray,
  requireTrimmedString,
} from '../shared/request-utils.mjs'
import {
  commandWorks,
  createPythonCommandArgs,
  formatPythonCommand,
  resolveImageClassifierPaths,
  resolvePythonCommand,
} from './python-runtime.mjs'

let imageClassifierTask = null

function appendImageClassifierBackendArgs(args, request) {
  const backend = request?.backend?.trim() || 'mock'
  args.push('--backend', backend)

  const baseUrl = request?.baseUrl?.trim()
  if (baseUrl) {
    args.push('--base-url', baseUrl)
  }

  const model = request?.model?.trim()
  if (model) {
    args.push('--model', model)
  }

  const apiKey = request?.apiKey?.trim()
  if (apiKey) {
    args.push('--api-key', apiKey)
  }
}

function buildImageClassifierRunArgs(subcommand, request, entryScript, pythonCommand) {
  const args = createPythonCommandArgs(entryScript, pythonCommand, subcommand)
  args.push(...request.inputs)

  if (!request.recursive) {
    args.push('--no-recursive')
  }

  appendImageClassifierBackendArgs(args, request)
  args.push('--video-frame-count', String(request.videoFrameCount ?? 5))

  if (request.failOnEmpty) {
    args.push('--fail-on-empty')
  }

  return args
}

function buildImageClassifierDiscoverArgs(request, entryScript, pythonCommand) {
  const args = createPythonCommandArgs(entryScript, pythonCommand, 'discover-json')
  args.push(...request.inputs)

  if (!request.recursive) {
    args.push('--no-recursive')
  }

  return args
}

function buildImageClassifierActionArgs(request, entryScript, pythonCommand) {
  const args = createPythonCommandArgs(entryScript, pythonCommand, 'action-json')
  args.push('--action', request.action)
  appendImageClassifierBackendArgs(args, request)

  if (typeof request.shouldLoad === 'boolean') {
    args.push('--should-load', request.shouldLoad ? 'true' : 'false')
  }

  return args
}

function buildImageClassifierResultActionArgs(request, payloadFile, entryScript, pythonCommand) {
  return [
    ...createPythonCommandArgs(entryScript, pythonCommand, 'result-action-json'),
    '--action',
    request.action,
    '--payload-file',
    payloadFile,
    '--output-path',
    request.outputPath,
  ]
}

function parseImageClassifierError(stderr, fallbackMessage) {
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

function assertNoRunningImageClassifierTask() {
  if (imageClassifierTask?.child && imageClassifierTask.child.exitCode === null) {
    throw new Error('已有图片分类任务在运行中。')
  }
}

function setRunningImageClassifierTask(task) {
  imageClassifierTask = task
}

function clearRunningImageClassifierTask(task) {
  if (imageClassifierTask === task) {
    imageClassifierTask = null
  }
}

function terminateProcessTree(pid) {
  return new Promise((resolve, reject) => {
    const child = process.platform === 'win32'
      ? execFile('taskkill', ['/PID', String(pid), '/T', '/F'], callback)
      : execFile('kill', ['-TERM', String(pid)], callback)

    function callback(error, _stdout, stderr) {
      if (!error) {
        resolve()
        return
      }

      const message = stderr?.trim() || error.message
      reject(new Error(message || '停止图片分类任务失败。'))
    }

    return child
  })
}

function createTempImageClassifierPayloadFile(payload) {
  const payloadPath = path.join(
    os.tmpdir(),
    `personal-system-image-classifier-${Date.now()}-${Math.random().toString(16).slice(2)}.json`,
  )

  return fs.writeFile(payloadPath, JSON.stringify(payload), 'utf8').then(() => payloadPath)
}

async function runImageClassifierJsonCommand(args, errorPrefix) {
  const pythonCommand = resolvePythonCommand()
  const { classifierDir } = resolveImageClassifierPaths()

  return await new Promise((resolve, reject) => {
    execFile(
      pythonCommand.program,
      [...pythonCommand.leadingArgs, ...args],
      { cwd: classifierDir },
      (error, stdout, stderr) => {
        if (error) {
          reject(new Error(parseImageClassifierError(stderr, `${errorPrefix}。`)))
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

function createImageClassifierChild(args, classifierDir, pythonCommand) {
  return spawn(
    pythonCommand.program,
    [...pythonCommand.leadingArgs, ...args],
    {
      cwd: classifierDir,
      env: {
        ...process.env,
        [IMAGE_CLASSIFIER_STOP_ENV_KEY]: '0',
      },
      stdio: ['ignore', 'pipe', 'pipe'],
    },
  )
}

async function runImageClassifier(request) {
  const normalizedInputs = normalizeStringArray(request?.inputs)
  if (!normalizedInputs.length) {
    throw new Error('至少需要传入一个文件或目录路径。')
  }

  assertNoRunningImageClassifierTask()

  const pythonCommand = resolvePythonCommand()
  const { classifierDir, entryScript } = resolveImageClassifierPaths()
  const args = buildImageClassifierRunArgs('desktop-json', { ...request, inputs: normalizedInputs }, entryScript, pythonCommand)
  const child = createImageClassifierChild(args, classifierDir, pythonCommand)
  const task = {
    child,
    cancelled: false,
  }

  setRunningImageClassifierTask(task)

  return await new Promise((resolve, reject) => {
    let stdout = ''
    let stderr = ''

    child.stdout?.setEncoding('utf8')
    child.stderr?.setEncoding('utf8')
    child.stdout?.on('data', (chunk) => {
      stdout += chunk
    })
    child.stderr?.on('data', (chunk) => {
      stderr += chunk
    })
    child.once('error', (error) => {
      clearRunningImageClassifierTask(task)
      reject(new Error(`启动图片分类任务失败：${error.message}`))
    })
    child.once('close', (code) => {
      clearRunningImageClassifierTask(task)

      if (task.cancelled) {
        reject(new Error(IMAGE_CLASSIFIER_STOP_MESSAGE))
        return
      }

      if (code !== 0) {
        reject(new Error(parseImageClassifierError(stderr, `图片分类任务执行失败，退出码：${code ?? '未知'}`)))
        return
      }

      try {
        resolve(JSON.parse(stdout.trim()))
      } catch (parseError) {
        reject(new Error(`图片分类结果 JSON 解析失败：${parseError instanceof Error ? parseError.message : String(parseError)}`))
      }
    })
  })
}

async function runImageClassifierStream(event, request) {
  const normalizedInputs = normalizeStringArray(request?.inputs)
  if (!normalizedInputs.length) {
    throw new Error('至少需要传入一个文件或目录路径。')
  }

  const eventChannel = requireTrimmedString(request?.eventChannel, '缺少图片分类进度事件通道。')

  assertNoRunningImageClassifierTask()

  const pythonCommand = resolvePythonCommand()
  const { classifierDir, entryScript } = resolveImageClassifierPaths()
  const args = buildImageClassifierRunArgs('desktop-stream-json', { ...request, inputs: normalizedInputs }, entryScript, pythonCommand)
  const child = createImageClassifierChild(args, classifierDir, pythonCommand)
  const task = {
    child,
    cancelled: false,
  }

  setRunningImageClassifierTask(task)

  return await new Promise((resolve, reject) => {
    let stderr = ''
    let settled = false
    let stdoutReadError = null
    const stdoutReader = readline.createInterface({ input: child.stdout })

    child.stderr?.setEncoding('utf8')
    child.stderr?.on('data', (chunk) => {
      stderr += chunk
    })

    stdoutReader.on('line', (line) => {
      const trimmed = line.trim()
      if (!trimmed || settled) {
        return
      }

      try {
        const payload = JSON.parse(trimmed)
        event.sender.send(eventChannel, payload)
      } catch (error) {
        stdoutReadError = new Error(`解析图片分类进度事件失败：${error instanceof Error ? error.message : String(error)}`)
        task.cancelled = true
        void terminateProcessTree(child.pid).catch(() => {})
      }
    })

    stdoutReader.once('error', (error) => {
      stdoutReadError = new Error(`读取图片分类进度失败：${error.message}`)
      task.cancelled = true
      void terminateProcessTree(child.pid).catch(() => {})
    })

    child.once('error', (error) => {
      settled = true
      stdoutReader.close()
      clearRunningImageClassifierTask(task)
      reject(new Error(`启动图片分类任务失败：${error.message}`))
    })

    child.once('close', (code) => {
      settled = true
      stdoutReader.close()
      clearRunningImageClassifierTask(task)

      if (stdoutReadError) {
        reject(stdoutReadError)
        return
      }

      if (task.cancelled) {
        reject(new Error(IMAGE_CLASSIFIER_STOP_MESSAGE))
        return
      }

      if (code !== 0) {
        reject(new Error(parseImageClassifierError(stderr, `图片分类任务执行失败，退出码：${code ?? '未知'}`)))
        return
      }

      resolve()
    })
  })
}

async function stopImageClassifier() {
  const task = imageClassifierTask
  if (!task?.child?.pid) {
    throw new Error('当前没有正在运行的图片分类任务。')
  }

  task.cancelled = true
  await terminateProcessTree(task.child.pid)
}

async function checkImageClassifierEnvironment() {
  const ffmpegAvailable = commandWorks('ffmpeg', ['-version'])
  const ffprobeAvailable = commandWorks('ffprobe', ['-version'])

  let workspaceRoot = null
  let classifierDir = null
  let entryScript = null
  let pythonCommand = null
  const missingDependencies = []

  try {
    const paths = resolveImageClassifierPaths()
    workspaceRoot = paths.workspaceRoot
    classifierDir = paths.classifierDir
    entryScript = paths.entryScript
  } catch (error) {
    missingDependencies.push(error instanceof Error ? error.message : String(error))
  }

  try {
    pythonCommand = formatPythonCommand(resolvePythonCommand())
  } catch (error) {
    missingDependencies.push(error instanceof Error ? error.message : String(error))
  }

  if (!ffmpegAvailable) {
    missingDependencies.push('ffmpeg')
  }
  if (!ffprobeAvailable) {
    missingDependencies.push('ffprobe')
  }

  return {
    available: missingDependencies.length === 0,
    workspaceRoot,
    classifierDir,
    entryScript,
    pythonCommand,
    pythonAvailable: Boolean(pythonCommand),
    ffmpegAvailable,
    ffprobeAvailable,
    missingDependencies,
    detail: missingDependencies.length === 0
      ? '图片分类运行环境检查通过。'
      : `图片分类运行环境不完整：${missingDependencies.join('；')}`,
  }
}

async function discoverImageClassifierInputs(request) {
  const normalizedInputs = normalizeStringArray(request?.inputs)
  if (!normalizedInputs.length) {
    return { inputs: [] }
  }

  const pythonCommand = resolvePythonCommand()
  const { entryScript } = resolveImageClassifierPaths()

  return await runImageClassifierJsonCommand(
    buildImageClassifierDiscoverArgs({ ...request, inputs: normalizedInputs }, entryScript, pythonCommand),
    '发现图片分类输入失败',
  )
}

async function runImageClassifierAction(request) {
  const pythonCommand = resolvePythonCommand()
  const { entryScript } = resolveImageClassifierPaths()

  return await runImageClassifierJsonCommand(
    buildImageClassifierActionArgs(request, entryScript, pythonCommand),
    '执行图片分类动作失败',
  )
}

async function runImageClassifierResultAction(request) {
  const normalizedOutputPath = requireTrimmedString(request?.outputPath, '输出路径不能为空。')

  const pythonCommand = resolvePythonCommand()
  const { entryScript } = resolveImageClassifierPaths()
  const payloadFile = await createTempImageClassifierPayloadFile({
    results: request?.payload?.results ?? [],
    skipped: request?.payload?.skipped ?? [],
  })

  try {
    return await runImageClassifierJsonCommand(
      buildImageClassifierResultActionArgs(
        { ...request, outputPath: normalizedOutputPath },
        payloadFile,
        entryScript,
        pythonCommand,
      ),
      '执行图片分类结果处理失败',
    )
  } finally {
    await fs.unlink(payloadFile).catch(() => {})
  }
}

export {
  checkImageClassifierEnvironment,
  discoverImageClassifierInputs,
  runImageClassifier,
  runImageClassifierAction,
  runImageClassifierResultAction,
  runImageClassifierStream,
  stopImageClassifier,
}
