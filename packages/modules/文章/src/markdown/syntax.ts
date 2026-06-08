import {
  Markdown提示块类型列表,
  Markdown自定义语法Schema,
} from '../markdown-schema'

export type 文章Markdown语法分类 = 'block' | 'inline' | 'fence' | 'metadata'

export interface 文章Markdown语法定义 {
  key: string
  name: string
  category: 文章Markdown语法分类
  description: string
  standardMarkdown: string
  attributes?: readonly string[]
}

export const 文章Markdown扩展语法定义列表 = [
  {
    key: 'horizontalRule',
    name: '水平线',
    category: 'block',
    description: '使用三个短横线输入水平分割线。',
    standardMarkdown: '---',
  },
  {
    key: 'codeFenceBacktick',
    name: '反引号代码围栏',
    category: 'fence',
    description: '使用三个反引号输入代码块。',
    standardMarkdown: '```ts\nconsole.log("hello")\n```',
  },
  {
    key: 'codeFenceTilde',
    name: '波浪号代码围栏',
    category: 'fence',
    description: '使用三个波浪号输入代码块。',
    standardMarkdown: '~~~ts\nconsole.log("hello")\n~~~',
  },
  {
    key: 'spoiler',
    name: '剧透文本',
    category: 'inline',
    description: Markdown自定义语法Schema.spoiler.description,
    standardMarkdown: ':spoiler[内容]',
  },
  {
    key: 'githubCard',
    name: 'GitHub 卡片',
    category: 'inline',
    description: Markdown自定义语法Schema.githubCard.description,
    standardMarkdown: '::github{repo="owner/repo"}',
    attributes: ['repo'],
  },
  {
    key: 'githubBlockquote',
    name: 'GitHub 风格提示块',
    category: 'block',
    description: Markdown自定义语法Schema.admonitions.githubBlockquote.description,
    standardMarkdown: '> [!NOTE]\n> 内容',
    attributes: ['type'],
  },
  {
    key: 'containerAdmonition',
    name: '容器提示块',
    category: 'block',
    description: Markdown自定义语法Schema.admonitions.container.description,
    standardMarkdown: ':::note[标题]\n内容\n:::',
    attributes: ['type', 'title'],
  },
  {
    key: 'indentedAdmonition',
    name: '缩进提示块',
    category: 'block',
    description: Markdown自定义语法Schema.admonitions.indented.description,
    standardMarkdown: '!!! note "标题"\n    内容',
    attributes: ['type', 'title'],
  },
  {
    key: 'detailsAdmonition',
    name: '折叠块',
    category: 'block',
    description: Markdown自定义语法Schema.admonitions.details.description,
    standardMarkdown: '??? note "标题"\n    内容',
    attributes: ['open', 'type', 'title'],
  },
  {
    key: 'imageGrid',
    name: '图片网格',
    category: 'block',
    description: Markdown自定义语法Schema.imageGrid.description,
    standardMarkdown: '[grid]\n![图片](https://example.com/a.png)\n[/grid]',
  },
  {
    key: 'codeFenceMetadata',
    name: '增强代码块元数据',
    category: 'metadata',
    description: '代码围栏 info 字符串支持标题、行号、高亮行、插入行、删除行、外框、换行和缩进保留。',
    standardMarkdown:
      '```ts title="示例" showLineNumbers highlight={1} ins={2} del={3} frame=code wrap preserveIndent\nconst a = 1\nconst b = 2\nconst c = 3\n```',
    attributes: Markdown自定义语法Schema.codeFence.metadata.map((item) => item.name),
  },
] as const satisfies readonly 文章Markdown语法定义[]

export const 文章Markdown提示块类型列表 = Markdown提示块类型列表
export const 文章Markdown代码块元数据定义列表 = Markdown自定义语法Schema.codeFence.metadata
export const 文章Markdown语法版本 = Markdown自定义语法Schema.version
