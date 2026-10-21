/**
 * 桌面端主进程入口。
 *
 * 桌面端只保留小工具窗口：启动即创建并显示小工具，不再创建主窗口。
 * 同时注册自定义协议 personal-system://widget?token=...，供网页后台一键唤起并写入设备令牌。
 */
import { app, BrowserWindow, Menu } from 'electron'
import path from 'node:path'
import process from 'node:process'

import { registerIpcHandlers } from './ipc/register-ipc-handlers.mjs'
import { saveDesktopAuthToken } from './services/auth-token.mjs'
import { ensureWidgetWindowStateLoaded } from './services/widget-state.mjs'
import { isDev } from './shared/environment.mjs'
import {
  APP_PROTOCOL_SCHEME,
  从启动参数查找协议URL,
  解析小工具协议URL,
} from './shared/protocol.mjs'
import { createWidgetWindow, getWidgetWindow } from './windows/widget-window.mjs'

/** 主进程入口文件绝对路径，开发期注册协议时需要作为 Electron 的启动参数。 */
const 主进程入口路径 = path.resolve(import.meta.dirname, 'main.mjs')

/** 应用是否已完成启动初始化。 */
let 应用已就绪 = false

/** 应用就绪前收到的协议地址（macOS 的 open-url 可能早于 ready）。 */
let 待处理协议URL = null

/**
 * 注册自定义协议。
 * 开发期需要显式指定 Electron 可执行文件与主进程入口；打包后由安装器/运行时注册。
 */
function 注册自定义协议() {
  if (isDev) {
    app.setAsDefaultProtocolClient(APP_PROTOCOL_SCHEME, process.execPath, [主进程入口路径])
    console.log('桌面端已注册开发版自定义协议', {
      scheme: APP_PROTOCOL_SCHEME,
      electron: process.execPath,
      main: 主进程入口路径,
    })
    return
  }

  app.setAsDefaultProtocolClient(APP_PROTOCOL_SCHEME)
  console.log('桌面端已注册自定义协议', { scheme: APP_PROTOCOL_SCHEME })
}

/**
 * 处理自定义协议地址。
 * 带 token 时先写入设备令牌，再重载/创建小工具（重新 bootstrap 读取令牌进入登录态）；
 * 不带 token 时只打开/聚焦小工具。
 * @param {string} rawUrl 协议地址
 * @returns {Promise<void>}
 */
async function 处理协议URL(rawUrl) {
  const parsed = 解析小工具协议URL(rawUrl)
  if (!parsed) {
    // 只记录协议前缀，避免把 token 等敏感参数写进日志。
    console.warn('桌面端忽略无法识别的协议地址', { protocolPrefix: rawUrl.split('?')[0] })
    return
  }

  if (!应用已就绪) {
    待处理协议URL = rawUrl
    return
  }

  if (parsed.token) {
    await saveDesktopAuthToken(parsed.token)
    console.log('桌面端已通过协议写入设备令牌')
  }

  const 小工具窗口 = getWidgetWindow()
  if (!小工具窗口 || 小工具窗口.isDestroyed()) {
    // 创建新窗口时首次加载就能读到刚写入的令牌，无需额外重载。
    const 新窗口 = createWidgetWindow()
    console.log('桌面端已通过协议创建小工具窗口', {
      hasToken: Boolean(parsed.token),
      windowId: 新窗口.id,
    })
    return
  }

  if (小工具窗口.isMinimized()) {
    小工具窗口.restore()
  }
  小工具窗口.show()
  小工具窗口.focus()

  if (parsed.token) {
    小工具窗口.webContents.reload()
    console.log('桌面端已通知小工具重新加载以应用设备令牌', { windowId: 小工具窗口.id })
    return
  }

  console.log('桌面端已聚焦小工具窗口', { windowId: 小工具窗口.id })
}

/**
 * 聚焦已有小工具窗口；没有窗口时创建。
 */
function 聚焦小工具窗口() {
  if (!应用已就绪) {
    return
  }

  const 小工具窗口 = getWidgetWindow()
  if (!小工具窗口 || 小工具窗口.isDestroyed()) {
    createWidgetWindow()
    return
  }

  if (小工具窗口.isMinimized()) {
    小工具窗口.restore()
  }
  小工具窗口.show()
  小工具窗口.focus()
  console.log('桌面端已聚焦小工具窗口', { windowId: 小工具窗口.id, source: 'second-instance' })
}

/**
 * 应用启动初始化：加载窗口状态、注册 IPC/菜单、处理启动参数里的协议地址、创建小工具。
 * @returns {Promise<void>}
 */
async function 启动应用() {
  await ensureWidgetWindowStateLoaded()
  registerIpcHandlers()
  Menu.setApplicationMenu(null)

  应用已就绪 = true

  // 启动参数里的协议地址（Windows/Linux 冷启动）优先于 open-url 排队地址处理。
  const 排队协议URL = 待处理协议URL
  待处理协议URL = null
  const 初始协议URL = 从启动参数查找协议URL(process.argv) ?? 排队协议URL

  if (初始协议URL) {
    try {
      await 处理协议URL(初始协议URL)
    } catch (error) {
      console.error('桌面端处理启动协议地址失败', error)
    }
    console.log('桌面端已处理启动参数中的协议地址')
  }

  // 启动即直接创建并显示小工具窗口（没有主窗口）。
  createWidgetWindow()
}

/**
 * 绑定应用级事件。
 */
function 绑定应用事件() {
  // 第二实例唤起：带协议地址时按协议处理，否则聚焦小工具。
  app.on('second-instance', (_event, argv) => {
    console.log('桌面端收到第二实例唤起')
    const 协议URL = 从启动参数查找协议URL(argv)
    if (协议URL) {
      void 处理协议URL(协议URL)
      return
    }

    聚焦小工具窗口()
  })

  // macOS 通过协议唤起时由 open-url 事件传入地址，可能早于 ready。
  app.on('open-url', (event, url) => {
    event.preventDefault()
    void 处理协议URL(url)
  })

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWidgetWindow()
    }
  })

  app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
      app.quit()
    }
  })
}

const 已获取单实例锁 = app.requestSingleInstanceLock()

if (!已获取单实例锁) {
  // 已有实例在运行，当前实例直接退出，由已有实例处理协议地址或聚焦窗口。
  app.quit()
} else {
  注册自定义协议()
  绑定应用事件()
  void app.whenReady().then(启动应用).catch((error) => {
    console.error('桌面端启动失败', error)
    app.quit()
  })
}
