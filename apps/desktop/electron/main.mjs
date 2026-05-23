import { app, BrowserWindow, dialog, ipcMain, Menu, screen } from 'electron'
import { execFile, spawn, spawnSync } from 'node:child_process'
import { existsSync } from 'node:fs'
import fs from 'node:fs/promises'
import os from 'node:os'
import path from 'node:path'
import process from 'node:process'
import readline from 'node:readline'
import { pathToFileURL } from 'node:url'

const isDev = !app.isPackaged
const appRoot = path.resolve(import.meta.dirname, '..')
const distDir = path.join(appRoot, 'dist')
const devServerUrl = 'http://localhost:5175'

let mainWindow = null
let widgetWindow = null
let imageClassifierTask = null
const WINDOW_STATE_EVENT_CHANNEL = 'desktop:window:state-changed'
const WIDGET_STATE_EVENT_CHANNEL = 'desktop:widget:state-changed'
const WIDGET_WINDOW_WIDTH = 380
const WIDGET_WINDOW_MIN_HEIGHT = 46
const DEFAULT_WIDGET_WINDOW_STATE = {
  alwaysOnTop: true,
  movable: false,
  surfaceOpacity: 100,
  showCloseButton: true,
}

const IMAGE_CLASSIFIER_STOP_MESSAGE = '图片分类已停止。'
const IMAGE_CLASSIFIER_RELATIVE_DIR = ['apps', 'desktop', 'python', 'ai-media-processor']
const IMAGE_CLASSIFIER_STOP_ENV_KEY = 'PERSONAL_SYSTEM_IMAGE_CLASSIFIER_STOP_REQUESTED'

const IMAGE_TOOLS_RELATIVE_DIR = ['apps', 'desktop', 'python', 'image-tools']
const MINECRAFT_TOOL_RELATIVE_DIR = ['apps', 'desktop', 'python', 'minecraft-tool']
const DESKTOP_PYTHON_RESOURCE_DIR = 'python'
const DESKTOP_EMBEDDED_PYTHON_DIR = 'python-runtime'
const DESKTOP_PYTHON_MODE_ENV_KEY = 'PERSONAL_SYSTEM_DESKTOP_PYTHON_MODE'
let cachedPythonCommand = null

const IMAGE_CLASSIFIER_MEDIA_EXTENSIONS = [
  '.png',
  '.jpg',
  '.jpeg',
  '.webp',
  '.bmp',
  '.gif',
  '.heic',
  '.heif',
  '.avif',
  '.mp4',
  '.mov',
  '.mkv',
  '.avi',
  '.webm',
  '.m4v',
]

function getDesktopAuthTokenPath() {
  return path.join(app.getPath('userData'), 'desktop-auth-token.txt')
}

function getWidgetConfigPath() {
  return path.join(app.getPath('userData'), 'desktop-widget', 'config.json')
}

function getWidgetWindowStatePath() {
  return path.join(app.getPath('userData'), 'desktop-widget', 'window-state.json')
}

function getMinecraftServerStoragePath() {
  return path.join(os.homedir(), '.personal-system', 'minecraft-tool.json')
}

function normalizeToken(token) {
  const normalized = token?.trim()
  return normalized ? normalized : null
}

async function loadDesktopAuthToken() {
  try {
    const content = await fs.readFile(getDesktopAuthTokenPath(), 'utf8')
    return normalizeToken(content)
  } catch (error) {
    if (error && typeof error === 'object' && 'code' in error && error.code === 'ENOENT') {
      return null
    }
    throw error
  }
}

async function saveDesktopAuthToken(token) {
  const normalized = normalizeToken(token)
  const tokenPath = getDesktopAuthTokenPath()

  if (!normalized) {
    try {
      await fs.unlink(tokenPath)
    } catch (error) {
      if (!(error && typeof error === 'object' && 'code' in error && error.code === 'ENOENT')) {
        throw error
      }
    }
    return
  }

  await fs.mkdir(path.dirname(tokenPath), { recursive: true })
  await fs.writeFile(tokenPath, `${normalized}\n`, 'utf8')
}

