import { app } from 'electron'
import { spawnSync } from 'node:child_process'
import { existsSync } from 'node:fs'
import path from 'node:path'
import process from 'node:process'

import {
  DESKTOP_EMBEDDED_PYTHON_DIR,
  DESKTOP_PYTHON_MODE_ENV_KEY,
  DESKTOP_PYTHON_RESOURCE_DIR,
  IMAGE_CLASSIFIER_RELATIVE_DIR,
  IMAGE_TOOLS_RELATIVE_DIR,
  MINECRAFT_TOOL_RELATIVE_DIR,
} from '../shared/constants.mjs'
import { appRoot } from '../shared/environment.mjs'

let cachedPythonCommand = null

function resolveWorkspaceRoot() {
  const candidates = [process.cwd(), appRoot, path.resolve(appRoot, '..', '..')]

  for (const candidate of candidates) {
    if (!candidate) {
      continue
    }

    const appsDesktopPath = path.join(candidate, 'apps', 'desktop')
    const packagesPath = path.join(candidate, 'packages')
    if (existsSync(appsDesktopPath) && existsSync(packagesPath)) {
      return candidate
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

function formatPythonCommand(pythonCommand) {
  return pythonCommand.leadingArgs.length
    ? `${pythonCommand.program} ${pythonCommand.leadingArgs.join(' ')}`
    : pythonCommand.program
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

function commandWorks(program, args) {
  const result = spawnSync(program, args, { encoding: 'utf8' })
  return result.status === 0
}

function createPythonCommandArgs(entryScript, pythonCommand, subcommand) {
  void pythonCommand
  return [entryScript, subcommand]
}

export {
  commandWorks,
  createPythonCommandArgs,
  formatPythonCommand,
  resolveImageClassifierPaths,
  resolveImageToolsPaths,
  resolveMinecraftToolPaths,
  resolvePythonCommand,
}
