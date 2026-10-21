import { APP_PROTOCOL_SCHEME } from '../electron/shared/protocol.mjs'

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
    '!node_modules/**/*',
  ],
  asar: true,
  // 自定义协议注册：macOS 写入 Info.plist；Windows 由主进程运行时注册 + 安装器关联。
  protocols: [
    {
      name: 'Personal System',
      // 协议 scheme 集中在 electron/shared/protocol.mjs，改名时只改一处。
      schemes: [APP_PROTOCOL_SCHEME],
    },
  ],
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
