/**
 * 桌面端自定义协议常量。
 *
 * 协议地址集中在这里定义，后续需要改名时只改本文件与桌面端 electron 配置中的引用。
 * 当前协议形如：personal-system://widget?token=<urlencoded token>。
 */

/** 桌面端自定义协议 scheme。 */
export const 桌面端协议名 = 'personal-system'

/** 小工具协议地址的 hostname。 */
export const 桌面端小工具主机名 = 'widget'

/** 协议地址前缀。 */
export const 桌面端协议前缀 = `${桌面端协议名}://`

/**
 * 构建唤起桌面端小工具的协议地址。
 * @param token 桌面端设备令牌
 */
export function 构建桌面端小工具协议地址(token: string): string {
  return `${桌面端协议前缀}${桌面端小工具主机名}?token=${encodeURIComponent(token)}`
}

/** 判断字符串是否为桌面端协议地址。 */
export function 是否为桌面端协议地址(地址: string): boolean {
  return 地址.toLowerCase().startsWith(桌面端协议前缀)
}
