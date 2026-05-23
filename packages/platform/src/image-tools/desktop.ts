import type {
  图片工具服务,
  图片资源句柄,
  桌面图片工具运行时,
} from './types'

function isDesktopRuntime(runtime: unknown): runtime is 桌面图片工具运行时 {
  if (!runtime || typeof runtime !== 'object') {
    return false
  }

  return (
    'runtime' in runtime
    && runtime.runtime === 'electron'
    && 'imageToolsGetCapabilities' in runtime
    && typeof runtime.imageToolsGetCapabilities === 'function'
    && 'imageToolsSelectInputs' in runtime
    && typeof runtime.imageToolsSelectInputs === 'function'
    && 'imageToolsSelectOutputPath' in runtime
    && typeof runtime.imageToolsSelectOutputPath === 'function'
    && 'imageToolsImportFromPaths' in runtime
    && typeof runtime.imageToolsImportFromPaths === 'function'
    && 'imageToolsConvert' in runtime
    && typeof runtime.imageToolsConvert === 'function'
    && 'imageToolsEdit' in runtime
    && typeof runtime.imageToolsEdit === 'function'
    && 'imageToolsStitch' in runtime
    && typeof runtime.imageToolsStitch === 'function'
    && 'imageToolsRelease' in runtime
    && typeof runtime.imageToolsRelease === 'function'
  )
}

function assertDesktopRuntime(runtime: unknown): asserts runtime is 桌面图片工具运行时 {
  if (!isDesktopRuntime(runtime)) {
    throw new Error('当前桌面运行时未注入图片工具能力')
  }
}

function 将桌面资源映射为句柄(resources: 图片资源句柄[]) {
  return resources
}

export function 获取桌面图片工具运行时(): 桌面图片工具运行时 | null {
  const runtime = (window as Window & {
    personalSystemDesktop?: unknown
  }).personalSystemDesktop ?? null

  if (!isDesktopRuntime(runtime)) {
    return null
  }

  return runtime
}

export function 创建桌面图片工具服务(runtime = 获取桌面图片工具运行时()): 图片工具服务 {
  assertDesktopRuntime(runtime)

  return {
    async 获取能力() {
      return await runtime.imageToolsGetCapabilities()
    },
    async 导入图片(_input: File[]) {
      throw new Error('桌面图片工具服务暂不支持直接从 File 导入，请改用桌面路径导入')
    },
    async 选择桌面输入() {
      return await runtime.imageToolsSelectInputs()
    },
    async 选择桌面输出路径(mode, options) {
      return await runtime.imageToolsSelectOutputPath(mode, options)
    },
    async 从桌面路径导入图片(paths: string[]) {
      return 将桌面资源映射为句柄(await runtime.imageToolsImportFromPaths(paths))
    },
    async 执行转换(resourceId, output) {
      return await runtime.imageToolsConvert({
        resourceId,
        output,
      })
    },
    async 执行编辑(resourceId, edit, output) {
      return await runtime.imageToolsEdit({
        resourceId,
        edit,
        output,
      })
    },
    async 执行拼接(resourceIds, stitch, output) {
      return await runtime.imageToolsStitch({
        resourceIds,
        stitch,
        output,
      })
    },
    async 释放资源(resourceIds) {
      await runtime.imageToolsRelease(resourceIds)
    },
  }
}
