import type { Node as ProseNode } from '@milkdown/prose/model'
import { Plugin } from '@milkdown/prose/state'
import { Decoration, DecorationSet, type EditorView } from '@milkdown/prose/view'
import { 清理代码块信息文本 } from './MilkdownMarkdown语法常量'

export function createCodeBlockInfoEditPlugin(): Plugin {
  return new Plugin({
    props: {
      decorations(state) {
        const decorations: Decoration[] = []

        state.doc.descendants((node, pos) => {
          if (node.type.name !== 'code_block') {
            return true
          }

          decorations.push(Decoration.widget(pos, (view) => 创建代码块信息区域(view, pos, node), {
            key: `milkdown-code-info-${pos}-${node.attrs.language ?? ''}`,
            side: -1,
            stopEvent: (event) => event.target instanceof HTMLInputElement,
          }))
          return false
        })

        return DecorationSet.create(state.doc, decorations)
      },
    },
  })
}

function 创建代码块信息区域(view: EditorView, pos: number, node: ProseNode): HTMLElement {
  const info = String(node.attrs.language ?? '')
  const container = document.createElement('div')
  container.className = 'milkdown-code-info-editor'
  container.contentEditable = 'false'

  const input = document.createElement('input')
  input.className = 'milkdown-code-info-editor__input'
  input.type = 'text'
  input.value = info
  input.placeholder = '语言和元数据，例如 ts title="入口" ln 等'
  input.ariaLabel = '代码块信息'
  input.autocomplete = 'off'
  input.spellcheck = false

  input.addEventListener('mousedown', (event) => event.stopPropagation())
  input.addEventListener('keydown', (event) => {
    event.stopPropagation()
    if (event.key === 'Enter') {
      event.preventDefault()
      input.blur()
    }
    if (event.key === 'Escape') {
      input.value = String(node.attrs.language ?? '')
      input.blur()
    }
  })
  input.addEventListener('blur', () => {
    更新代码块信息(view, pos, input.value)
  })

  container.append(input)
  return container
}

function 更新代码块信息(view: EditorView, pos: number, rawInfo: string) {
  const node = view.state.doc.nodeAt(pos)
  if (!node || node.type.name !== 'code_block') {
    return
  }

  const currentInfo = String(node.attrs.language ?? '')
  const nextInfo = 清理代码块信息文本(rawInfo)
  if (nextInfo === currentInfo) {
    return
  }

  view.dispatch(view.state.tr.setNodeMarkup(pos, undefined, {
    ...node.attrs,
    language: nextInfo,
  }))
}
