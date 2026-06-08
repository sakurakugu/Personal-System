declare module 'markdown-it-abbr' {
  import type MarkdownIt from 'markdown-it'

  const plugin: (md: MarkdownIt, ...params: unknown[]) => void
  export default plugin
}