async function syncWidgetAuthToken(payload) {
  const normalizedToken = normalizeToken(payload.token)
  if (!normalizedToken) {
    throw new Error('小工具凭证不能为空')
  }

  const normalizedApiBaseUrl = payload.apiBaseUrl?.trim().replace(/\/+$/, '') || 'http://127.0.0.1:8000/api/v1'
  const normalizedWidgetName = payload.widgetName?.trim() || 'Personal System Widget'
  const configPath = getWidgetConfigPath()

  await fs.mkdir(path.dirname(configPath), { recursive: true })
  await fs.writeFile(configPath, `${JSON.stringify({
    api_base_url: normalizedApiBaseUrl,
    widget_name: normalizedWidgetName,
    token: normalizedToken,
  }, null, 2)}\n`, 'utf8')

  return configPath
}

async function readJsonFile(filePath, fallbackValue) {
  try {
    const content = await fs.readFile(filePath, 'utf8')
    return JSON.parse(content)
  } catch (error) {
    if (error && typeof error === 'object' && 'code' in error && error.code === 'ENOENT') {
      return fallbackValue
    }
    throw error
  }
}

async function writePrettyJson(filePath, payload) {
  await fs.mkdir(path.dirname(filePath), { recursive: true })
  await fs.writeFile(filePath, `${JSON.stringify(payload, null, 2)}\n`, 'utf8')
}

function normalizeWidgetWindowState(value) {
  const normalizedSurfaceOpacity = Number(value?.surfaceOpacity)
  const surfaceOpacity = Number.isFinite(normalizedSurfaceOpacity)
    ? Math.max(0, Math.min(100, Math.round(normalizedSurfaceOpacity)))
    : DEFAULT_WIDGET_WINDOW_STATE.surfaceOpacity
  return {
    alwaysOnTop: typeof value?.alwaysOnTop === 'boolean'
      ? value.alwaysOnTop
      : DEFAULT_WIDGET_WINDOW_STATE.alwaysOnTop,
    movable: typeof value?.movable === 'boolean'
      ? value.movable
      : DEFAULT_WIDGET_WINDOW_STATE.movable,
    surfaceOpacity,
    showCloseButton: typeof value?.showCloseButton === 'boolean'
      ? value.showCloseButton
      : DEFAULT_WIDGET_WINDOW_STATE.showCloseButton,
  }
}

let widgetWindowState = { ...DEFAULT_WIDGET_WINDOW_STATE }
let widgetWindowStateInitialized = false
let widgetWindowStatePromise = null

async function ensureWidgetWindowStateLoaded() {
  if (widgetWindowStateInitialized) {
    return widgetWindowState
  }

  if (!widgetWindowStatePromise) {
    widgetWindowStatePromise = (async () => {
      const payload = await readJsonFile(getWidgetWindowStatePath(), DEFAULT_WIDGET_WINDOW_STATE)
      widgetWindowState = normalizeWidgetWindowState(payload)
      widgetWindowStateInitialized = true
      return widgetWindowState
    })().finally(() => {
      widgetWindowStatePromise = null
    })
  }

  return await widgetWindowStatePromise
}

async function saveWidgetWindowState(nextState) {
  widgetWindowState = normalizeWidgetWindowState(nextState)
  widgetWindowStateInitialized = true
  await writePrettyJson(getWidgetWindowStatePath(), widgetWindowState)
  return widgetWindowState
}

function getCurrentWidgetWindowState() {
  if (widgetWindow && !widgetWindow.isDestroyed()) {
    return {
      open: true,
      alwaysOnTop: widgetWindow.isAlwaysOnTop(),
      movable: widgetWindow.isMovable(),
      surfaceOpacity: widgetWindowState.surfaceOpacity,
      showCloseButton: widgetWindowState.showCloseButton,
    }
  }

  return {
    open: false,
    alwaysOnTop: widgetWindowState.alwaysOnTop,
    movable: widgetWindowState.movable,
    surfaceOpacity: widgetWindowState.surfaceOpacity,
    showCloseButton: widgetWindowState.showCloseButton,
  }
}

function applyWidgetWindowState(window, nextState) {
  window.setAlwaysOnTop(nextState.alwaysOnTop)
  window.setMovable(nextState.movable)
}

function resizeWidgetWindowHeight(window, contentHeight) {
  if (!window || window.isDestroyed()) {
    return null
  }

  const bounds = window.getBounds()
  const display = screen.getDisplayMatching(bounds)
  const workAreaHeight = display.workArea.height
  const nextHeight = Math.max(WIDGET_WINDOW_MIN_HEIGHT, Math.min(Math.round(contentHeight), workAreaHeight - 32))
  const nextWidth = WIDGET_WINDOW_WIDTH
  const currentSize = window.getSize()

  if (Math.abs(currentSize[1] - nextHeight) <= 1 && currentSize[0] === nextWidth) {
    return nextHeight
  }

  window.setBounds({
    x: bounds.x,
    y: bounds.y,
    width: nextWidth,
    height: nextHeight,
  })

  return nextHeight
}

