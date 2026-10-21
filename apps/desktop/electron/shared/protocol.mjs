/**
 * 桌面端自定义协议常量与解析逻辑。
 *
 * 协议地址集中在这里定义，后续需要改名时只改本文件与 electron-builder 配置中的引用。
 * 当前协议形如：personal-system://widget?token=<urlencoded token>
 */

/** 自定义协议 scheme。 */
const APP_PROTOCOL_SCHEME = 'personal-system'

/** 小工具协议地址的 hostname。 */
const APP_PROTOCOL_WIDGET_HOST = 'widget'

/** 协议地址前缀。 */
const APP_PROTOCOL_PREFIX = `${APP_PROTOCOL_SCHEME}://`

/**
 * 判断一个参数是否是本应用的自定义协议地址。
 * @param {unknown} value 待判断的启动参数
 * @returns {boolean}
 */
function 是应用协议URL(value) {
  return typeof value === 'string' && value.toLowerCase().startsWith(APP_PROTOCOL_PREFIX)
}

/**
 * 从进程启动参数中查找自定义协议地址（Windows/Linux 冷启动会把协议地址放进 argv）。
 * @param {readonly string[] | undefined | null} argv 进程启动参数
 * @returns {string | null}
 */
function 从启动参数查找协议URL(argv) {
  if (!Array.isArray(argv)) {
    return null
  }

  return argv.find((item) => 是应用协议URL(item)) ?? null
}

/**
 * 解析小工具协议地址。
 * 仅接受 personal-system://widget 主机，其余地址返回 null，避免误处理其他协议路由。
 * @param {string} rawUrl 协议地址
 * @returns {{ token: string | null } | null}
 */
function 解析小工具协议URL(rawUrl) {
  if (!是应用协议URL(rawUrl)) {
    return null
  }

  let url
  try {
    url = new URL(rawUrl)
  } catch {
    return null
  }

  if (url.protocol !== `${APP_PROTOCOL_SCHEME}:`) {
    return null
  }

  if (url.hostname !== APP_PROTOCOL_WIDGET_HOST) {
    return null
  }

  const token = url.searchParams.get('token')?.trim() ?? ''

  return {
    token: token ? token : null,
  }
}

export {
  APP_PROTOCOL_PREFIX,
  APP_PROTOCOL_SCHEME,
  APP_PROTOCOL_WIDGET_HOST,
  从启动参数查找协议URL,
  是应用协议URL,
  解析小工具协议URL,
}
