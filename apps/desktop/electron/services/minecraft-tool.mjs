import { execFile } from 'node:child_process'
import os from 'node:os'
import path from 'node:path'

import { readJsonFile, writePrettyJson } from '../shared/json-file.mjs'
import {
  resolveMinecraftToolPaths,
  resolvePythonCommand,
} from './python-runtime.mjs'

function getMinecraftServerStoragePath() {
  return path.join(os.homedir(), '.personal-system', 'minecraft-tool.json')
}

function normalizeMinecraftRecord(record) {
  const address = record?.address?.trim()
  if (!address) {
    return null
  }

  const edition = record?.edition === 'java' || record?.edition === 'bedrock'
    ? record.edition
    : 'auto'

  return { address, edition }
}

function normalizeMinecraftRecords(records, limit) {
  const output = []
  const keys = new Set()

  for (const record of Array.isArray(records) ? records : []) {
    const normalized = normalizeMinecraftRecord(record)
    if (!normalized) {
      continue
    }

    const key = `${normalized.edition}:${normalized.address}`
    if (keys.has(key)) {
      continue
    }

    keys.add(key)
    output.push(normalized)
    if (output.length >= limit) {
      break
    }
  }

  return output
}

async function readMinecraftServerStorage() {
  const data = await readJsonFile(getMinecraftServerStoragePath(), {
    favorites: [],
    history: [],
  })

  return {
    favorites: normalizeMinecraftRecords(data.favorites, 20),
    history: normalizeMinecraftRecords(data.history, 30),
  }
}

async function writeMinecraftServerStorage(data) {
  await writePrettyJson(getMinecraftServerStoragePath(), {
    favorites: normalizeMinecraftRecords(data?.favorites, 20),
    history: normalizeMinecraftRecords(data?.history, 30),
  })
}

async function queryMinecraftServer(request) {
  const address = request?.address?.trim()
  if (!address) {
    throw new Error('服务器地址不能为空。')
  }

  const { toolDir: queryDir, entryScript } = resolveMinecraftToolPaths()
  const pythonCommand = resolvePythonCommand()
  const edition = request?.edition === 'java' || request?.edition === 'bedrock' ? request.edition : 'auto'
  const timeout = request?.timeout ?? 3

  return await new Promise((resolve, reject) => {
    execFile(
      pythonCommand.program,
      [
        ...pythonCommand.leadingArgs,
        entryScript,
        'query-json',
        address,
        '--edition',
        edition,
        '--timeout',
        String(timeout),
      ],
      { cwd: queryDir },
      (error, stdout, stderr) => {
        if (error) {
          reject(new Error(stderr.trim() || error.message))
          return
        }

        try {
          resolve(JSON.parse(stdout.trim()))
        } catch (parseError) {
          reject(parseError)
        }
      },
    )
  })
}

export {
  queryMinecraftServer,
  readMinecraftServerStorage,
  writeMinecraftServerStorage,
}
