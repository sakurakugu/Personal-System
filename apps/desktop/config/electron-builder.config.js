import { createPythonToolResources } from './electron-builder/python-tools.js'

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
    target: [
      {
        target: 'nsis',
        arch: ['x64'],
      },
    ],
    icon: 'electron/assets/icon.ico',
  },
  nsis: {
    oneClick: false,
    allowToChangeInstallationDirectory: true,
  },
}

export default buildConfig
