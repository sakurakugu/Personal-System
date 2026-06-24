import { Markdown自定义语法Schema } from '../../markdown-schema'

export type CustomMarkdownSnippet =
  | 'github-alert-note'
  | 'github-alert-tip'
  | 'github-alert-important'
  | 'github-alert-warning'
  | 'github-alert-caution'
  | 'github-alert-syntax'
  | 'container-alert'
  | 'indented-alert'
  | 'details-alert-collapsed'
  | 'details-alert-expanded'
  | 'tabs'
  | 'image-grid'
  | 'github-card'
  | 'code-syntax'
  | 'spoiler'

const GitHub提示块中文标题映射: Record<string, string> = {
  NOTE: '说明',
  TIP: '提示',
  IMPORTANT: '重要',
  WARNING: '警告',
  CAUTION: '注意',
  ABSTRACT: '摘要',
  SUMMARY: '总结',
  TLDR: '太长不看',
  INFO: '信息',
  TODO: '待办',
  SUCCESS: '成功',
  CHECK: '检查',
  DONE: '完成',
  QUESTION: '问题',
  HELP: '帮助',
  FAQ: '常见问题',
  ATTENTION: '注意',
  FAILURE: '失败',
  MISSING: '缺失',
  FAIL: '失败',
  DANGER: '危险',
  ERROR: '错误',
  BUG: '缺陷',
  EXAMPLE: '示例',
  QUOTE: '引用',
  CITE: '引用',
}

export function normalizeCustomMarkdownSnippet(payload?: string | number): CustomMarkdownSnippet | null {
  if (typeof payload !== 'string') {
    return null
  }

  const snippets: readonly CustomMarkdownSnippet[] = [
    'github-alert-note',
    'github-alert-tip',
    'github-alert-important',
    'github-alert-warning',
    'github-alert-caution',
    'github-alert-syntax',
    'container-alert',
    'indented-alert',
    'details-alert-collapsed',
    'details-alert-expanded',
    'tabs',
    'image-grid',
    'github-card',
    'code-syntax',
    'spoiler',
  ]
  return snippets.includes(payload as CustomMarkdownSnippet) ? payload as CustomMarkdownSnippet : null
}

export function buildCustomMarkdownSnippet(type: CustomMarkdownSnippet): string {
  switch (type) {
    case 'github-alert-note':
      return buildGithubAlertSnippet('NOTE')
    case 'github-alert-tip':
      return buildGithubAlertSnippet('TIP')
    case 'github-alert-important':
      return buildGithubAlertSnippet('IMPORTANT')
    case 'github-alert-warning':
      return buildGithubAlertSnippet('WARNING')
    case 'github-alert-caution':
      return buildGithubAlertSnippet('CAUTION')
    case 'github-alert-syntax':
      return ''
    case 'container-alert':
      return '\n:::tip[提示标题]\n这里是容器式提示块内容。\n:::\n'
    case 'indented-alert':
      return '\n!!! note "提示标题"\n    这里是缩进式提示块内容。\n'
    case 'details-alert-collapsed':
      return '\n??? warning "折叠标题"\n    这里是默认收起的折叠块内容。\n'
    case 'details-alert-expanded':
      return '\n???+ info "折叠标题"\n    这里是默认展开的折叠块内容。\n'
    case 'tabs':
      return '\n=== "方案一"\n    这里是方案一内容。\n\n=== "方案二"\n    这里是方案二内容。\n'
    case 'image-grid':
      return '\n[grid]\n![图片一](https://example.com/image-1.png)\n![图片二](https://example.com/image-2.png)\n[/grid]\n'
    case 'code-syntax':
      return ''
    case 'spoiler':
      return ':spoiler[这里是剧透内容]'
    case 'github-card':
      return ''
  }
}

export function buildGithubAlertSyntaxSnippet(): string {
  const commonTypes = ['NOTE', 'TIP', 'IMPORTANT', 'WARNING', 'CAUTION']
  const otherTypes = Markdown自定义语法Schema.admonitions.types
    .map((item) => item.name.toUpperCase())
    .filter((type) => !commonTypes.includes(type))
  const commonTypeText = commonTypes.map(formatGithubAlertTypeLabel).join('、')
  const otherTypeText = otherTypes.map(formatGithubAlertTypeLabel).join('、')

  return [
    '> [!NOTE]',
    '> GitHub 风格提示块：把 [!TYPE] 放在引用块第一行。',
    '',
    `常用类型：${commonTypeText}`,
    `其他类型：${otherTypeText}`,
    '',
  ].join('\n')
}

export function buildCodeSyntaxSnippet(): string {
  const metadataLines = Markdown自定义语法Schema.codeFence.metadata
    .map((item) => `// ${item.aliases.join('/')}：${item.description}`)
    .join('\n')

  return [
    '',
    '```ts title="代码标题" ln startLine=1 highlight={2,4-5} ins={6} del={7} frame=terminal wrap preserveIndent',
    metadataLines,
    'console.log("增强代码块")',
    '```',
    '',
  ].join('\n')
}

export function buildMermaidSnippet(type: string): string {
  const snippets: Record<string, string> = {
    flow: 'graph TD\n  A[开始] --> B[结束]',
    sequence: 'sequenceDiagram\n  Alice->>Bob: 你好\n  Bob-->>Alice: 收到',
    gantt: 'gantt\n  title 计划\n  dateFormat  YYYY-MM-DD\n  任务一 :a1, 2026-01-01, 3d',
    class: 'classDiagram\n  class Article\n  Article : string title',
    state: 'stateDiagram-v2\n  [*] --> 草稿\n  草稿 --> 发布',
    pie: 'pie title 占比\n  "写作" : 60\n  "整理" : 40',
    relationship: 'erDiagram\n  ARTICLE ||--o{ TAG : has',
    journey: 'journey\n  title 写作流程\n  section 准备\n    构思: 5: 我',
  }
  return `\n\`\`\`mermaid\n${snippets[type] ?? snippets.flow}\n\`\`\`\n`
}

function buildGithubAlertSnippet(type: string): string {
  return `\n> [!${type}]\n> 这里是${获取GitHub提示块中文标题(type)}提示块内容。\n`
}

function formatGithubAlertTypeLabel(type: string): string {
  return `${获取GitHub提示块中文标题(type)}（${type}）`
}

function 获取GitHub提示块中文标题(type: string): string {
  const normalizedType = type.toUpperCase().replace(/[^A-Z0-9]/g, '')
  return GitHub提示块中文标题映射[normalizedType] ?? type
}