function normalizeMinecraftRecord(record) {
  const address = record?.address?.trim()
  if (!address) {
    return null
  }

  const edition = record?.edition === 'java' || record?.edition === 'bedrock'
    ? record.edition
    : 'auto'

  return { address, edition }
}

function normalizeMinecraftRecords(records, limit) {
  const output = []
  const keys = new Set()

  for (const record of Array.isArray(records) ? records : []) {
    const normalized = normalizeMinecraftRecord(record)
    if (!normalized) {
      continue
    }

    const key = `${normalized.edition}:${normalized.address}`
    if (keys.has(key)) {
      continue
    }

    keys.add(key)
    output.push(normalized)
    if (output.length >= limit) {
      break
    }
  }

  return output
}

async function readMinecraftServerStorage() {
  const data = await readJsonFile(getMinecraftServerStoragePath(), {
    favorites: [],
    history: [],
  })

  return {
    favorites: normalizeMinecraftRecords(data.favorites, 20),
    history: normalizeMinecraftRecords(data.history, 30),
  }
}

async function writeMinecraftServerStorage(data) {
  await writePrettyJson(getMinecraftServerStoragePath(), {
    favorites: normalizeMinecraftRecords(data?.favorites, 20),
    history: normalizeMinecraftRecords(data?.history, 30),
  })
}

function resolveWorkspaceRoot() {
  const candidates = [process.cwd(), appRoot, path.resolve(appRoot, '..', '..')]
  for (const candidate of candidates) {
    if (candidate) {
      const appsDesktopPath = path.join(candidate, 'apps', 'desktop')
      const packagesPath = path.join(candidate, 'packages')
      if (existsSync(appsDesktopPath) && existsSync(packagesPath)) {
        return candidate
      }
    }
  }
  throw new Error('未找到仓库根目录。')
}

function resolveDesktopPythonToolPaths(options) {
  const { relativeDir, packagedDirName, label } = options
  const candidates = []

  if (!app.isPackaged) {
    const workspaceRoot = resolveWorkspaceRoot()
    candidates.push({
      toolDir: path.join(workspaceRoot, ...relativeDir),
      workspaceRoot,
    })
  }

  candidates.push({
    toolDir: path.join(process.resourcesPath, DESKTOP_PYTHON_RESOURCE_DIR, packagedDirName),
    workspaceRoot: null,
  })

  candidates.push({
    toolDir: path.join(appRoot, DESKTOP_PYTHON_RESOURCE_DIR, packagedDirName),
    workspaceRoot: null,
  })

  for (const candidate of candidates) {
    const entryScript = path.join(candidate.toolDir, 'main.py')
    if (existsSync(candidate.toolDir) && existsSync(entryScript)) {
      return {
        workspaceRoot: candidate.workspaceRoot,
        toolDir: candidate.toolDir,
        entryScript,
      }
    }
  }

  const searchedPaths = candidates.map((item) => item.toolDir).join('；')
  throw new Error(`未找到${label}目录。已检查：${searchedPaths}`)
}

function resolveImageClassifierPaths() {
  const resolved = resolveDesktopPythonToolPaths({
    relativeDir: IMAGE_CLASSIFIER_RELATIVE_DIR,
    packagedDirName: 'ai-media-processor',
    label: '图片分类',
  })

  return {
    workspaceRoot: resolved.workspaceRoot,
    classifierDir: resolved.toolDir,
    entryScript: resolved.entryScript,
  }
}

function resolveImageToolsPaths() {
  return resolveDesktopPythonToolPaths({
    relativeDir: IMAGE_TOOLS_RELATIVE_DIR,
    packagedDirName: 'image-tools',
    label: '桌面图片工具',
  })
}

function resolveMinecraftToolPaths() {
  return resolveDesktopPythonToolPaths({
    relativeDir: MINECRAFT_TOOL_RELATIVE_DIR,
    packagedDirName: 'minecraft-tool',
    label: 'Minecraft 工具',
  })
}

