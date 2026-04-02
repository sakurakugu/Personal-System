import type { CapacitorConfig } from '@capacitor/cli'

function resolveDevServerConfig(): CapacitorConfig['server'] | undefined {
  const rawUrl = process.env.CAP_SERVER_URL?.trim()
  if (!rawUrl) {
    return undefined
  }

  const serverUrl = new URL(rawUrl)

  return {
    url: serverUrl.toString(),
    cleartext: serverUrl.protocol === 'http:',
  }
}

const config: CapacitorConfig = {
  appId: 'com.elric.websystem',
  appName: 'Web System',
  webDir: 'dist',
  bundledWebRuntime: false,
  server: resolveDevServerConfig(),
}

export default config
