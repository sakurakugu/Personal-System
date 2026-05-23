/* global Headers, Response */
import fs from 'node:fs'
import fsPromises from 'node:fs/promises'
import path from 'node:path'
import { Readable } from 'node:stream'
import { pathToFileURL } from 'node:url'

import { app, protocol } from 'electron'

import { isDev } from './environment.mjs'

const DEV_FILE_PROTOCOL_SCHEME = 'personal-system-dev-file'

const MIME_TYPE_BY_EXTENSION = {
  '.aac': 'audio/aac',
  '.avif': 'image/avif',
  '.bin': 'application/octet-stream',
  '.bmp': 'image/bmp',
  '.csv': 'text/csv; charset=utf-8',
  '.flac': 'audio/flac',
  '.gif': 'image/gif',
  '.heic': 'image/heic',
  '.heif': 'image/heif',
  '.ico': 'image/x-icon',
  '.jpeg': 'image/jpeg',
  '.jpg': 'image/jpeg',
  '.js': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.m4a': 'audio/mp4',
  '.md': 'text/markdown; charset=utf-8',
  '.mkv': 'video/x-matroska',
  '.mov': 'video/quicktime',
  '.mp3': 'audio/mpeg',
  '.mp4': 'video/mp4',
  '.ogg': 'audio/ogg',
  '.pdf': 'application/pdf',
  '.png': 'image/png',
  '.py': 'text/x-python; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.tif': 'image/tiff',
  '.tiff': 'image/tiff',
  '.ts': 'text/plain; charset=utf-8',
  '.txt': 'text/plain; charset=utf-8',
  '.vue': 'text/plain; charset=utf-8',
  '.wav': 'audio/wav',
  '.webm': 'video/webm',
  '.webp': 'image/webp',
  '.xml': 'application/xml; charset=utf-8',
  '.yaml': 'text/yaml; charset=utf-8',
  '.yml': 'text/yaml; charset=utf-8',
  '.zip': 'application/zip',
}

let 协议已声明 = false
let 协议已注册 = false

function 输出开发文件协议日志(level, message, extra) {
  const payload = extra ? { ...extra } : undefined
  if (level === 'error') {
    console.error(`[开发文件协议] ${message}`, payload ?? '')
    return
  }
  if (level === 'warn') {
    console.warn(`[开发文件协议] ${message}`, payload ?? '')
    return
  }
  console.log(`[开发文件协议] ${message}`, payload ?? '')
}

function ensureDevFileProtocolDeclared() {
  if (协议已声明 || !isDev) {
    return
  }

  protocol.registerSchemesAsPrivileged([{
    scheme: DEV_FILE_PROTOCOL_SCHEME,
    privileges: {
      standard: true,
      secure: true,
      supportFetchAPI: true,
      stream: true,
      corsEnabled: true,
    },
  }])
  协议已声明 = true
  输出开发文件协议日志('log', '已声明开发版本地文件协议', {
    scheme: DEV_FILE_PROTOCOL_SCHEME,
  })
}

function buildResponseHeaders(filePath, contentLength) {
  const headers = new Headers({
    'Accept-Ranges': 'bytes',
    'Cache-Control': 'no-store',
    'Content-Length': String(contentLength),
    'Access-Control-Allow-Origin': '*',
  })

  const extension = path.extname(filePath).toLowerCase()
  headers.set('Content-Type', MIME_TYPE_BY_EXTENSION[extension] ?? 'application/octet-stream')

  return headers
}

function isAbsoluteLocalPath(filePath) {
  if (!filePath || !path.isAbsolute(filePath)) {
    return false
  }

  if (process.platform !== 'win32') {
    return true
  }

  return /^[a-zA-Z]:\\/.test(filePath) || filePath.startsWith('\\\\')
}

function parseRangeHeader(rangeHeader, fileSize) {
  if (!rangeHeader) {
    return null
  }

  const matched = /^bytes=(\d*)-(\d*)$/i.exec(rangeHeader.trim())
  if (!matched) {
    return { error: '无法解析 Range 请求头。' }
  }

  const rawStart = matched[1]
  const rawEnd = matched[2]

  if (!rawStart && !rawEnd) {
    return { error: 'Range 请求头缺少起止位置。' }
  }

  let start = rawStart ? Number.parseInt(rawStart, 10) : Number.NaN
  let end = rawEnd ? Number.parseInt(rawEnd, 10) : Number.NaN

  if (Number.isNaN(start) && Number.isNaN(end)) {
    return { error: 'Range 请求头不是有效数字。' }
  }

  if (Number.isNaN(start)) {
    const suffixLength = end
    if (!Number.isFinite(suffixLength) || suffixLength <= 0) {
      return { error: 'Range 尾段长度无效。' }
    }
    start = Math.max(0, fileSize - suffixLength)
    end = fileSize - 1
  } else if (Number.isNaN(end) || end >= fileSize) {
    end = fileSize - 1
  }

  if (start < 0 || start >= fileSize || end < start) {
    return { error: 'Range 请求超出文件范围。' }
  }

  return { start, end }
}

