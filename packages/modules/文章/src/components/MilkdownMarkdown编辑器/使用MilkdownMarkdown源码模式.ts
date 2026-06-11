import { nextTick, type Ref } from 'vue'
import { buildToolbarMarkdownSnippet } from './MilkdownMarkdown工具栏动作辅助'
import {
  getMarkdownHeadingShortcutLevel,
  isMarkdownStrongShortcut,
  type MarkdownHeadingLevel,
} from './MilkdownMarkdown快捷键'

export interface 使用MilkdownMarkdown源码模式选项 {
  sourceTextareaRef: Ref<HTMLTextAreaElement | null>
  sourceContent: Ref<string>
  lastMarkdown: Ref<string>
  insertMarkdown: (markdown: string) => void
  updateCursorStatus: () => void
  emitModelValue: (value: string) => void
}

export function 使用MilkdownMarkdown源码模式({
  sourceTextareaRef,
  sourceContent,
  lastMarkdown,
  insertMarkdown,
  updateCursorStatus,
  emitModelValue,
}: 使用MilkdownMarkdown源码模式选项) {
  function handleSourceInput() {
    lastMarkdown.value = sourceContent.value
    updateCursorStatus()
    emitModelValue(sourceContent.value)
  }

  function handleSourceKeydown(event: KeyboardEvent) {
    const headingLevel = getMarkdownHeadingShortcutLevel(event)
    if (headingLevel) {
      event.preventDefault()
      toggleSourceHeading(headingLevel)
      return
    }

    if (isMarkdownStrongShortcut(event)) {
      event.preventDefault()
      toggleSourceStrong()
    }
  }

  function toggleSourceHeading(level: MarkdownHeadingLevel) {
    const textarea = sourceTextareaRef.value
    if (!textarea) {
      insertMarkdown(`${'\n'}${'#'.repeat(level)} 标题\n`)
      return
    }

    const selectionStart = Math.min(textarea.selectionStart, textarea.selectionEnd)
    const selectionEnd = Math.max(textarea.selectionStart, textarea.selectionEnd)
    const lineRange = 获取源码选区行范围(sourceContent.value, selectionStart, selectionEnd)
    const originalLinesText = sourceContent.value.slice(lineRange.start, lineRange.end)
    const originalLines = originalLinesText.split('\n')
    const shouldRemoveHeading = 源码行列表全是指定级别标题(originalLines, level)
    const nextLines = originalLines.map((line) => 切换源码标题行(line, level, shouldRemoveHeading))
    const nextLinesText = nextLines.join('\n')

    sourceContent.value = [
      sourceContent.value.slice(0, lineRange.start),
      nextLinesText,
      sourceContent.value.slice(lineRange.end),
    ].join('')
    handleSourceInput()

    const nextSelectionStart = 计算源码标题切换后选区位置(
      sourceContent.value,
      lineRange.start,
      selectionStart,
      level,
      shouldRemoveHeading,
    )
    const nextSelectionEnd = Math.max(
      nextSelectionStart,
      selectionEnd + nextLinesText.length - originalLinesText.length,
    )

    void nextTick(() => {
      textarea.focus({ preventScroll: true })
      textarea.setSelectionRange(nextSelectionStart, nextSelectionEnd)
      updateCursorStatus()
    })
  }

  function toggleSourceStrong() {
    const textarea = sourceTextareaRef.value
    if (!textarea) {
      insertMarkdown(buildToolbarMarkdownSnippet('strong'))
      return
    }

    const selectionStart = Math.min(textarea.selectionStart, textarea.selectionEnd)
    const selectionEnd = Math.max(textarea.selectionStart, textarea.selectionEnd)
    const selectedText = sourceContent.value.slice(selectionStart, selectionEnd)
    const nextText = selectedText || '加粗文本'
    sourceContent.value = [
      sourceContent.value.slice(0, selectionStart),
      `**${nextText}**`,
      sourceContent.value.slice(selectionEnd),
    ].join('')
    handleSourceInput()

    void nextTick(() => {
      textarea.focus({ preventScroll: true })
      const contentStart = selectionStart + 2
      const contentEnd = contentStart + nextText.length
      textarea.setSelectionRange(contentStart, contentEnd)
      updateCursorStatus()
    })
  }

  function updateSourceSelectionStatus() {
    updateCursorStatus()
  }

  return {
    handleSourceInput,
    handleSourceKeydown,
    toggleSourceHeading,
    toggleSourceStrong,
    updateSourceSelectionStatus,
  }
}

export function 获取源码选区行范围(
  source: string,
  selectionStart: number,
  selectionEnd: number,
) {
  const lineStart = source.lastIndexOf('\n', Math.max(0, selectionStart - 1)) + 1
  const normalizedSelectionEnd = selectionEnd > selectionStart && source[selectionEnd - 1] === '\n'
    ? selectionEnd - 1
    : selectionEnd
  const nextLineBreak = source.indexOf('\n', normalizedSelectionEnd)
  return {
    start: lineStart,
    end: nextLineBreak === -1 ? source.length : nextLineBreak,
  }
}

export function 源码行列表全是指定级别标题(
  lines: string[],
  level: MarkdownHeadingLevel,
): boolean {
  const contentLines = lines.filter((line) => line.trim().length > 0)
  return contentLines.length > 0
    && contentLines.every((line) => 获取源码标题级别(line) === level)
}

export function 切换源码标题行(
  line: string,
  level: MarkdownHeadingLevel,
  shouldRemoveHeading: boolean,
): string {
  const match = line.match(/^(\s*)(#{1,6})([ \t]+)(.*)$/)
  if (shouldRemoveHeading) {
    if (!match) {
      return line
    }

    return `${match[1] ?? ''}${match[4] ?? ''}`
  }

  const headingPrefix = '#'.repeat(level)
  if (match) {
    return `${match[1] ?? ''}${headingPrefix}${match[3] ?? ' '}${match[4] ?? ''}`
  }

  if (line.trim().length === 0) {
    return `${line}${headingPrefix} `
  }

  const indentMatch = line.match(/^(\s*)(.*)$/)
  return `${indentMatch?.[1] ?? ''}${headingPrefix} ${indentMatch?.[2] ?? line}`
}

export function 获取源码标题级别(line: string): MarkdownHeadingLevel | null {
  const match = line.match(/^\s*(#{1,6})(?:[ \t]+|$)/)
  const level = match?.[1]?.length ?? 0
  if (level >= 1 && level <= 6) {
    return level as MarkdownHeadingLevel
  }

  return null
}

export function 计算源码标题切换后选区位置(
  nextSource: string,
  lineRangeStart: number,
  originalPosition: number,
  level: MarkdownHeadingLevel,
  shouldRemoveHeading: boolean,
): number {
  const lineStart = nextSource.lastIndexOf('\n', Math.max(0, originalPosition - 1)) + 1
  if (originalPosition > lineRangeStart && originalPosition !== lineStart) {
    return originalPosition
  }

  if (shouldRemoveHeading) {
    return lineStart
  }

  return Math.min(nextSource.length, lineStart + level + 1)
}
