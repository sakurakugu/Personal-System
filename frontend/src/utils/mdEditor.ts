import { config as configureMdEditor } from 'md-editor-v3'
import { applyAuthorizedMarkdownImageRenderer } from './articleMedia'

let 已初始化编辑器配置 = false

export function setupMdEditorConfig() {
  if (已初始化编辑器配置) {
    return
  }

  configureMdEditor({
    markdownItConfig(md) {
      applyAuthorizedMarkdownImageRenderer(md)
    },
  })
  已初始化编辑器配置 = true
}
