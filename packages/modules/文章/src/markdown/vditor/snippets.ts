export type VditorMermaid图表类型 =
  | 'flow'
  | 'sequence'
  | 'gantt'
  | 'class'
  | 'state'
  | 'pie'
  | 'relationship'
  | 'journey'

export type Vditor公式类型 = 'inline' | 'block'

export function 构建VditorMermaid代码片段(type: VditorMermaid图表类型): string {
  const snippets: Record<VditorMermaid图表类型, string> = {
    flow: 'graph TD\n  A[开始] --> B[结束]',
    sequence: 'sequenceDiagram\n  Alice->>Bob: 你好\n  Bob-->>Alice: 收到',
    gantt: 'gantt\n  title 计划\n  dateFormat  YYYY-MM-DD\n  任务一 :a1, 2026-01-01, 3d',
    class: 'classDiagram\n  class Article\n  Article : string title',
    state: 'stateDiagram-v2\n  [*] --> 草稿\n  草稿 --> 发布',
    pie: 'pie title 占比\n  "写作" : 60\n  "整理" : 40',
    relationship: 'erDiagram\n  ARTICLE ||--o{ TAG : has',
    journey: 'journey\n  title 写作流程\n  section 准备\n    构思: 5: 我',
  }

  return `\n\`\`\`mermaid\n${snippets[type]}\n\`\`\`\n`
}

export function 构建Vditor公式代码片段(type: Vditor公式类型): string {
  return type === 'block'
    ? '\n$$\nE = mc^2\n$$\n'
    : '$E = mc^2$'
}
