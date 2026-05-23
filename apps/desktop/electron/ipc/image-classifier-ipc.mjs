import { dialog, ipcMain } from 'electron'

import { IMAGE_CLASSIFIER_MEDIA_EXTENSIONS } from '../shared/constants.mjs'
import { IPC_CHANNELS } from '../shared/ipc-channels.mjs'
import {
  checkImageClassifierEnvironment,
  discoverImageClassifierInputs,
  runImageClassifier,
  runImageClassifierAction,
  runImageClassifierResultAction,
  runImageClassifierStream,
  stopImageClassifier,
} from '../services/image-classifier.mjs'

function registerImageClassifierIpc() {
  ipcMain.handle(IPC_CHANNELS.imageClassifierCheckEnvironment, async () => {
    return await checkImageClassifierEnvironment()
  })

  ipcMain.handle(IPC_CHANNELS.imageClassifierSelectInputs, async (_event, mode) => {
    if (mode === 'file') {
      const result = await dialog.showOpenDialog({
        title: '选择图片或视频',
        properties: ['openFile', 'multiSelections'],
        filters: [
          {
            name: 'Media',
            extensions: IMAGE_CLASSIFIER_MEDIA_EXTENSIONS.map((extension) => extension.slice(1)),
          },
        ],
      })
      return result.canceled ? [] : result.filePaths
    }

    if (mode === 'folder') {
      const result = await dialog.showOpenDialog({
        title: '选择文件夹',
        properties: ['openDirectory'],
      })
      return result.canceled ? [] : result.filePaths
    }

    throw new Error('不支持的选择模式。')
  })

  ipcMain.handle(IPC_CHANNELS.imageClassifierSelectOutputPath, async (_event, mode) => {
    if (mode === 'csv') {
      const result = await dialog.showSaveDialog({
        title: '导出 CSV',
        defaultPath: 'image-classifier-results.csv',
        filters: [{ name: 'CSV', extensions: ['csv'] }],
      })
      return result.canceled ? null : result.filePath ?? null
    }

    if (mode === 'json') {
      const result = await dialog.showSaveDialog({
        title: '导出 JSON',
        defaultPath: 'image-classifier-results.json',
        filters: [{ name: 'JSON', extensions: ['json'] }],
      })
      return result.canceled ? null : result.filePath ?? null
    }

    if (mode === 'folder') {
      const result = await dialog.showOpenDialog({
        title: '选择分类输出文件夹',
        properties: ['openDirectory', 'createDirectory'],
      })
      return result.canceled ? null : result.filePaths[0] ?? null
    }

    throw new Error('不支持的输出选择模式。')
  })

  ipcMain.handle(IPC_CHANNELS.imageClassifierDiscoverInputs, async (_event, request) => {
    return await discoverImageClassifierInputs(request)
  })

  ipcMain.handle(IPC_CHANNELS.imageClassifierStop, async () => {
    await stopImageClassifier()
  })

  ipcMain.handle(IPC_CHANNELS.imageClassifierAction, async (_event, request) => {
    return await runImageClassifierAction(request)
  })

  ipcMain.handle(IPC_CHANNELS.imageClassifierRun, async (_event, request) => {
    return await runImageClassifier(request)
  })

  ipcMain.handle(IPC_CHANNELS.imageClassifierRunStream, async (event, request) => {
    await runImageClassifierStream(event, request)
  })

  ipcMain.handle(IPC_CHANNELS.imageClassifierResultAction, async (_event, request) => {
    return await runImageClassifierResultAction(request)
  })
}

export {
  registerImageClassifierIpc,
}