function resolvePythonCommand() {
  if (cachedPythonCommand) {
    return cachedPythonCommand
  }

  const pythonMode = process.env[DESKTOP_PYTHON_MODE_ENV_KEY]?.trim() || 'auto'
  if (pythonMode === 'embedded') {
    const pythonCommand = resolveEmbeddedPythonCommand()
    console.log(`桌面端 Python 模式: embedded，使用 ${formatPythonCommand(pythonCommand)}`)
    cachedPythonCommand = pythonCommand
    return cachedPythonCommand
  }

  if (pythonMode === 'system') {
    const pythonCommand = resolveSystemPythonCommand()
    console.log(`桌面端 Python 模式: system，使用 ${formatPythonCommand(pythonCommand)}`)
    cachedPythonCommand = pythonCommand
    return cachedPythonCommand
  }

  const embeddedPythonCommand = resolveEmbeddedPythonCommand({ strict: false })
  if (embeddedPythonCommand) {
    console.log(`桌面端 Python 模式: auto，优先使用内置 Python ${formatPythonCommand(embeddedPythonCommand)}`)
    cachedPythonCommand = embeddedPythonCommand
    return cachedPythonCommand
  }

  const systemPythonCommand = resolveSystemPythonCommand()
  console.log(`桌面端 Python 模式: auto，未找到内置 Python，回退到系统 Python ${formatPythonCommand(systemPythonCommand)}`)
  cachedPythonCommand = systemPythonCommand
  return cachedPythonCommand
}

function resolveEmbeddedPythonCommand({ strict = true } = {}) {
  const candidates = [
    path.join(process.resourcesPath, DESKTOP_EMBEDDED_PYTHON_DIR, 'python', 'python.exe'),
    path.join(appRoot, DESKTOP_EMBEDDED_PYTHON_DIR, 'python', 'python.exe'),
  ]

  for (const candidate of candidates) {
    if (!existsSync(candidate)) {
      continue
    }

    const result = spawnSync(candidate, ['--version'], { encoding: 'utf8' })
    if (result.status === 0) {
      return { program: candidate, leadingArgs: [] }
    }
  }

  if (!strict) {
    return null
  }

  throw new Error(`桌面端已切换到 embedded Python 模式，但未找到内置 Python。请检查 ${DESKTOP_EMBEDDED_PYTHON_DIR} 目录。`)
}

function resolveSystemPythonCommand() {
  const candidates = [
    { program: 'python', leadingArgs: [] },
    { program: 'python3', leadingArgs: [] },
    { program: 'py', leadingArgs: ['-3'] },
  ]

  for (const candidate of candidates) {
    const result = spawnSync(candidate.program, [...candidate.leadingArgs, '--version'], { encoding: 'utf8' })
    if (result.status === 0) {
      return candidate
    }
  }

  throw new Error('未找到可用的 Python 3 命令。')
}

function commandWorks(program, args) {
  const result = spawnSync(program, args, { encoding: 'utf8' })
  return result.status === 0
}

function formatPythonCommand(pythonCommand) {
  return pythonCommand.leadingArgs.length
    ? `${pythonCommand.program} ${pythonCommand.leadingArgs.join(' ')}`
    : pythonCommand.program
}

function createPythonCommandArgs(entryScript, pythonCommand, subcommand) {
  void pythonCommand
  return [entryScript, subcommand]
}

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
  if (!Array.isArray(request?.inputs) || request.inputs.length === 0) {
    throw new Error('至少需要传入一个文件或目录路径。')
  }

  assertNoRunningImageClassifierTask()

  const pythonCommand = resolvePythonCommand()
  const { classifierDir, entryScript } = resolveImageClassifierPaths()
  const args = buildImageClassifierRunArgs('desktop-json', request, entryScript, pythonCommand)
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
  if (!Array.isArray(request?.inputs) || request.inputs.length === 0) {
    throw new Error('至少需要传入一个文件或目录路径。')
  }

  const eventChannel = request?.eventChannel?.trim()
  if (!eventChannel) {
    throw new Error('缺少图片分类进度事件通道。')
  }

  assertNoRunningImageClassifierTask()

  const pythonCommand = resolvePythonCommand()
  const { classifierDir, entryScript } = resolveImageClassifierPaths()
  const args = buildImageClassifierRunArgs('desktop-stream-json', request, entryScript, pythonCommand)
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

