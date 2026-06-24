import { commandsCtx } from '@milkdown/core'
import {
  createCodeBlockCommand,
  insertHrCommand,
  toggleEmphasisCommand,
  toggleInlineCodeCommand,
  toggleLinkCommand,
  toggleStrongCommand,
  wrapInBlockquoteCommand,
  wrapInBulletListCommand,
  wrapInHeadingCommand,
  wrapInOrderedListCommand,
} from '@milkdown/preset-commonmark'
import { insertTableCommand, toggleStrikethroughCommand } from '@milkdown/preset-gfm'
import type { Editor } from '@milkdown/core'
import type { Ref } from 'vue'
import type { ToolbarAction } from '../MilkdownMarkdown工具栏/MilkdownMarkdown工具栏类型'
import {
  buildCustomMarkdownSnippet,
  normalizeCustomMarkdownSnippet,
} from './Markdown自定义语法片段'
import {
  buildTableMarkdown,
  buildToolbarMarkdownSnippet,
  normalizeHeadingLevel,
  normalizeTableSizePayload,
  shouldInsertMarkdownSnippet,
} from './MilkdownMarkdown工具栏动作辅助'

export type MilkdownMarkdown预览类型 = 'preview' | 'html' | 'mindmap'
export type MilkdownMarkdown预览布局模式 = 'split' | 'full'
export type MilkdownMarkdown自定义语法弹窗类型 = 'github-alert-syntax' | 'code-syntax'

export interface 使用MilkdownMarkdown工具栏动作选项 {
  editor: Ref<Editor | null>
  isSourceMode: Ref<boolean>
  lastMarkdown: Ref<string>
  getMarkdown: () => string
  insertMarkdown: (markdown: string) => void
  undoEdit: () => boolean
  redoEdit: () => boolean
  toggleHighlight: () => void
  toggleSourceStrong: () => void
  toggleSourceMode: () => void
  focus: () => void
  openImagePicker: () => void
  insertImageLink: () => void
  openCropImagePicker: () => void
  formatContent: () => void | Promise<unknown> | undefined
  openAiTools: () => void
  getPreviewLayoutMode: () => MilkdownMarkdown预览布局模式
  getPreviewType: () => MilkdownMarkdown预览类型
  getScrollSync: () => boolean
  getPreviewEnabled: () => boolean
  getOutlineVisible: () => boolean
  emitModelValue: (value: string) => void
  emitScrollSync: (value: boolean) => void
  emitPreviewEnabled: (value: boolean) => void
  emitPreviewLayoutMode: (value: MilkdownMarkdown预览布局模式) => void
  emitPreviewType: (value: MilkdownMarkdown预览类型) => void
  emitOutlineVisible: (value: boolean) => void
  togglePageFullscreen: () => void
  toggleScreenFullscreen: () => Promise<void>
  openGithubCardDialog: () => void
  openCustomMarkdownSyntaxDialog: (type: MilkdownMarkdown自定义语法弹窗类型) => void
}

