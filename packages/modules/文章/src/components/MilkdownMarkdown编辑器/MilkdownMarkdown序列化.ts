import {
  GitHub卡片语法名称,
  标签页压缩代码块正则,
  标签页标题正则,
  标签页标题转义正则,
  代码围栏边界正则,
  剧透语法名称,
  图片网格标记转义正则,
  容器提示块标题方括号转义正则,
  容器提示块标题正则,
  容器提示块结束正则,
  扩展块标题正则,
  扩展块标题转义正则,
  星号水平线正则,
  星号紧凑水平线正则,
  转义Emoji短码正则,
  转义GitHub卡片正则,
  转义GitHub提示块正文正则,
  转义代码围栏边界正则,
  转义剧透文本正则,
  转义块级数学围栏全局正则,
  转义缩写定义正则,
  转义行内数学正则,
  转义图片语法正则,
  容器提示块标题转义正则,
} from './MilkdownMarkdown语法常量'

export function normalizeSerializedMarkdown(markdown: string): string {
  const normalizedMarkdown = markdown
    .replace(标签页压缩代码块正则, (_match, title: string, language: string, content: string) => {
      const fence = '```'
      const normalizedContent = content.trim()
      return [
        `=== "${title}"`,
        `    ${fence}${language}`,
        `    ${normalizedContent}`,
        `    ${fence}`,
      ].join('\n')
    })
    .replace(标签页标题转义正则, '$1')
    .replace(转义块级数学围栏全局正则, () => '$$')
    .replace(转义行内数学正则, (_match, prefix: string, content: string) => `${prefix}$${content}$`)
    .replace(转义缩写定义正则, '*[$1]:$2')
    .replace(转义GitHub提示块正文正则, '[!$1]')
    .replace(转义图片语法正则, normalizeSerializedMarkdownImage)
    .replace(转义剧透文本正则, `:${剧透语法名称}[$1]`)
    .replace(转义GitHub卡片正则, `::${GitHub卡片语法名称}{repo="$1"}`)
    .replace(
      转义Emoji短码正则,
      (_match, shortcode: string) => `:${shortcode.replace(/\\_/g, '_')}:`,
    )

  return normalizeSerializedMarkdownBlocks(normalizeSerializedMarkdownMarkers(normalizedMarkdown))
}

function normalizeSerializedMarkdownImage(match: string): string {
  const 图片标记被转义 = match.startsWith('\\!') || match.startsWith('!\\[') || match.includes('\\](') || match.includes('\\]\\(')
  if (!图片标记被转义) {
    return match
  }

  return match.replaceAll(/\\([!()[\]])/g, '$1')
}

function normalizeSerializedMarkdownMarkers(markdown: string): string {
  const lines = markdown.split('\n')
  let fence: { marker: string, length: number, indent: string } | null = null

  return lines.map((line) => {
    const markerLine = normalizeSerializedMarkdownFenceMarker(line)
    const fenceMatch = markerLine.match(代码围栏边界正则)

    if (fence) {
      if (
        fenceMatch
        && fenceMatch[1] === fence.indent
        && fenceMatch[2]?.startsWith(fence.marker.repeat(fence.length))
      ) {
        fence = null
        return markerLine
      }

      return line
    }

    if (fenceMatch) {
      const markerText = fenceMatch[2] ?? ''
      fence = {
        marker: markerText[0] ?? '',
        length: markerText.length,
        indent: fenceMatch[1] ?? '',
      }
      return markerLine
    }

    if (星号水平线正则.test(line) || 星号紧凑水平线正则.test(line)) {
      return `${line.match(/^\s*/)?.[0] ?? ''}---`
    }

    return line.replace(/^(\s*)\*(?=[ \t]+(?:\S|$))/, '$1-')
  }).join('\n')
}