function createErrorResponse(status, message, extra) {
  if (status >= 500) {
    输出开发文件协议日志('error', message, extra)
  } else {
    输出开发文件协议日志('warn', message, extra)
  }
  return new Response(message, { status })
}

async function handleDevFileRequest(request) {
  if (request.method !== 'GET' && request.method !== 'HEAD') {
    return createErrorResponse(405, '仅支持读取本地文件。', {
      method: request.method,
      url: request.url,
    })
  }

  let filePath = ''
  try {
    const requestUrl = new URL(request.url)
    if (requestUrl.hostname !== 'local') {
      return createErrorResponse(400, '开发版本地文件协议主机无效。', {
        hostname: requestUrl.hostname,
        url: request.url,
      })
    }

    filePath = requestUrl.searchParams.get('path') ?? ''
    if (!filePath) {
      return createErrorResponse(400, '缺少本地文件路径。', {
        url: request.url,
      })
    }

    const normalizedPath = path.resolve(filePath)
    if (!isAbsoluteLocalPath(normalizedPath)) {
      return createErrorResponse(400, '仅允许访问绝对本地文件路径。', {
        requestedPath: filePath,
        normalizedPath,
      })
    }

    const stats = await fsPromises.stat(normalizedPath)
    if (!stats.isFile()) {
      return createErrorResponse(404, '目标不是文件。', {
        normalizedPath,
      })
    }

    const rangeHeader = request.headers.get('range')
    const parsedRange = parseRangeHeader(rangeHeader, stats.size)
    if (parsedRange?.error) {
      return createErrorResponse(416, parsedRange.error, {
        normalizedPath,
        rangeHeader,
        fileSize: stats.size,
      })
    }

    if (parsedRange) {
      const { start, end } = parsedRange
      const contentLength = end - start + 1
      const headers = buildResponseHeaders(normalizedPath, contentLength)
      headers.set('Content-Range', `bytes ${start}-${end}/${stats.size}`)

      if (request.method === 'HEAD') {
        return new Response(null, { status: 206, headers })
      }

      const stream = fs.createReadStream(normalizedPath, { start, end })
      return new Response(Readable.toWeb(stream), {
        status: 206,
        headers,
      })
    }

    const headers = buildResponseHeaders(normalizedPath, stats.size)
    if (request.method === 'HEAD') {
      return new Response(null, { status: 200, headers })
    }

    const stream = fs.createReadStream(normalizedPath)
    return new Response(Readable.toWeb(stream), {
      status: 200,
      headers,
    })
  } catch (error) {
    const status = filePath && error && typeof error === 'object' && 'code' in error && error.code === 'ENOENT' ? 404 : 500
    return createErrorResponse(
      status,
      `读取开发版本地文件失败：${error instanceof Error ? error.message : String(error)}`,
      {
        filePath,
        url: request.url,
      },
    )
  }
}

async function registerDevFileProtocol() {
  if (!isDev || 协议已注册) {
    return
  }

  ensureDevFileProtocolDeclared()
  await protocol.handle(DEV_FILE_PROTOCOL_SCHEME, handleDevFileRequest)
  协议已注册 = true
  输出开发文件协议日志('log', '已注册开发版本地文件协议处理器', {
    scheme: DEV_FILE_PROTOCOL_SCHEME,
  })
}

function buildLocalFileUrl(filePath) {
  const normalizedPath = path.resolve(filePath)
  if (!isDev) {
    return pathToFileURL(normalizedPath).toString()
  }

  const url = new URL(`${DEV_FILE_PROTOCOL_SCHEME}://local/`)
  url.searchParams.set('path', normalizedPath)
  return url.toString()
}

ensureDevFileProtocolDeclared()

export {
  buildLocalFileUrl,
  registerDevFileProtocol,
}
