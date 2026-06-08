import { 文章Markdown扩展语法定义列表 } from './syntax'

export interface 文章Markdown示例 {
  key: string
  name: string
  markdown: string
  expectedHtmlIncludes: readonly string[]
}

export const 文章Markdown示例列表 = [
  {
    key: 'horizontalRule',
    name: '水平线',
    markdown: '---',
    expectedHtmlIncludes: ['<hr'],
  },
  {
    key: 'codeFenceBacktick',
    name: '反引号代码围栏',
    markdown: '```ts\nconsole.log("hello")\n```',
    expectedHtmlIncludes: ['article-code-block', 'language-ts'],
  },
  {
    key: 'codeFenceTilde',
    name: '波浪号代码围栏',
    markdown: '~~~ts\nconsole.log("hello")\n~~~',
    expectedHtmlIncludes: ['article-code-block', 'language-ts'],
  },
  {
    key: 'spoiler',
    name: '剧透文本',
    markdown: ':spoiler[内容]',
    expectedHtmlIncludes: ['class="spoiler"', '内容'],
  },
  {
    key: 'githubCard',
    name: 'GitHub 卡片',
    markdown: '::github{repo="owner/repo"}',
    expectedHtmlIncludes: ['card-github', 'data-github-repo="owner/repo"'],
  },
  {
    key: 'githubBlockquote',
    name: 'GitHub 风格提示块',
    markdown: '> [!NOTE]\n> 内容',
    expectedHtmlIncludes: ['blockquote', '[!NOTE]'],
  },
  {
    key: 'containerAdmonition',
    name: '容器提示块',
    markdown: ':::note[标题]\n内容\n:::',
    expectedHtmlIncludes: ['class="admonition bdm-note"', '标题'],
  },
  {
    key: 'indentedAdmonition',
    name: '缩进提示块',
    markdown: '!!! note "标题"\n    内容',
    expectedHtmlIncludes: ['class="admonition bdm-note"', '标题'],
  },
  {
    key: 'detailsAdmonition',
    name: '折叠块',
    markdown: '??? note "标题"\n    内容',
    expectedHtmlIncludes: ['<details', '标题'],
  },
  {
    key: 'imageGrid',
    name: '图片网格',
    markdown: '[grid]\n![图片](https://example.com/a.png)\n[/grid]',
    expectedHtmlIncludes: ['class="image-grid"', '<img'],
  },
  {
    key: 'codeFenceMetadata',
    name: '增强代码块元数据',
    markdown:
      '```ts title="示例" showLineNumbers highlight={1} ins={2} del={3} frame=code wrap preserveIndent\nconst a = 1\nconst b = 2\nconst c = 3\n```',
    expectedHtmlIncludes: ['article-code-title', 'data-line-numbers="true"', 'is-highlighted'],
  },
] as const satisfies readonly 文章Markdown示例[]

const 已定义语法键集合 = new Set(文章Markdown扩展语法定义列表.map((item) => item.key))

export const 缺失示例的文章Markdown语法键列表 = 文章Markdown扩展语法定义列表
  .map((item) => item.key)
  .filter((key) => !文章Markdown示例列表.some((example) => example.key === key))

export const 未定义语法的文章Markdown示例键列表 = 文章Markdown示例列表
  .map((example) => example.key)
  .filter((key) => !已定义语法键集合.has(key))