export function 使用MilkdownMarkdown工具栏动作({
  editor,
  isSourceMode,
  lastMarkdown,
  getMarkdown,
  insertMarkdown,
  undoEdit,
  redoEdit,
  toggleHighlight,
  toggleSourceStrong,
  toggleSourceMode,
  focus,
  openImagePicker,
  insertImageLink,
  openCropImagePicker,
  formatContent,
  openAiTools,
  getPreviewLayoutMode,
  getPreviewType,
  getScrollSync,
  getPreviewEnabled,
  getOutlineVisible,
  emitModelValue,
  emitScrollSync,
  emitPreviewEnabled,
  emitPreviewLayoutMode,
  emitPreviewType,
  emitOutlineVisible,
  togglePageFullscreen,
  toggleScreenFullscreen,
  openGithubCardDialog,
  openCustomMarkdownSyntaxDialog,
}: 使用MilkdownMarkdown工具栏动作选项) {
  function runToolbarAction(action: ToolbarAction, payload?: string | number) {
    if (action === 'image') {
      openImagePicker()
      return
    }

    if (action === 'imageLink') {
      insertImageLink()
      return
    }

    if (action === 'imageCropUpload') {
      openCropImagePicker()
      return
    }

    if (action === 'sourceMode') {
      toggleSourceMode()
      return
    }

    if (action === 'undo') {
      undoEdit()
      focus()
      return
    }

    if (action === 'redo') {
      redoEdit()
      focus()
      return
    }

    if (action === 'format') {
      void formatContent()
      return
    }

    if (action === 'aiTools') {
      openAiTools()
      return
    }

    if (action === 'scrollSync') {
      if (getPreviewLayoutMode() !== 'split' || getPreviewType() === 'mindmap') {
        return
      }
      emitScrollSync(!getScrollSync())
      return
    }

    if (action === 'previewToggle') {
      emitPreviewEnabled(!getPreviewEnabled())
      return
    }

    if (action === 'previewLayoutToggle') {
      emitPreviewLayoutMode(getPreviewLayoutMode() === 'split' ? 'full' : 'split')
      return
    }

    if (action === 'previewLayoutSplit') {
      emitPreviewLayoutMode('split')
      return
    }

    if (action === 'previewLayoutFull') {
      emitPreviewLayoutMode('full')
      return
    }

    if (action === 'previewTypeToggle') {
      if (getPreviewType() === 'preview') {
        emitPreviewType('html')
        return
      }
      if (getPreviewType() === 'html') {
        emitPreviewType('mindmap')
        return
      }
      emitPreviewType('preview')
      return
    }

    if (action === 'previewTypePreview') {
      emitPreviewType('preview')
      return
    }

    if (action === 'previewTypeHtml') {
      emitPreviewType('html')
      return
    }

    if (action === 'previewTypeMindmap') {
      emitPreviewType('mindmap')
      return
    }

    if (action === 'outlineToggle') {
      emitOutlineVisible(!getOutlineVisible())
      return
    }

    if (action === 'pageFullscreen') {
      togglePageFullscreen()
      return
    }

    if (action === 'fullscreen') {
      void toggleScreenFullscreen()
      return
    }

    if (action === 'customMarkdown') {
      const handled = runCustomMarkdownAction(payload)
      if (handled) {
        focus()
      }
      return
    }

    if (action === 'highlight' && !isSourceMode.value) {
      toggleHighlight()
      focus()
      return
    }

    if (shouldInsertMarkdownSnippet(action)) {
      insertMarkdown(buildToolbarMarkdownSnippet(action, payload))
      focus()
      return
    }

    if (isSourceMode.value) {
      runSourceModeAction(action, payload)
      return
    }

    const currentEditor = editor.value
    if (!currentEditor) {
      return
    }

    const commandResult = currentEditor.action((ctx) => {
      const commands = ctx.get(commandsCtx)
      switch (action) {
        case 'heading':
          return commands.call(wrapInHeadingCommand.key, normalizeHeadingLevel(payload))
        case 'strong':
          return commands.call(toggleStrongCommand.key)
        case 'emphasis':
          return commands.call(toggleEmphasisCommand.key)
        case 'strikethrough':
          return commands.call(toggleStrikethroughCommand.key)
        case 'inlineCode':
          return commands.call(toggleInlineCodeCommand.key)
        case 'link':
          return commands.call(toggleLinkCommand.key, { href: 'https://example.com' })
        case 'blockquote':
          return commands.call(wrapInBlockquoteCommand.key)
        case 'bulletList':
          return commands.call(wrapInBulletListCommand.key)
        case 'orderedList':
          return commands.call(wrapInOrderedListCommand.key)
        case 'taskList':
          return false
        case 'codeBlock':
          return commands.call(createCodeBlockCommand.key)
        case 'table':
          return commands.call(insertTableCommand.key, normalizeTableSizePayload(payload))
        case 'hr':
          return commands.call(insertHrCommand.key)
      }
    })

    if (!commandResult) {
      runSourceModeAction(action, payload)
    }

    lastMarkdown.value = getMarkdown()
    emitModelValue(lastMarkdown.value)
    focus()
  }

  function runSourceModeAction(action: ToolbarAction, payload?: string | number) {
    switch (action) {
      case 'heading':
        insertMarkdown(`${'\n'}${'#'.repeat(normalizeHeadingLevel(payload))} 标题\n`)
        return
      case 'underline':
      case 'subscript':
      case 'superscript':
      case 'emphasis':
      case 'strikethrough':
      case 'highlight':
      case 'inlineCode':
      case 'link':
      case 'footnote':
      case 'abbr':
      case 'emojiShortcode':
      case 'mermaid':
      case 'math':
        insertMarkdown(buildToolbarMarkdownSnippet(action, payload))
        return
      case 'strong':
        toggleSourceStrong()
        return
      case 'customMarkdown':
        runCustomMarkdownAction(payload)
        return
      case 'blockquote':
        insertMarkdown('\n> 引用内容\n')
        return
      case 'bulletList':
        insertMarkdown('\n- 列表项\n')
        return
      case 'orderedList':
        insertMarkdown('\n1. 列表项\n')
        return
      case 'taskList':
        insertMarkdown('\n- [ ] 待办项\n')
        return
      case 'codeBlock':
        insertMarkdown('\n```ts\n\n```\n')
        return
      case 'table':
        insertMarkdown(buildTableMarkdown(normalizeTableSizePayload(payload)))
        return
      case 'hr':
        insertMarkdown('\n---\n')
        return
      case 'undo':
      case 'redo':
      case 'image':
      case 'imageLink':
      case 'imageCropUpload':
      case 'format':
      case 'aiTools':
      case 'scrollSync':
      case 'previewToggle':
      case 'previewLayoutToggle':
      case 'previewLayoutSplit':
      case 'previewLayoutFull':
      case 'previewTypeToggle':
      case 'previewTypePreview':
      case 'previewTypeHtml':
      case 'previewTypeMindmap':
      case 'outlineToggle':
      case 'pageFullscreen':
      case 'fullscreen':
      case 'sourceMode':
        return
    }
  }

  function runCustomMarkdownAction(payload?: string | number): boolean {
    const snippetType = normalizeCustomMarkdownSnippet(payload)
    if (!snippetType) {
      return false
    }

    if (snippetType === 'github-card') {
      openGithubCardDialog()
      return true
    }

    if (snippetType === 'github-alert-syntax' || snippetType === 'code-syntax') {
      openCustomMarkdownSyntaxDialog(snippetType)
      return true
    }

    insertMarkdown(buildCustomMarkdownSnippet(snippetType))
    return true
  }

  return {
    runToolbarAction,
  }
}