async function queryMinecraftServer(request) {
  const address = request?.address?.trim()
  if (!address) {
    throw new Error('服务器地址不能为空。')
  }

  const { toolDir: queryDir, entryScript } = resolveMinecraftToolPaths()
  const pythonCommand = resolvePythonCommand()
  const edition = request?.edition === 'java' || request?.edition === 'bedrock' ? request.edition : 'auto'
  const timeout = request?.timeout ?? 3

  return await new Promise((resolve, reject) => {
    execFile(
      pythonCommand.program,
      [
        ...pythonCommand.leadingArgs,
        entryScript,
        'query-json',
        address,
        '--edition',
        edition,
        '--timeout',
        String(timeout),
      ],
      {
        cwd: queryDir,
      },
      (error, stdout, stderr) => {
        if (error) {
          reject(new Error(stderr.trim() || error.message))
          return
        }

        try {
          resolve(JSON.parse(stdout.trim()))
        } catch (parseError) {
          reject(parseError)
        }
      },
    )
  })
}

function resolveRendererUrl(relativePath = '/') {
  if (isDev) {
    return new URL(relativePath, `${devServerUrl}/`).toString()
  }
  return path.join(distDir, relativePath === '/' ? 'index.html' : relativePath)
}

function isWidgetWindowOpen() {
  return Boolean(widgetWindow && !widgetWindow.isDestroyed())
}

function emitWidgetWindowState() {
  const payload = getCurrentWidgetWindowState()

  for (const window of BrowserWindow.getAllWindows()) {
    if (!window.isDestroyed()) {
      window.webContents.send(WIDGET_STATE_EVENT_CHANNEL, payload)
    }
  }
}

async function loadWindow(window, relativePath = '/') {
  if (isDev) {
    await window.loadURL(resolveRendererUrl(relativePath))
    return
  }

  await window.loadFile(resolveRendererUrl(relativePath))
}

