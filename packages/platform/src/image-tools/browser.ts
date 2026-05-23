import type {
  图片导出参数,
  图片工具能力,
  图片工具服务,
  图片编辑参数,
  图片拼接参数,
  图片资源句柄,
} from './types'

const 浏览器导入格式 = [
  {
    mimeType: 'image/png',
    扩展名: ['png'],
    可导入: true,
    可导出: true,
    支持透明: true,
    支持动画: false,
    保留元数据: false,
  },
  {
    mimeType: 'image/jpeg',
    扩展名: ['jpg', 'jpeg'],
    可导入: true,
    可导出: true,
    支持透明: false,
    支持动画: false,
    保留元数据: false,
  },
  {
    mimeType: 'image/webp',
    扩展名: ['webp'],
    可导入: true,
    可导出: true,
    支持透明: true,
    支持动画: false,
    保留元数据: false,
  },
  {
    mimeType: 'image/avif',
    扩展名: ['avif'],
    可导入: true,
    可导出: true,
    支持透明: true,
    支持动画: false,
    保留元数据: false,
  },
  {
    mimeType: 'image/gif',
    扩展名: ['gif'],
    可导入: true,
    可导出: false,
    支持透明: true,
    支持动画: false,
    保留元数据: false,
  },
] as const

const 浏览器图片工具能力: 图片工具能力 = {
  运行时: 'browser',
  支持后端增强: false,
  导入格式: [...浏览器导入格式],
  导出格式: 浏览器导入格式.filter((item) => item.可导出),
  支持预览代理: false,
  支持拼接: true,
  支持编辑: true,
  支持批量转换: true,
}

function 创建浏览器未实现错误(methodName: string) {
  return new Error(`浏览器图片工具服务暂未实现方法：${methodName}`)
}

export function 获取浏览器图片工具能力() {
  return 浏览器图片工具能力
}

export function 创建浏览器图片工具服务(): 图片工具服务 {
  return {
    async 获取能力() {
      return 浏览器图片工具能力
    },
    async 导入图片(_input: File[]): Promise<图片资源句柄[]> {
      throw 创建浏览器未实现错误('导入图片')
    },
    async 选择桌面输入() {
      throw 创建浏览器未实现错误('选择桌面输入')
    },
    async 选择桌面输出路径() {
      throw 创建浏览器未实现错误('选择桌面输出路径')
    },
    async 执行转换(_resourceId: string, _options: 图片导出参数) {
      throw 创建浏览器未实现错误('执行转换')
    },
    async 执行编辑(_resourceId: string, _edit: 图片编辑参数, _output: 图片导出参数) {
      throw 创建浏览器未实现错误('执行编辑')
    },
    async 执行拼接(_resourceIds: string[], _stitch: 图片拼接参数, _output: 图片导出参数) {
      throw 创建浏览器未实现错误('执行拼接')
    },
    async 释放资源(_resourceIds: string[]) {
      return
    },
  }
}
