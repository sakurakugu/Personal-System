import { applyAuthorizedMarkdownImageRenderer } from './articleMedia'

let 已初始化编辑器配置 = false
let 编辑器配置任务: Promise<void> | null = null

export function ensureMdEditorConfig(): Promise<void> {
  if (已初始化编辑器配置) {
    return Promise.resolve()
  }

  if (编辑器配置任务) {
    return 编辑器配置任务
  }

  编辑器配置任务 = (async () => {
    const { config: configureMdEditor } = await import('md-editor-v3')

    configureMdEditor({
      markdownItConfig(md) {
        applyAuthorizedMarkdownImageRenderer(md)
      },
    })
    已初始化编辑器配置 = true
  })()

  return 编辑器配置任务
}
