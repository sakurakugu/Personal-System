import path from 'node:path'

type AliasEntry = {
  find: RegExp | string
  replacement: string
}

type SharedAliasOptions = {
  appDir: string
  srcAlias?: boolean
}

export function createFrontendAliasEntries(options: SharedAliasOptions): AliasEntry[] {
  const {
    appDir,
    srcAlias = true,
  } = options

  const aliases: AliasEntry[] = []

  if (srcAlias) {
    aliases.push({ find: '@', replacement: path.resolve(appDir, './src') })
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
