import { config as configureMdEditor } from 'md-editor-v3'
import { applyAuthorizedMarkdownImageRenderer, getStoredAccessToken } from './articleMedia'

let 已初始化编辑器配置 = false

export function setupMdEditorConfig() {
  if (已初始化编辑器配置) {
    return
  }

  configureMdEditor({
    markdownItConfig(md) {
      applyAuthorizedMarkdownImageRenderer(md, () => getStoredAccessToken())
    },
  })
  已初始化编辑器配置 = true
}
