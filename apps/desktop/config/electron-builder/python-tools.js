export const PYTHON_TOOL_EXCLUDE_PATTERNS = [
  '!**/.git/**',
  '!**/.githooks/**',
  '!**/.gitignore',
  '!**/.mypy_cache/**',
  '!**/.ruff_cache/**',
  '!**/__pycache__/**',
  '!**/*.pyc',
  '!**/*.pyo',
  '!**/AGENTS.md',
  '!**/README.md',
  '!**/LICENSE',
  '!**/requirements.txt',
  '!**/pyproject.toml',
]

export const PYTHON_TOOL_DIRECTORIES = [
  'ai-media-processor',
  'image-tools',
  'minecraft-tool',
]

const DESKTOP_EMBEDDED_PYTHON_DIRECTORY = 'python-runtime'

export function createPythonToolResources() {
  return PYTHON_TOOL_DIRECTORIES.map((directoryName) => ({
    from: `python/${directoryName}`,
    to: `python/${directoryName}`,
    filter: [
      '**/*',
      ...PYTHON_TOOL_EXCLUDE_PATTERNS,
    ],
  }))
}

export function createEmbeddedPythonRuntimeResource() {
  return {
    from: DESKTOP_EMBEDDED_PYTHON_DIRECTORY,
    to: DESKTOP_EMBEDDED_PYTHON_DIRECTORY,
    filter: [
      '**/*',
      ...PYTHON_TOOL_EXCLUDE_PATTERNS,
    ],
  }
}
