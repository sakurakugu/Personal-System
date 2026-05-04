declare module 'markdown-it-mark' {
  import type MarkdownIt from 'markdown-it'

  const plugin: (md: MarkdownIt) => void
  export default plugin
}

declare module 'markdown-it-emoji' {
  import type MarkdownIt from 'markdown-it'

  export const bare: (md: MarkdownIt, options?: Record<string, unknown>) => void
  export const light: (md: MarkdownIt, options?: Record<string, unknown>) => void
  export const full: (md: MarkdownIt, options?: Record<string, unknown>) => void
}

declare module 'markdown-it-task-lists' {
  import type MarkdownIt from 'markdown-it'

  interface TaskListOptions {
    enabled?: boolean
    label?: boolean
    labelAfter?: boolean
  }

  const plugin: (md: MarkdownIt, options?: TaskListOptions) => void
  export = plugin
}

declare module 'markdown-it-footnote' {
  import type MarkdownIt from 'markdown-it'

  const plugin: (md: MarkdownIt) => void
  export default plugin
}

declare module 'markdown-it-abbr' {
  import type MarkdownIt from 'markdown-it'

  const plugin: (md: MarkdownIt) => void
  export default plugin
}
