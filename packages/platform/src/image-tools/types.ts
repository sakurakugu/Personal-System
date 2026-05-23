export type 图片格式能力 = {
  mimeType: string
  扩展名: readonly string[]
  可导入: boolean
  可导出: boolean
  支持透明: boolean
  支持动画: boolean
  保留元数据: boolean
}

export type 图片工具能力 = {
  运行时: 'browser' | 'desktop'
  支持后端增强: boolean
  导入格式: 图片格式能力[]
  导出格式: 图片格式能力[]
  支持预览代理: boolean
  支持拼接: boolean
  支持编辑: boolean
  支持批量转换: boolean
}

export type 图片资源句柄 = {
  id: string
  原始文件名: string
  原始MimeType: string
  宽度: number
  高度: number
  是否动画: boolean
  预览地址: string
  源文件路径?: string
  元数据摘要?: {
    hasExif: boolean
    hasIcc: boolean
  }
}

export type 图片编辑参数 = {
  旋转角度: number
  水平翻转: boolean
  垂直翻转: boolean
  亮度?: number
  对比度?: number
  饱和度?: number
  灰度?: number
  模糊?: number
  裁剪区域?: {
    x: number
    y: number
    width: number
    height: number
  }
  输出宽度?: number
  输出高度?: number
}

export type 图片拼接参数 = {
  布局: 'horizontal' | 'vertical' | 'grid' | 'subtitle'
  目标尺寸: number
  列数?: number
  间距: number
  边距: number
  字幕裁剪比例?: number
  宫格比例?: '1:1' | '4:3' | '3:4' | '16:9'
  宫格填充?: 'contain' | 'cover'
  背景: {
    type: 'transparent' | 'solid'
    color?: string
  }
}

export type 图片导出参数 = {
  mimeType: string
  quality?: number
  保留元数据?: boolean
  保持动画?: boolean
  outputPath?: string | null
}

export type 桌面文件结果 = {
  outputPath: string
  outputMimeType: string
  outputSize: number
}

export type 图片工具结果 = Blob | 桌面文件结果

export interface 图片工具服务 {
  获取能力(): Promise<图片工具能力>
  导入图片(input: File[]): Promise<图片资源句柄[]>
  选择桌面输入?(): Promise<string[]>
  选择桌面输出路径?(mode: 'file' | 'folder', options?: {
    defaultName?: string
    filters?: Array<{ name: string, extensions: string[] }>
  }): Promise<string | null>
  从桌面路径导入图片?(paths: string[]): Promise<图片资源句柄[]>
  执行转换(resourceId: string, options: 图片导出参数): Promise<图片工具结果>
  执行编辑(resourceId: string, edit: 图片编辑参数, output: 图片导出参数): Promise<图片工具结果>
  执行拼接(resourceIds: string[], stitch: 图片拼接参数, output: 图片导出参数): Promise<图片工具结果>
  释放资源(resourceIds: string[]): Promise<void>
}

export type 桌面图片工具运行时 = {
  runtime: 'electron'
  imageToolsGetCapabilities: () => Promise<图片工具能力>
  imageToolsSelectInputs: () => Promise<string[]>
  imageToolsSelectOutputPath: (mode: 'file' | 'folder', options?: {
    defaultName?: string
    filters?: Array<{ name: string, extensions: string[] }>
  }) => Promise<string | null>
  imageToolsImportFromPaths: (paths: string[]) => Promise<图片资源句柄[]>
  imageToolsConvert: (request: {
    resourceId: string
    output: 图片导出参数
  }) => Promise<桌面文件结果>
  imageToolsEdit: (request: {
    resourceId: string
    edit: 图片编辑参数
    output: 图片导出参数
  }) => Promise<桌面文件结果>
  imageToolsStitch: (request: {
    resourceIds: string[]
    stitch: 图片拼接参数
    output: 图片导出参数
  }) => Promise<桌面文件结果>
  imageToolsRelease: (resourceIds: string[]) => Promise<void>
}