function createMainWindow() {
  if (mainWindow && !mainWindow.isDestroyed()) {
    return mainWindow
  }

  mainWindow = new BrowserWindow({
    width: 1280,
    height: 860,
    minWidth: 960,
    minHeight: 680,
    frame: false,
    show: false,
    webPreferences: {
      preload: path.join(import.meta.dirname, 'preload.mjs'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
    },
  })

  mainWindow.once('ready-to-show', () => {
    console.log('桌面端主窗口已就绪')
    mainWindow?.show()
  })

  mainWindow.on('closed', () => {
    mainWindow = null
  })

  const emitWindowState = () => {
    if (!mainWindow || mainWindow.isDestroyed()) {
      return
    }

    mainWindow.webContents.send(WINDOW_STATE_EVENT_CHANNEL, {
      maximized: mainWindow.isMaximized(),
    })
  }

  mainWindow.on('maximize', emitWindowState)
  mainWindow.on('unmaximize', emitWindowState)
  mainWindow.on('enter-full-screen', emitWindowState)
  mainWindow.on('leave-full-screen', emitWindowState)

  void loadWindow(mainWindow, '/')

  return mainWindow
}

function createWidgetWindow() {
  if (widgetWindow && !widgetWindow.isDestroyed()) {
    return widgetWindow
  }

  widgetWindow = new BrowserWindow({
    width: WIDGET_WINDOW_WIDTH,
    height: 620,
    minWidth: WIDGET_WINDOW_WIDTH,
    maxWidth: WIDGET_WINDOW_WIDTH,
    minHeight: WIDGET_WINDOW_MIN_HEIGHT,
    resizable: false,
    frame: false,
    transparent: true,
    backgroundColor: '#00000000',
    alwaysOnTop: widgetWindowState.alwaysOnTop,
    movable: widgetWindowState.movable,
    skipTaskbar: true,
    show: false,
    webPreferences: {
      preload: path.join(import.meta.dirname, 'preload.mjs'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
    },
  })

  applyWidgetWindowState(widgetWindow, widgetWindowState)

  widgetWindow.once('ready-to-show', () => {
    widgetWindow?.show()
    emitWidgetWindowState()
  })

  widgetWindow.on('closed', () => {
    widgetWindow = null
    emitWidgetWindowState()
  })

  void loadWindow(widgetWindow, '/widget.html')

  return widgetWindow
}

function showAndFocus(window) {
  if (window.isMinimized()) {
    window.restore()
  }
  window.show()
  window.focus()
  return window
}

ipcMain.handle('desktop:window:open-main', async () => {
  const window = showAndFocus(createMainWindow())
  return window.id
})

ipcMain.handle('desktop:window:open-widget', async () => {
  await ensureWidgetWindowStateLoaded()
  const window = showAndFocus(createWidgetWindow())
  emitWidgetWindowState()
  return window.id
})

ipcMain.handle('desktop:window:close-widget', async () => {
  if (!widgetWindow || widgetWindow.isDestroyed()) {
    emitWidgetWindowState()
    return false
  }
  widgetWindow.close()
  return true
})

ipcMain.handle('desktop:window:close-current', async (event) => {
  const targetWindow = BrowserWindow.fromWebContents(event.sender)
  if (!targetWindow || targetWindow.isDestroyed()) {
    return
  }
  targetWindow.close()
})

ipcMain.handle('desktop:window:minimize-current', async (event) => {
  const targetWindow = BrowserWindow.fromWebContents(event.sender)
  if (!targetWindow || targetWindow.isDestroyed()) {
    return
  }
  targetWindow.minimize()
})

ipcMain.handle('desktop:window:toggle-maximize-current', async (event) => {
  const targetWindow = BrowserWindow.fromWebContents(event.sender)
  if (!targetWindow || targetWindow.isDestroyed()) {
    return { maximized: false }
  }

  if (targetWindow.isMaximized()) {
    targetWindow.unmaximize()
  } else {
    targetWindow.maximize()
  }

  return {
    maximized: targetWindow.isMaximized(),
  }
})

ipcMain.handle('desktop:window:get-current-state', async (event) => {
  const targetWindow = BrowserWindow.fromWebContents(event.sender)
  if (!targetWindow || targetWindow.isDestroyed()) {
    return {
      maximized: false,
    }
  }

  return {
    maximized: targetWindow.isMaximized(),
  }
})

ipcMain.handle('desktop:widget:get-state', async () => {
  await ensureWidgetWindowStateLoaded()
  return getCurrentWidgetWindowState()
})

ipcMain.handle('desktop:widget:set-state', async (_event, payload) => {
  const currentState = await ensureWidgetWindowStateLoaded()
  const nextState = await saveWidgetWindowState({
    ...currentState,
    ...payload,
  })

  if (widgetWindow && !widgetWindow.isDestroyed()) {
    applyWidgetWindowState(widgetWindow, nextState)
  }

  emitWidgetWindowState()
  return getCurrentWidgetWindowState()
})

ipcMain.handle('desktop:widget:set-content-height', async (_event, height) => {
  if (!widgetWindow || widgetWindow.isDestroyed()) {
    return null
  }

  if (typeof height !== 'number' || !Number.isFinite(height)) {
    return widgetWindow.getBounds().height
  }

  return resizeWidgetWindowHeight(widgetWindow, height)
})

ipcMain.handle('desktop:auth:load-token', async () => {
  return await loadDesktopAuthToken()
})

ipcMain.handle('desktop:auth:save-token', async (_event, token) => {
  await saveDesktopAuthToken(token)
})

ipcMain.handle('desktop:widget:sync-token', async (_event, payload) => {
  return await syncWidgetAuthToken(payload)
})

ipcMain.handle('desktop:windows:check-git', async () => {
  try {
    const { execFile } = await import('node:child_process')
    const result = await new Promise((resolve) => {
      execFile('git', ['--version'], (error, stdout, stderr) => {
        if (error) {
          resolve({
            installed: false,
            version: null,
            detail: `未找到 Git 命令：${error.message}`,
          })
          return
        }

        const version = stdout.trim()
        resolve({
          installed: true,
          version: version || null,
          detail: version ? `已检测到 Git：${version}` : stderr.trim() || 'Git 环境检查完成',
        })
      })
    })
    return result
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error)
    return {
      installed: false,
      version: null,
      detail: `Git 环境检查失败：${message}`,
    }
  }
})

ipcMain.handle('desktop:minecraft:read-storage', async () => {
  return await readMinecraftServerStorage()
})

ipcMain.handle('desktop:minecraft:write-storage', async (_event, data) => {
  await writeMinecraftServerStorage(data)
})

ipcMain.handle('desktop:minecraft:query', async (_event, request) => {
  return await queryMinecraftServer(request)
})

ipcMain.handle('desktop:file:to-url', async (_event, filePath) => {
  return pathToFileURL(filePath).toString()
})

ipcMain.handle('desktop:image-tools:get-capabilities', async () => {
  const pythonCommand = resolvePythonCommand()
  const { entryScript } = resolveImageToolsPaths()
  return await runImageToolsJsonCommand(
    createPythonCommandArgs(entryScript, pythonCommand, 'capabilities-json'),
    '获取桌面图片工具能力失败',
  )
})

ipcMain.handle('desktop:image-tools:select-inputs', async () => {
  const result = await dialog.showOpenDialog({
    title: '选择图片文件',
    properties: ['openFile', 'multiSelections'],
    filters: [
      {
        name: 'Images',
        extensions: ['png', 'jpg', 'jpeg', 'webp', 'avif', 'bmp', 'gif', 'heic', 'heif', 'tif', 'tiff', 'ico', 'psd'],
      },
    ],
  })
  return result.canceled ? [] : result.filePaths
})

ipcMain.handle('desktop:image-tools:select-output-path', async (_event, mode, options) => {
  if (mode === 'file') {
    const result = await dialog.showSaveDialog({
      title: '选择图片输出路径',
      defaultPath: options?.defaultName?.trim() || 'image.png',
      filters: Array.isArray(options?.filters) ? options.filters : undefined,
    })
    return result.canceled ? null : result.filePath ?? null
  }

  if (mode === 'folder') {
    const result = await dialog.showOpenDialog({
      title: '选择输出文件夹',
      properties: ['openDirectory', 'createDirectory'],
    })
    return result.canceled ? null : result.filePaths[0] ?? null
  }

  throw new Error('不支持的图片工具输出选择模式。')
})

ipcMain.handle('desktop:image-tools:import-from-paths', async (_event, paths) => {
  if (!Array.isArray(paths) || paths.length === 0) {
    return []
  }

  const normalizedPaths = paths
    .map((item) => typeof item === 'string' ? item.trim() : '')
    .filter(Boolean)

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

  return result.map((item) => ({
    ...item,
    预览地址: pathToFileURL(item.预览地址).toString(),
  }))
})

ipcMain.handle('desktop:image-tools:convert', async (_event, request) => {
  const resourceId = request?.resourceId?.trim()
  const outputMimeType = request?.output?.mimeType?.trim()
  const outputPath = request?.output?.outputPath?.trim()

  if (!resourceId) {
    throw new Error('桌面图片工具缺少资源标识。')
  }
  if (!outputMimeType) {
    throw new Error('桌面图片工具缺少目标格式。')
  }
  if (!outputPath) {
    throw new Error('桌面图片工具缺少输出路径。')
  }

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

  return await runImageToolsJsonCommand(
    args,
    '桌面图片工具转换失败',
  )
})

ipcMain.handle('desktop:image-tools:edit', async (_event, request) => {
  const resourceId = request?.resourceId?.trim() ?? ''
  const editPayload = request?.edit
  const outputMimeType = request?.output?.mimeType?.trim() ?? ''
  const outputPath = request?.output?.outputPath?.trim() ?? ''

  if (!resourceId) {
    throw new Error('桌面图片工具缺少编辑资源标识。')
  }
  if (!editPayload || typeof editPayload !== 'object') {
    throw new Error('桌面图片工具缺少编辑参数。')
  }
  if (!outputMimeType) {
    throw new Error('桌面图片工具缺少编辑目标格式。')
  }
  if (!outputPath) {
    throw new Error('桌面图片工具缺少编辑输出路径。')
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

  return await runImageToolsJsonCommand(
    args,
    '桌面图片工具编辑导出失败',
  )
})

ipcMain.handle('desktop:image-tools:stitch', async (_event, request) => {
  const resourceIds = Array.isArray(request?.resourceIds)
    ? request.resourceIds.map((item) => typeof item === 'string' ? item.trim() : '').filter(Boolean)
    : []
  const stitchPayload = request?.stitch
  const outputMimeType = request?.output?.mimeType?.trim?.() ?? ''
  const outputPath = request?.output?.outputPath?.trim?.() ?? ''

  if (!resourceIds.length) {
    throw new Error('桌面图片工具缺少拼接资源列表。')
  }
  if (!stitchPayload || typeof stitchPayload !== 'object') {
    throw new Error('桌面图片工具缺少拼接参数。')
  }
  if (!outputMimeType) {
    throw new Error('桌面图片工具缺少拼接目标格式。')
  }
  if (!outputPath) {
    throw new Error('桌面图片工具缺少拼接输出路径。')
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

  return await runImageToolsJsonCommand(
    args,
    '桌面图片工具拼接导出失败',
  )
})

ipcMain.handle('desktop:image-tools:release', async (_event, resourceIds) => {
  if (!Array.isArray(resourceIds) || resourceIds.length === 0) {
    return
  }

  const normalizedResourceIds = resourceIds
    .map((item) => typeof item === 'string' ? item.trim() : '')
    .filter(Boolean)

  if (!normalizedResourceIds.length) {
    return
  }

  const pythonCommand = resolvePythonCommand()
  const { entryScript } = resolveImageToolsPaths()
  await runImageToolsJsonCommand(
    [...createPythonCommandArgs(entryScript, pythonCommand, 'release-json'), ...normalizedResourceIds],
    '释放桌面图片资源失败',
  )
})

ipcMain.handle('desktop:image-classifier:check-environment', async () => {
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
    const resolvedPythonCommand = resolvePythonCommand()
    pythonCommand = resolvedPythonCommand.leadingArgs.length
      ? `${resolvedPythonCommand.program} ${resolvedPythonCommand.leadingArgs.join(' ')}`
      : resolvedPythonCommand.program
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
})

ipcMain.handle('desktop:image-classifier:select-inputs', async (_event, mode) => {
  if (mode === 'file') {
    const result = await dialog.showOpenDialog({
      title: '选择图片或视频',
      properties: ['openFile', 'multiSelections'],
      filters: [
        {
          name: 'Media',
          extensions: IMAGE_CLASSIFIER_MEDIA_EXTENSIONS.map((extension) => extension.slice(1)),
        },
      ],
    })
    return result.canceled ? [] : result.filePaths
  }

  if (mode === 'folder') {
    const result = await dialog.showOpenDialog({
      title: '选择文件夹',
      properties: ['openDirectory'],
    })
    return result.canceled ? [] : result.filePaths
  }

  throw new Error('不支持的选择模式。')
})

ipcMain.handle('desktop:image-classifier:select-output-path', async (_event, mode) => {
  if (mode === 'csv') {
    const result = await dialog.showSaveDialog({
      title: '导出 CSV',
      defaultPath: 'image-classifier-results.csv',
      filters: [{ name: 'CSV', extensions: ['csv'] }],
    })
    return result.canceled ? null : result.filePath ?? null
  }

  if (mode === 'json') {
    const result = await dialog.showSaveDialog({
      title: '导出 JSON',
      defaultPath: 'image-classifier-results.json',
      filters: [{ name: 'JSON', extensions: ['json'] }],
    })
    return result.canceled ? null : result.filePath ?? null
  }

  if (mode === 'folder') {
    const result = await dialog.showOpenDialog({
      title: '选择分类输出文件夹',
      properties: ['openDirectory', 'createDirectory'],
    })
    return result.canceled ? null : result.filePaths[0] ?? null
  }

  throw new Error('不支持的输出选择模式。')
})

ipcMain.handle('desktop:image-classifier:discover-inputs', async (_event, request) => {
  if (!Array.isArray(request?.inputs) || request.inputs.length === 0) {
    return { inputs: [] }
  }

  const pythonCommand = resolvePythonCommand()
  const { entryScript } = resolveImageClassifierPaths()
  return await runImageClassifierJsonCommand(
    buildImageClassifierDiscoverArgs(request, entryScript, pythonCommand),
    '发现图片分类输入失败',
  )
})

ipcMain.handle('desktop:image-classifier:stop', async () => {
  await stopImageClassifier()
})

ipcMain.handle('desktop:image-classifier:action', async (_event, request) => {
  const pythonCommand = resolvePythonCommand()
  const { entryScript } = resolveImageClassifierPaths()
  return await runImageClassifierJsonCommand(
    buildImageClassifierActionArgs(request, entryScript, pythonCommand),
    '执行图片分类动作失败',
  )
})

ipcMain.handle('desktop:image-classifier:run', async (_event, request) => {
  return await runImageClassifier(request)
})

ipcMain.handle('desktop:image-classifier:run-stream', async (event, request) => {
  await runImageClassifierStream(event, request)
})

ipcMain.handle('desktop:image-classifier:result-action', async (_event, request) => {
  const normalizedOutputPath = request?.outputPath?.trim()
  if (!normalizedOutputPath) {
    throw new Error('输出路径不能为空。')
  }

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
})

app.whenReady().then(async () => {
  await ensureWidgetWindowStateLoaded()
  Menu.setApplicationMenu(null)
  createMainWindow()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createMainWindow()
    }
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})
