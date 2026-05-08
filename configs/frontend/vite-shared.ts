import fs from 'node:fs'
import path from 'node:path'

type AliasEntry = {
  find: RegExp | string
  replacement: string
}

type SharedAliasOptions = {
  appDir: string
  srcAlias?: boolean
}

type WorkspacePackageJson = {
  name?: string
}

function 规范化路径(filePath: string) {
  return filePath.replace(/\\/g, '/')
}

function 转义正则文本(text: string) {
  return text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

function 读取工作区配置(packageJsonPath: string) {
  const rawContent = fs.readFileSync(packageJsonPath, 'utf8')
  const parsed = JSON.parse(rawContent) as { workspaces?: string[] }
  return Array.isArray(parsed.workspaces) ? parsed.workspaces : []
}

function 查找工作区根目录(startDir: string) {
  let currentDir = path.resolve(startDir)

  while (true) {
    const packageJsonPath = path.join(currentDir, 'package.json')
    if (fs.existsSync(packageJsonPath)) {
      const workspacePatterns = 读取工作区配置(packageJsonPath)
      if (workspacePatterns.length > 0) {
        return {
          workspaceRoot: currentDir,
          workspacePatterns,
        }
      }
    }

    const parentDir = path.dirname(currentDir)
    if (parentDir === currentDir) {
      throw new Error(`未找到工作区根目录：${startDir}`)
    }

    currentDir = parentDir
  }
}

function 展开工作区目录(workspaceRoot: string, workspacePattern: string) {
  const normalizedPattern = workspacePattern.replace(/\\/g, '/')

  if (normalizedPattern.endsWith('/*')) {
    const baseDir = path.resolve(workspaceRoot, normalizedPattern.slice(0, -2))
    if (!fs.existsSync(baseDir)) {
      return []
    }

    return fs.readdirSync(baseDir, { withFileTypes: true })
      .filter((entry) => entry.isDirectory())
      .map((entry) => path.join(baseDir, entry.name))
  }

  const targetDir = path.resolve(workspaceRoot, normalizedPattern)
  return fs.existsSync(targetDir) ? [targetDir] : []
}

function 读取工作区包别名(directoryPath: string): AliasEntry[] {
  const packageJsonPath = path.join(directoryPath, 'package.json')
  const srcDir = path.join(directoryPath, 'src')

  if (!fs.existsSync(packageJsonPath) || !fs.existsSync(srcDir)) {
    return []
  }

  const rawContent = fs.readFileSync(packageJsonPath, 'utf8')
  const packageJson = JSON.parse(rawContent) as WorkspacePackageJson
  if (!packageJson.name?.startsWith('@personal-system/')) {
    return []
  }

  const normalizedSrcDir = 规范化路径(srcDir)
  const escapedPackageName = 转义正则文本(packageJson.name)

  return [
    {
      find: packageJson.name,
      replacement: normalizedSrcDir,
    },
    {
      find: new RegExp(`^${escapedPackageName}/(.+)$`),
      replacement: `${normalizedSrcDir}/$1`,
    },
  ]
}

function 创建工作区包别名(startDir: string) {
  const { workspaceRoot, workspacePatterns } = 查找工作区根目录(startDir)
  const packageDirectories = workspacePatterns
    .flatMap((pattern) => 展开工作区目录(workspaceRoot, pattern))
    .sort((left, right) => right.length - left.length)

  return packageDirectories.flatMap((directoryPath) => 读取工作区包别名(directoryPath))
}

export function createFrontendAliasEntries(options: SharedAliasOptions): AliasEntry[] {
  const {
    appDir,
    srcAlias = true,
  } = options

  const aliases: AliasEntry[] = 创建工作区包别名(appDir)

  if (srcAlias) {
    aliases.push({ find: '@', replacement: 规范化路径(path.resolve(appDir, './src')) })
  }

  return aliases
}

export function createFrontendServerConfig(workspaceRoot: string) {
  return {
    fs: {
      allow: [workspaceRoot],
    },
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/files': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  }
}
