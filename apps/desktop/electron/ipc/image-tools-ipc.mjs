import { dialog, ipcMain } from 'electron'

import { IPC_CHANNELS } from '../shared/ipc-channels.mjs'
import {
  convertImageResource,
  editImageResource,
  getImageToolCapabilities,
  importImagesFromPaths,
  releaseImageResources,
  stitchImageResources,
} from '../services/image-tools.mjs'

function registerImageToolsIpc() {
  ipcMain.handle(IPC_CHANNELS.imageToolsGetCapabilities, async () => {
    return await getImageToolCapabilities()
  })

  ipcMain.handle(IPC_CHANNELS.imageToolsSelectInputs, async () => {
    const result = await dialog.showOpenDialog({
      title: '选择图片文件',
      properties: ['openFile', 'multiSelections'],
      filters: [
        {
          name: 'Images',
          extensions: ['png', 'jpg', 'jpeg', 'webp', 'avif', 'bmp', 'gif', 'heic', 'heif', 'tif', 'tiff', 'ico', 'psd'],
        },
      ],
    })

    return result.canceled ? [] : result.filePaths
  })

  ipcMain.handle(IPC_CHANNELS.imageToolsSelectOutputPath, async (_event, mode, options) => {
    if (mode === 'file') {
      const result = await dialog.showSaveDialog({
        title: '选择图片输出路径',
        defaultPath: options?.defaultName?.trim() || 'image.png',
        filters: Array.isArray(options?.filters) ? options.filters : undefined,
      })
      return result.canceled ? null : result.filePath ?? null
    }

    if (mode === 'folder') {
      const result = await dialog.showOpenDialog({
        title: '选择输出文件夹',
        properties: ['openDirectory', 'createDirectory'],
      })
      return result.canceled ? null : result.filePaths[0] ?? null
    }

    throw new Error('不支持的图片工具输出选择模式。')
  })

  ipcMain.handle(IPC_CHANNELS.imageToolsImportFromPaths, async (_event, paths) => {
    return await importImagesFromPaths(paths)
  })

  ipcMain.handle(IPC_CHANNELS.imageToolsConvert, async (_event, request) => {
    return await convertImageResource(request)
  })

  ipcMain.handle(IPC_CHANNELS.imageToolsEdit, async (_event, request) => {
    return await editImageResource(request)
  })

  ipcMain.handle(IPC_CHANNELS.imageToolsStitch, async (_event, request) => {
    return await stitchImageResources(request)
  })

  ipcMain.handle(IPC_CHANNELS.imageToolsRelease, async (_event, resourceIds) => {
    await releaseImageResources(resourceIds)
  })
}

export {
  registerImageToolsIpc,
}
