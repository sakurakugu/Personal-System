export interface Vditor换行插入结果 {
  markdown: string
  cursorOffset: number
}

function 规范化偏移量(markdown: string, cursorOffset: number): number {
  if (!Number.isFinite(cursorOffset)) {
    return markdown.length
  }

  return Math.min(markdown.length, Math.max(0, Math.trunc(cursorOffset)))
}

export function 插入Vditor源码换行(
  markdown: string,
  cursorOffset: number,
  endOffset = cursorOffset,
): Vditor换行插入结果 {
  const normalizedStartOffset = 规范化偏移量(markdown, cursorOffset)
  const normalizedEndOffset = 规范化偏移量(markdown, endOffset)
  const normalizedMarkdown = markdown.replace(/\r\n/g, '\n')
  const selectionStartOffset = Math.min(normalizedStartOffset, normalizedEndOffset)
  const selectionEndOffset = Math.max(normalizedStartOffset, normalizedEndOffset)
  const startOffsetDelta = markdown.slice(0, selectionStartOffset).length
    - markdown.slice(0, selectionStartOffset).replace(/\r\n/g, '\n').length
  const endOffsetDelta = markdown.slice(0, selectionEndOffset).length
    - markdown.slice(0, selectionEndOffset).replace(/\r\n/g, '\n').length
  const insertOffset = Math.max(0, selectionStartOffset - startOffsetDelta)
  const replaceEndOffset = Math.max(insertOffset, selectionEndOffset - endOffsetDelta)

  return {
    markdown: `${normalizedMarkdown.slice(0, insertOffset)}\n${normalizedMarkdown.slice(replaceEndOffset)}`,
    cursorOffset: insertOffset + 1,
  }
}
