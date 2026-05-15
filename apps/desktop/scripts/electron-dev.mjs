import { spawn } from 'node:child_process'
import fs from 'node:fs'
import { createRequire } from 'node:module'
import path from 'node:path'
import process from 'node:process'
import { clearTimeout, setTimeout } from 'node:timers'
import waitOn from 'wait-on'

const VITE_WAIT_TIMEOUT = 5000
const WAIT_RESOURCE = 'http://localhost:5175'
const require = createRequire(import.meta.url)
const electronBinary = require('electron')
const vitePackageJsonPath = require.resolve('vite/package.json')
const vitePackageJson = JSON.parse(fs.readFileSync(vitePackageJsonPath, 'utf8'))
const viteBinRelativePath = typeof vitePackageJson.bin === 'string' ? vitePackageJson.bin : vitePackageJson.bin?.vite

if (!viteBinRelativePath) {
  throw new Error('未找到 Vite CLI 入口。')
}

const viteCliPath = path.resolve(path.dirname(vitePackageJsonPath), viteBinRelativePath)
const children = new Set()
let electronStarted = false
let shuttingDown = false

function trackChild(child) {
  children.add(child)
  child.once('exit', () => {
    children.delete(child)
  })
  return child
}

function waitForChildExit(child, timeout = 5000) {
  if (!child || child.exitCode !== null) {
    return Promise.resolve()
  }

  return new Promise((resolve) => {
    let finished = false
    const finish = () => {
      if (finished) {
        return
      }
      finished = true
      clearTimeout(timer)
      resolve()
    }

    const timer = setTimeout(finish, timeout)
    child.once('exit', finish)
  })
}

async function stopChild(child) {
  if (!child || child.killed || child.exitCode !== null) {
    return
  }

  if (process.platform === 'win32') {
    await new Promise((resolve) => {
      const killer = spawn('taskkill', ['/PID', String(child.pid), '/T', '/F'], {
        stdio: 'ignore',
        shell: false,
      })

      const finish = () => resolve()
      killer.once('exit', finish)
      killer.once('error', finish)
    })
    await waitForChildExit(child)
    return
  }

  child.kill('SIGTERM')
  await waitForChildExit(child)
}

async function stopAllChildren() {
  const pending = [...children].map((child) => stopChild(child))
  await Promise.allSettled(pending)
}

async function shutdown(code) {
  if (shuttingDown) {
    return
  }

  shuttingDown = true
  await stopAllChildren()
  process.exit(code)
}

function bindTerminationSignals() {
  const handleSignal = (signal) => {
    void shutdown(signal === 'SIGINT' ? 130 : 143)
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

  const viteChild = trackChild(spawn(process.execPath, [viteCliPath, '--port', '5175', '--strictPort'], {
    stdio: 'inherit',
    shell: false,
  }))

  viteChild.once('exit', async (code, signal) => {
    if (shuttingDown) {
      return
    }

    if (signal || code === 0) {
      await shutdown(code ?? 0)
      return
    }

    if (electronStarted) {
      const viteAvailable = await isViteAvailable()
      if (viteAvailable) {
        console.warn('桌面端开发服务器已存在，复用当前监听实例继续运行。')
        return
      }

      await shutdown(code ?? 1)
      return
    }

    const viteAvailable = await isViteAvailable()
    if (viteAvailable) {
      console.warn('桌面端开发服务器已存在，继续启动 Electron。')
      return
    }

    await shutdown(code ?? 1)
  })

  await waitForVite()

  const electronChild = trackChild(spawn(electronBinary, ['./electron/main.mjs'], {
    stdio: 'inherit',
    shell: false,
  }))
  electronStarted = true

  electronChild.once('exit', (code) => {
    if (shuttingDown) {
      return
    }
    void shutdown(code ?? 0)
  })
}

void main()
