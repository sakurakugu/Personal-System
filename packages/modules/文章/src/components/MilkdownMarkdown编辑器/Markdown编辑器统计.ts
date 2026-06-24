export interface Markdown编辑器统计信息 {
  lines: number
  words: number
  characters: number
}

export interface Markdown编辑器光标状态 {
  line: number
  selectedWords: number
  selectedCharacters: number
}

export function buildEditorStats(markdown: string): Markdown编辑器统计信息 {
  const normalizedMarkdown = markdown.replace(/\r\n/g, '\n')
  const lines = normalizedMarkdown.length === 0 ? 1 : normalizedMarkdown.split('\n').length
  const visibleText = normalizedMarkdown
    .replace(/```[\s\S]*?```/g, '')
    .replace(/`([^`]+)`/g, '$1')
    .replace(/!\[[^\]]*]\([^)]+\)/g, '')
    .replace(/\[([^\]]+)]\([^)]+\)/g, '$1')
    .replace(/[#>*_~`[\]()|:-]/g, ' ')
  const chineseCharacterCount = visibleText.match(/[\u4e00-\u9fff]/g)?.length ?? 0
  const latinWordCount = visibleText.match(/[A-Za-z0-9]+(?:[-_'][A-Za-z0-9]+)*/g)?.length ?? 0

  return {
    lines,
    words: chineseCharacterCount + latinWordCount,
    characters: Array.from(markdown).length,
  }
}

export function buildCursorStatusFromOffsets(
  markdown: string,
  startOffset: number,
  endOffset: number,
): Markdown编辑器光标状态 {
  const normalizedStartOffset = Math.min(markdown.length, Math.max(0, startOffset))
  const normalizedEndOffset = Math.min(markdown.length, Math.max(0, endOffset))
  const selectionStart = Math.min(normalizedStartOffset, normalizedEndOffset)
  const selectionEnd = Math.max(normalizedStartOffset, normalizedEndOffset)
  const beforeCursor = markdown.slice(0, normalizedStartOffset).replace(/\r\n/g, '\n')
  const selectedText = markdown.slice(selectionStart, selectionEnd)

  return {
    line: beforeCursor.length === 0 ? 1 : beforeCursor.split('\n').length,
    selectedWords: countReadableWords(selectedText),
    selectedCharacters: Array.from(selectedText).length,
  }
}

export function buildCursorStatusFromText(
  beforeCursor: string,
  selectedText: string,
): Markdown编辑器光标状态 {
  const normalizedBeforeCursor = beforeCursor.replace(/\r\n/g, '\n')
  return {
    line: normalizedBeforeCursor.length === 0 ? 1 : normalizedBeforeCursor.split('\n').length,
    selectedWords: countReadableWords(selectedText),
    selectedCharacters: Array.from(selectedText).length,
  }
}

function countReadableWords(text: string): number {
  const chineseCharacterCount = text.match(/[\u4e00-\u9fff]/g)?.length ?? 0
  const latinWordCount = text.match(/[A-Za-z0-9]+(?:[-_'][A-Za-z0-9]+)*/g)?.length ?? 0
  return chineseCharacterCount + latinWordCount
}
