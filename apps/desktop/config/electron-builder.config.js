import { createPythonToolResources } from './electron-builder/python-tools.js'

const processEnv = globalThis.process?.env ?? {}
const 支持的Windows构建目标 = new Set(['nsis', 'msi', 'portable'])

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
  ],
  extraResources: createPythonToolResources(),
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
