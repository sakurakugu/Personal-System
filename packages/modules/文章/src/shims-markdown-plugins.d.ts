declare module 'markdown-it-abbr' {
  import type MarkdownIt from 'markdown-it'

  const plugin: (md: MarkdownIt, ...params: unknown[]) => void
  export default plugin
}

declare module 'markdown-it-emoji' {
  import type MarkdownIt from 'markdown-it'

  export const full: (md: MarkdownIt, ...params: unknown[]) => void
  const pluginNamespace: {
    full?: typeof full
    default?: (md: MarkdownIt, ...params: unknown[]) => void
  }
  export default pluginNamespace
}

declare module 'markdown-it-emoji/lib/data/full.mjs' {
  const emoji: Record<string, string>
  export default emoji
}

declare module 'markdown-it-emoji/lib/data/light.mjs' {
  const emoji: Record<string, string>
  export default emoji
}

declare module 'markdown-it-emoji/lib/data/shortcuts.mjs' {
  const shortcuts: Record<string, string[]>
  export default shortcuts
}

declare module 'markdown-it-footnote' {
  import type MarkdownIt from 'markdown-it'

  const plugin: (md: MarkdownIt, ...params: unknown[]) => void
  export default plugin
}

declare module 'markdown-it-mark' {
  import type MarkdownIt from 'markdown-it'

  const plugin: (md: MarkdownIt, ...params: unknown[]) => void
  export default plugin
}

declare module 'markdown-it-task-lists' {
  import type MarkdownIt from 'markdown-it'

  const plugin: (md: MarkdownIt, ...params: unknown[]) => void
  export default plugin
}
