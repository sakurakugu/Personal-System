import { spawn } from 'node:child_process'
import process from 'node:process'
import waitOn from 'wait-on'

const VITE_WAIT_TIMEOUT = 5000
const WAIT_RESOURCE = 'http://localhost:5175'

function createNpmRunner() {
  if (process.platform === 'win32') {
    return {
      command: 'cmd.exe',
      leadingArgs: ['/d', '/s', '/c', 'npm.cmd'],
    }
  }

  return {
    command: 'npm',
    leadingArgs: [],
  }
}

function spawnInherited(command, args) {
  return spawn(command.command, [...command.leadingArgs, ...args], {
    stdio: 'inherit',
    shell: false,
  })
}

const npmCommand = createNpmRunner()
const children = new Set()
let electronStarted = false

function trackChild(child) {
  children.add(child)
  child.once('exit', () => {
    children.delete(child)
  })
  return child
}

function stopChild(child) {
  if (!child || child.killed || child.exitCode !== null) {
    return
  }

  if (process.platform === 'win32') {
    const killer = spawn('taskkill', ['/PID', String(child.pid), '/T', '/F'], {
      stdio: 'ignore',
      shell: false,
    })
    killer.unref()
    return
  }

  child.kill('SIGTERM')
}

function stopAllChildren() {
  for (const child of [...children]) {
    stopChild(child)
  }
}

function bindTerminationSignals() {
  const handleSignal = (signal) => {
    stopAllChildren()
    process.exit(signal === 'SIGINT' ? 130 : 143)
  }

  process.once('SIGINT', () => handleSignal('SIGINT'))
  process.once('SIGTERM', () => handleSignal('SIGTERM'))
}

async function waitForVite() {
  try {
    await waitOn({
      resources: [WAIT_RESOURCE],
      timeout: VITE_WAIT_TIMEOUT,
      interval: 250,
      httpTimeout: 250,
    })
    return true
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error)
    console.warn(`桌面端开发服务器等待超时，继续启动 Electron：${message}`)
    return false
  }
}

async function isViteAvailable() {
  try {
    await waitOn({
      resources: [WAIT_RESOURCE],
      timeout: 1000,
      interval: 250,
      httpTimeout: 250,
    })
    return true
  } catch {
    return false
  }
}

async function main() {
  bindTerminationSignals()

  const viteChild = trackChild(spawnInherited(npmCommand, ['run', 'dev']))

  viteChild.once('exit', async (code, signal) => {
    if (signal || code === 0) {
      stopAllChildren()
      process.exit(code ?? 0)
      return
    }

    if (electronStarted) {
      const viteAvailable = await isViteAvailable()
      if (viteAvailable) {
        console.warn('桌面端开发服务器已存在，复用当前监听实例继续运行。')
        return
      }

      stopAllChildren()
      process.exit(code ?? 1)
      return
    }

    const viteAvailable = await isViteAvailable()
    if (viteAvailable) {
      console.warn('桌面端开发服务器已存在，继续启动 Electron。')
      return
    }

    stopAllChildren()
    process.exit(code ?? 1)
  })

  await waitForVite()

  const electronChild = trackChild(spawnInherited(npmCommand, ['run', 'electron:main']))
  electronStarted = true

  electronChild.once('exit', (code) => {
    stopAllChildren()
    process.exit(code ?? 0)
  })
}

void main()
