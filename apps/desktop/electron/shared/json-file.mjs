import fs from 'node:fs/promises'
import path from 'node:path'

async function readJsonFile(filePath, fallbackValue) {
  try {
    const content = await fs.readFile(filePath, 'utf8')
    return JSON.parse(content)
  } catch (error) {
    if (error && typeof error === 'object' && 'code' in error && error.code === 'ENOENT') {
      return fallbackValue
    }

    throw error
  }
}

async function writePrettyJson(filePath, payload) {
  await fs.mkdir(path.dirname(filePath), { recursive: true })
  await fs.writeFile(filePath, `${JSON.stringify(payload, null, 2)}\n`, 'utf8')
}

export {
  readJsonFile,
  writePrettyJson,
}