function normalizeSerializedMarkdownBlocks(markdown: string): string {
  const lines = markdown.split('\n')
  const normalizedLines: string[] = []
  let fence: { marker: string, length: number, indent: string } | null = null
  let extendedBlock: { indent: string, bodyIndent: string } | null = null
  let containerBlock: { indent: string } | null = null

  for (const rawLine of lines) {
    const line = normalizeSerializedMarkdownBlockMarkers(rawLine)
    const fenceMatch = line.match(代码围栏边界正则)

    if (fence) {
      const normalizedFenceLine = containerBlock
        ? line
        : normalizeSerializedMarkdownBlockBodyLine(line, extendedBlock)
      normalizedLines.push(normalizedFenceLine)
      if (
        fenceMatch
        && normalizeSerializedMarkdownFenceIndent(fenceMatch[1] ?? '', extendedBlock, containerBlock) === fence.indent
        && fenceMatch[2]?.startsWith(fence.marker.repeat(fence.length))
      ) {
        fence = null
      }
      continue
    }

    if (fenceMatch) {
      const markerText = fenceMatch[2] ?? ''
      const normalizedFenceLine = containerBlock
        ? line
        : normalizeSerializedMarkdownBlockBodyLine(line, extendedBlock)
      const normalizedFenceMatch = normalizedFenceLine.match(代码围栏边界正则)
      fence = {
        marker: markerText[0] ?? '',
        length: markerText.length,
        indent: normalizedFenceMatch?.[1] ?? fenceMatch[1] ?? '',
      }
      normalizedLines.push(normalizedFenceLine)
      continue
    }

    if (containerBlock && 容器提示块结束正则.test(line)) {
      normalizedLines.push(`${containerBlock.indent}:::`)
      containerBlock = null
      continue
    }

    const containerTitleMatch = line.match(容器提示块标题正则)
    if (containerTitleMatch) {
      containerBlock = {
        indent: containerTitleMatch[1] ?? '',
      }
      extendedBlock = null
      normalizedLines.push(line)
      continue
    }

    const blockTitleMatch = line.match(扩展块标题正则) ?? line.match(标签页标题正则)
    if (blockTitleMatch) {
      const indent = blockTitleMatch[1] ?? ''
      extendedBlock = {
        indent,
        bodyIndent: `${indent}    `,
      }
      normalizedLines.push(line)
      continue
    }

    if (line.trim().length === 0) {
      if (!containerBlock) {
        extendedBlock = null
      }
      normalizedLines.push(line)
      continue
    }

    normalizedLines.push(containerBlock ? line : normalizeSerializedMarkdownBlockBodyLine(line, extendedBlock))
  }

  return normalizedLines.join('\n')
}

function normalizeSerializedMarkdownBlockMarkers(line: string): string {
  const normalizedLine = line
    .replace(转义代码围栏边界正则, '$1$2')
    .replace(扩展块标题转义正则, '$1$2$3')
    .replace(容器提示块标题转义正则, '$1:::$2')
    .replace(图片网格标记转义正则, '[$1]')

  if (!/^(\s*):::[A-Za-z][\w-]*/.test(normalizedLine)) {
    return normalizedLine
  }

  return normalizedLine.replace(容器提示块标题方括号转义正则, '$1')
}

function normalizeSerializedMarkdownFenceMarker(line: string): string {
  return line.replace(转义代码围栏边界正则, '$1$2')
}

function normalizeSerializedMarkdownFenceIndent(
  indent: string,
  extendedBlock: { bodyIndent: string } | null,
  containerBlock: { indent: string } | null,
): string {
  if (containerBlock) {
    return indent
  }

  return normalizeSerializedMarkdownBlockBodyLine(indent, extendedBlock)
}

function normalizeSerializedMarkdownBlockBodyLine(
  line: string,
  extendedBlock: { bodyIndent: string } | null,
): string {
  if (!extendedBlock || line.startsWith(extendedBlock.bodyIndent)) {
    return line
  }

  return `${extendedBlock.bodyIndent}${line.trimStart()}`
}
