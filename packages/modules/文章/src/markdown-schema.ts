export type Markdown代码块框架 = 'code' | 'terminal' | 'none'

export interface Markdown提示块类型Schema {
  name: string
  defaultTitle: string
}

export interface Markdown代码块元数据Schema {
  name: string
  aliases: readonly string[]
  valueType: 'boolean' | 'enum' | 'line-ranges' | 'number' | 'string'
  description: string
  allowedValues?: readonly string[]
}

export interface Markdown自定义语法Schema定义 {
  version: string
  admonitions: {
    types: readonly Markdown提示块类型Schema[]
    githubBlockquote: {
      pattern: string
      description: string
    }
    container: {
      startPattern: string
      endPattern: string
      description: string
    }
    indented: {
      startPattern: string
      description: string
    }
    details: {
      startPattern: string
      description: string
    }
  }
  tabs: {
    itemPattern: string
    description: string
  }
  imageGrid: {
    openMarker: string
    closeMarker: string
    description: string
  }
  githubCard: {
    pattern: string
    repoPattern: string
    description: string
  }
  spoiler: {
    pattern: string
    description: string
  }
  mermaid: {
    language: string
    description: string
  }
  codeFence: {
    frames: readonly Markdown代码块框架[]
    defaultFrame: Markdown代码块框架
    defaultLanguage: string
    autoCollapseLines: number
    metadata: readonly Markdown代码块元数据Schema[]
  }
}

export const Markdown自定义语法Schema = {
  version: '1.0.0',
  admonitions: {
    types: [
      { name: 'note', defaultTitle: 'Note' },
      { name: 'tip', defaultTitle: 'Tip' },
      { name: 'important', defaultTitle: 'Important' },
      { name: 'warning', defaultTitle: 'Warning' },
      { name: 'caution', defaultTitle: 'Caution' },
      { name: 'abstract', defaultTitle: 'Abstract' },
      { name: 'summary', defaultTitle: 'Summary' },
      { name: 'tldr', defaultTitle: 'TL;DR' },
      { name: 'info', defaultTitle: 'Info' },
      { name: 'todo', defaultTitle: 'Todo' },
      { name: 'success', defaultTitle: 'Success' },
      { name: 'check', defaultTitle: 'Check' },
      { name: 'done', defaultTitle: 'Done' },
      { name: 'question', defaultTitle: 'Question' },
      { name: 'help', defaultTitle: 'Help' },
      { name: 'faq', defaultTitle: 'FAQ' },
      { name: 'attention', defaultTitle: 'Attention' },
      { name: 'failure', defaultTitle: 'Failure' },
      { name: 'missing', defaultTitle: 'Missing' },
      { name: 'fail', defaultTitle: 'Fail' },
      { name: 'danger', defaultTitle: 'Danger' },
      { name: 'error', defaultTitle: 'Error' },
      { name: 'bug', defaultTitle: 'Bug' },
      { name: 'example', defaultTitle: 'Example' },
      { name: 'quote', defaultTitle: 'Quote' },
      { name: 'cite', defaultTitle: 'Cite' },
    ],
    githubBlockquote: {
      pattern: '^\\[!(\\w+)]\\s*(.*)$',
      description: '引用块首段以 [!TYPE] 开头时转换为 GitHub 风格提示块。',
    },
    container: {
      startPattern: '^:::([A-Za-z][\\w-]*)(?:\\[((?:[^\\]\\\\]|\\\\.)*)])?$',
      endPattern: '^:::$',
      description: ':::type[title] 到 ::: 之间的内容渲染为提示块。',
    },
    indented: {
      startPattern: '^!!!\\s+([a-zA-Z][\\w-]*)(?:\\s+"((?:[^"\\\\]|\\\\.)+)")?\\s*$',
      description: '!!! type "title" 后的缩进内容渲染为提示块。',
    },
    details: {
      startPattern: '^(\\?\\?\\?\\+?)\\s+([a-zA-Z][\\w-]*)(?:\\s+"((?:[^"\\\\]|\\\\.)+)")?\\s*$',
      description: '??? type "title" 或 ???+ type "title" 后的缩进内容渲染为折叠块。',
    },
  },
  tabs: {
    itemPattern: '^===\\s+"((?:[^"\\\\]|\\\\.)+)"\\s*$',
    description: '连续的 === "title" 缩进块渲染为同一组标签页。',
  },
  imageGrid: {
    openMarker: '[grid]',
    closeMarker: '[/grid]',
    description: '[grid] 与 [/grid] 包裹的 Markdown 渲染为图片网格。',
  },
  githubCard: {
    pattern: '::github\\{repo="([^"]+)"\\}',
    repoPattern: '^[^/\\s]+/[^/\\s]+$',
    description: '::github{repo="owner/repo"} 渲染为 GitHub 仓库卡片。',
  },
  spoiler: {
    pattern: ':spoiler\\[((?:[^\\]\\\\]|\\\\.)*)]',
    description: ':spoiler[content] 渲染为点击或悬停显示的剧透文本。',
  },
  mermaid: {
    language: 'mermaid',
    description: 'mermaid 语言代码块渲染为可缩放图表。',
  },
  codeFence: {
    frames: ['code', 'terminal', 'none'],
    defaultFrame: 'code',
    defaultLanguage: 'text',
    autoCollapseLines: 18,
    metadata: [
      {
        name: 'title',
        aliases: ['title'],
        valueType: 'string',
        description: '代码块标题。',
      },
      {
        name: 'highlight',
        aliases: ['highlight'],
        valueType: 'line-ranges',
        description: '高亮行范围。',
      },
      {
        name: 'lineNumbers',
        aliases: ['showLineNumbers', 'lineNumbers', 'linenos', 'ln'],
        valueType: 'boolean',
        description: '显示行号。',
      },
      {
        name: 'startLineNumber',
        aliases: ['startLineNumber', 'startLine', 'lineNumberStart'],
        valueType: 'number',
        description: '起始行号。',
      },
      {
        name: 'ins',
        aliases: ['ins'],
        valueType: 'line-ranges',
        description: '新增行范围。',
      },
      {
        name: 'del',
        aliases: ['del'],
        valueType: 'line-ranges',
        description: '删除行范围。',
      },
      {
        name: 'frame',
        aliases: ['frame'],
        valueType: 'enum',
        allowedValues: ['code', 'terminal', 'none'],
        description: '代码块外框样式。',
      },
      {
        name: 'wrap',
        aliases: ['wrap'],
        valueType: 'boolean',
        description: '长行自动换行。',
      },
      {
        name: 'preserveIndent',
        aliases: ['preserveIndent'],
        valueType: 'boolean',
        description: '换行时保留缩进视觉宽度。',
      },
    ],
  },
} as const satisfies Markdown自定义语法Schema定义

