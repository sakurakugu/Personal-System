import type { Component } from 'vue'

export type ToolbarAction =
  | 'heading'
  | 'underline'
  | 'subscript'
  | 'superscript'
  | 'strong'
  | 'emphasis'
  | 'strikethrough'
  | 'highlight'
  | 'link'
  | 'inlineCode'
  | 'blockquote'
  | 'bulletList'
  | 'orderedList'
  | 'taskList'
  | 'codeBlock'
  | 'table'
  | 'hr'
  | 'footnote'
  | 'abbr'
  | 'emojiShortcode'
  | 'image'
  | 'imageLink'
  | 'imageCropUpload'
  | 'mermaid'
  | 'math'
  | 'customMarkdown'
  | 'undo'
  | 'redo'
  | 'aiTools'
  | 'format'
  | 'scrollSync'
  | 'previewToggle'
  | 'previewLayoutToggle'
  | 'previewLayoutSplit'
  | 'previewLayoutFull'
  | 'previewTypeToggle'
  | 'previewTypePreview'
  | 'previewTypeHtml'
  | 'previewTypeMindmap'
  | 'outlineToggle'
  | 'pageFullscreen'
  | 'fullscreen'
  | 'sourceMode'

export type ToolbarItemType = 'button' | 'dropdown' | 'separator' | 'spacer'

export interface ToolbarDropdownOption {
  label: string
  title: string
  action: ToolbarAction
  payload?: string | number
  kind?: 'option'
}

export interface ToolbarDropdownDivider {
  label: string
  kind: 'divider'
}

export type ToolbarDropdownEntry = ToolbarDropdownOption | ToolbarDropdownDivider

export interface ToolbarItem {
  type?: ToolbarItemType
  label: string
  title: string
  dynamicTitle?: () => string
  action?: ToolbarAction
  payload?: string | number
  icon?: Component
  dynamicIcon?: () => Component
  dropdown?: ToolbarDropdownEntry[]
  hidden?: () => boolean
  active?: () => boolean
  disabled?: () => boolean
}

export interface ToolbarOverflowMenuOption {
  kind: 'option'
  key: string
  label: string
  title: string
  action: ToolbarAction
  payload?: string | number
  icon?: Component
  disabled?: () => boolean
  children?: ToolbarOverflowSubmenuEntry[]
}

export interface ToolbarOverflowMenuDivider {
  kind: 'divider'
  key: string
  label: string
}

export type ToolbarOverflowMenuEntry = ToolbarOverflowMenuOption | ToolbarOverflowMenuDivider
export type ToolbarOverflowSubmenuEntry = ToolbarDropdownEntry & { key: string }
