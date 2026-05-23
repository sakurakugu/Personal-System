import fs from 'node:fs'
import path from 'node:path'
import {
  createEmbeddedPythonRuntimeResource,
  createPythonToolResources,
} from './electron-builder/python-tools.js'

const processEnv = globalThis.process?.env ?? {}
const 支持的Windows构建目标 = new Set(['nsis', 'msi', 'portable'])
const 桌面端Python模式 = processEnv.PERSONAL_SYSTEM_DESKTOP_PYTHON_MODE?.trim() || 'auto'
const 内置Python运行时目录 = path.resolve(import.meta.dirname, '..', 'python-runtime')

function 解析Windows构建目标() {
  const rawTargets = processEnv.PERSONAL_SYSTEM_DESKTOP_BUILD_TARGETS
  if (!rawTargets) {
    return ['nsis']
  }

  const targets = rawTargets
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)

  if (targets.length === 0) {
    return ['nsis']
  }

  for (const target of targets) {
    if (!支持的Windows构建目标.has(target)) {
      throw new Error(`不支持的桌面端 Windows 构建目标: ${target}`)
    }
  }

  return Array.from(new Set(targets))
}

const windowsBuildTargets = 解析Windows构建目标()

function 创建额外资源列表() {
  const resources = [...createPythonToolResources()]
  const 运行时目录存在 = fs.existsSync(内置Python运行时目录)

  if (桌面端Python模式 === 'embedded') {
    if (!运行时目录存在) {
      throw new Error(`当前为 embedded Python 模式，但未找到内置运行时目录: ${内置Python运行时目录}`)
    }
    resources.push(createEmbeddedPythonRuntimeResource())
    return resources
  }

  if (桌面端Python模式 === 'auto' && 运行时目录存在) {
    resources.push(createEmbeddedPythonRuntimeResource())
  }

  return resources
}

const buildConfig = {
  appId: 'top.sakurakugu.personal-system.desktop.electron',
  productName: 'Personal System',
  electronVersion: '42.1.0',
  publish: null,
  directories: {
    output: 'build/release',
  },
  files: [
    'dist/**/*',
    'electron/**/*',
    'package.json',
    '!node_modules/**/*',
  ],
  extraResources: 创建额外资源列表(),
  asar: true,
  win: {
    target: windowsBuildTargets.map((target) => ({
      target,
      arch: ['x64'],
    })),
    icon: 'electron/assets/icon.ico',
  },
  nsis: {
    oneClick: false,
    allowToChangeInstallationDirectory: true,
  },
}

export default buildConfig
