export function 从Markdown首行提取文章标题(content: string): string {
  const firstNonEmptyLine = content
    .replace(/^\uFEFF/u, '')
    .split(/\r?\n/u)
    .find((line) => line.trim().length > 0)
    ?.trim() ?? ''

  if (!firstNonEmptyLine) {
    return ''
  }

  let title = firstNonEmptyLine
  let previousTitle = ''
  while (title && title !== previousTitle) {
    previousTitle = title
    title = title.replace(/^(?:>\s*)+/u, '').trim()
    title = title.replace(/^#{1,6}(?:\s+|$)/u, '').trim()
  }

  return title.replace(/\s+#{1,}\s*$/u, '').trim()
}