export const Markdown提示块类型列表 = Markdown自定义语法Schema.admonitions.types.map(
  (item) => item.name,
)

export const Markdown提示块类型集合: ReadonlySet<string> = new Set(Markdown提示块类型列表)

export const Markdown提示块大写类型集合: ReadonlySet<string> = new Set(
  Markdown提示块类型列表.map((type) => type.toUpperCase()),
)

export const Markdown提示块默认标题映射 = Object.fromEntries(
  Markdown自定义语法Schema.admonitions.types.map((item) => [item.name, item.defaultTitle]),
) as Record<string, string>

export const Markdown标签页匹配正则 = new RegExp(Markdown自定义语法Schema.tabs.itemPattern)
export const Markdown缩进提示块匹配正则 = new RegExp(
  Markdown自定义语法Schema.admonitions.indented.startPattern,
)
export const Markdown折叠块匹配正则 = new RegExp(
  Markdown自定义语法Schema.admonitions.details.startPattern,
)
export const Markdown容器提示块起始正则 = new RegExp(
  Markdown自定义语法Schema.admonitions.container.startPattern,
)
export const Markdown容器提示块结束正则 = new RegExp(
  Markdown自定义语法Schema.admonitions.container.endPattern,
)
export const MarkdownGithub提示块正则 = new RegExp(
  Markdown自定义语法Schema.admonitions.githubBlockquote.pattern,
)
export const MarkdownGithub卡片正则 = new RegExp(
  Markdown自定义语法Schema.githubCard.pattern,
  'g',
)
export const Markdown仓库名称正则 = new RegExp(Markdown自定义语法Schema.githubCard.repoPattern)
export const Markdown剧透文本正则 = new RegExp(Markdown自定义语法Schema.spoiler.pattern, 'g')

export function 获取Markdown代码块元数据Schema(name: string): Markdown代码块元数据Schema | null {
  return Markdown自定义语法Schema.codeFence.metadata.find((item) => item.name === name) ?? null
}
