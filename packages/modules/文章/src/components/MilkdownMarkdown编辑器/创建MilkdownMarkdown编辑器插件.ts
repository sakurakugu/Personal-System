import {
  commandsCtx,
  parserCtx,
} from '@milkdown/core'
import type { MilkdownPlugin } from '@milkdown/ctx'
import { clipboard } from '@milkdown/plugin-clipboard'
import { cursor } from '@milkdown/plugin-cursor'
import { history } from '@milkdown/plugin-history'
import { indent } from '@milkdown/plugin-indent'
import { listener } from '@milkdown/plugin-listener'
import { trailing } from '@milkdown/plugin-trailing'
import {
  commands as commonmarkCommands,
  keymap as commonmarkKeymap,
  plugins as commonmarkPlugins,
  schema as commonmarkSchema,
  createCodeBlockInputRule,
  emphasisStarInputRule,
  emphasisUnderscoreInputRule,
  inlineCodeInputRule,
  linkSchema,
  listItemSchema,
  strongInputRule,
  toggleStrongCommand,
  wrapInBlockquoteInputRule,
  wrapInBulletListInputRule,
  wrapInHeadingInputRule,
  wrapInOrderedListInputRule,
} from '@milkdown/preset-commonmark'
import { gfm } from '@milkdown/preset-gfm'
import { InputRule } from '@milkdown/prose/inputrules'
import { Plugin } from '@milkdown/prose/state'
import type { EditorView } from '@milkdown/prose/view'
import { $inputRule, $prose } from '@milkdown/utils'
import { buildExtendedMarkdownDecorations } from './MilkdownMarkdown扩展装饰'
import { imageGridMarkdownPlugins } from './MilkdownMarkdown图片网格'
import { createCodeBlockInfoEditPlugin } from './MilkdownMarkdown代码块信息编辑'
import { highlightMarkdownPlugins } from './MilkdownMarkdown标记语法'
import { createMarkdownKeyboardPlugin } from './MilkdownMarkdown快捷键'
import { createReverseInlineMarkdownInputPlugin } from './反向行内Markdown输入'

interface 创建MilkdownMarkdown编辑器插件选项 {
  更新光标状态: () => void
}

type Milkdown插件项 = MilkdownPlugin | MilkdownPlugin[]

export function 创建MilkdownMarkdown编辑器插件(
  options: 创建MilkdownMarkdown编辑器插件选项,
): Milkdown插件项[] {
  return [
    ...创建Commonmark编辑器插件(),
    gfm,
    ...highlightMarkdownPlugins,
    ...imageGridMarkdownPlugins,
    创建Markdown链接输入规则(),
    $prose(() => createReverseInlineMarkdownInputPlugin()),
    创建任务列表复选框点击插件(),
    创建扩展Markdown预览装饰插件(),
    创建代码块信息编辑插件(),
    创建编辑器状态插件(options.更新光标状态),
    history,
    listener,
    clipboard,
    cursor,
    indent,
    trailing,
  ]
}

function 创建Commonmark编辑器插件(): Milkdown插件项[] {
  return [
    commonmarkSchema,
    [
      wrapInBlockquoteInputRule,
      wrapInBulletListInputRule,
      wrapInOrderedListInputRule,
      createCodeBlockInputRule,
      wrapInHeadingInputRule,
    ],
    [
      emphasisStarInputRule,
      emphasisUnderscoreInputRule,
      inlineCodeInputRule,
      strongInputRule,
    ],
    commonmarkCommands,
    $prose((ctx) => createMarkdownKeyboardPlugin(
      ctx.get(parserCtx),
      listItemSchema.type(ctx),
      {
        toggleStrong: () => ctx.get(commandsCtx).call(toggleStrongCommand.key),
      },
    )),
    commonmarkKeymap,
    commonmarkPlugins,
  ].flat()
}

function 创建Markdown链接输入规则(): MilkdownPlugin {
  return $inputRule((ctx) => new InputRule(
    /\[([^\]\n]+)]\((https?:\/\/[^\s)]+)\)$/,
    (state, match, start, end) => {
      const linkText = match[1]
      const href = match[2]
      if (!linkText || !href) {
        return null
      }

      const linkMark = linkSchema.type(ctx).create({ href, title: null })
      const tr = state.tr.insertText(linkText, start, end)
      tr.addMark(start, start + linkText.length, linkMark)
      tr.removeStoredMark(linkSchema.type(ctx))
      return tr
    },
  ))
}

function 创建任务列表复选框点击插件(): MilkdownPlugin {
  return $prose(() => new Plugin({
    props: {
      handleClickOn(view, _pos, node, nodePos, event) {
        if (node.type.name !== 'list_item' || node.attrs.checked == null) {
          return false
        }

        if (!isTaskListCheckboxClick(view, nodePos, event)) {
          return false
        }

        const checked = node.attrs.checked !== true
        view.dispatch(view.state.tr.setNodeMarkup(nodePos, undefined, {
          ...node.attrs,
          checked,
        }))
        return true
      },
    },
  }))
}

function 创建扩展Markdown预览装饰插件(): MilkdownPlugin {
  return $prose(() => new Plugin({
    props: {
      decorations(state) {
        return buildExtendedMarkdownDecorations(state.doc)
      },
    },
  }))
}

function 创建代码块信息编辑插件(): MilkdownPlugin {
  return $prose(() => createCodeBlockInfoEditPlugin())
}

function 创建编辑器状态插件(更新光标状态: () => void): MilkdownPlugin {
  return $prose(() => new Plugin({
    view() {
      return {
        update() {
          更新光标状态()
        },
      }
    },
  }))
}

function isTaskListCheckboxClick(view: EditorView, nodePos: number, event: MouseEvent): boolean {
  const nodeDom = view.nodeDOM(nodePos)
  if (!(nodeDom instanceof HTMLElement)) {
    return false
  }

  const rect = nodeDom.getBoundingClientRect()
  const style = window.getComputedStyle(nodeDom)
  const beforeStyle = window.getComputedStyle(nodeDom, '::before')
  const fontSize = Number.parseFloat(style.fontSize) || 16
  const lineHeight = Number.parseFloat(style.lineHeight) || fontSize * 1.5
  const beforeWidth = Number.parseFloat(beforeStyle.width)
  const beforeHeight = Number.parseFloat(beforeStyle.height)
  const beforeMarginTop = Number.parseFloat(beforeStyle.marginTop) || 0

  if (beforeStyle.content !== 'none' && Number.isFinite(beforeWidth) && beforeWidth > 0) {
    const hitPadding = Math.max(4, fontSize * 0.2)
    const checkboxLeft = rect.left - hitPadding
    const checkboxRight = rect.left + beforeWidth + hitPadding
    const checkboxTop = rect.top + beforeMarginTop - hitPadding
    const checkboxBottom = rect.top + beforeMarginTop + (Number.isFinite(beforeHeight) && beforeHeight > 0
      ? beforeHeight
      : fontSize) + hitPadding

    return (
      event.clientX >= checkboxLeft
      && event.clientX <= checkboxRight
      && event.clientY >= checkboxTop
      && event.clientY <= checkboxBottom
    )
  }

  const checkboxLeft = rect.left - fontSize * 1.55
  const checkboxRight = rect.left - fontSize * 0.15
  const checkboxTop = rect.top
  const checkboxBottom = rect.top + Math.max(lineHeight, fontSize * 1.35)

  return (
    event.clientX >= checkboxLeft
    && event.clientX <= checkboxRight
    && event.clientY >= checkboxTop
    && event.clientY <= checkboxBottom
  )
}
