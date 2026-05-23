import { 创建浏览器图片工具服务, 获取浏览器图片工具能力 } from './browser'
import { 创建桌面图片工具服务, 获取桌面图片工具运行时 } from './desktop'
import type { 图片工具能力, 图片工具服务 } from './types'

export function 获取默认图片工具能力(): 图片工具能力 {
  const desktopRuntime = 获取桌面图片工具运行时()
  if (desktopRuntime) {
    return {
      ...获取浏览器图片工具能力(),
      运行时: 'desktop',
      支持后端增强: true,
      支持预览代理: true,
    }
  }

  return 获取浏览器图片工具能力()
}

export function 创建图片工具服务(): 图片工具服务 {
  const desktopRuntime = 获取桌面图片工具运行时()
  if (desktopRuntime) {
    return 创建桌面图片工具服务(desktopRuntime)
  }

  return 创建浏览器图片工具服务()
}

export {
  创建浏览器图片工具服务,
  创建桌面图片工具服务,
  获取桌面图片工具运行时,
}
