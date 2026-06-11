import { TextSelection } from '@milkdown/prose/state'
import type { EditorView } from '@milkdown/prose/view'
import type { Ref } from 'vue'

export interface 使用MilkdownMarkdown滚动定位选项 {
  contentRef: Ref<HTMLDivElement | null>
  isSourceMode: Ref<boolean>
  sourceTextareaRef: Ref<HTMLTextAreaElement | null>
  sourceContent: Ref<string>
  getEditorView: () => EditorView | null
  updateCursorStatus: () => void
}

export function 使用MilkdownMarkdown滚动定位({
  contentRef,
  isSourceMode,
  sourceTextareaRef,
  sourceContent,
  getEditorView,
  updateCursorStatus,
}: 使用MilkdownMarkdown滚动定位选项) {
  let pendingScrollRatioAfterModeSwitch: number | null = null

  function getScrollElement(): HTMLElement | null {
    return contentRef.value
  }

  function getScrollRatio(): number {
    const scrollElement = getScrollElement()
    if (!scrollElement) {
      return 0
    }

    const maxScrollTop = scrollElement.scrollHeight - scrollElement.clientHeight
    if (maxScrollTop <= 0) {
      return 0
    }

    return scrollElement.scrollTop / maxScrollTop
  }

  function setScrollRatio(ratio: number) {
    const scrollElement = getScrollElement()
    if (!scrollElement) {
      return
    }

    const normalizedRatio = Math.min(1, Math.max(0, ratio))
    const maxScrollTop = scrollElement.scrollHeight - scrollElement.clientHeight
    scrollElement.scrollTop = maxScrollTop <= 0 ? 0 : maxScrollTop * normalizedRatio
  }

  function scrollToHeading(headingIndex: number, sourceLine: number): boolean {
    if (headingIndex < 0) {
      return false
    }

    if (isSourceMode.value) {
      return scrollSourceToLine(sourceLine)
    }

    const view = getEditorView()
    if (!view) {
      return false
    }

    let currentHeadingIndex = -1
    let targetPosition: number | null = null
    view.state.doc.descendants((node, pos) => {
      if (node.type.name !== 'heading') {
        return true
      }

      currentHeadingIndex += 1
      if (currentHeadingIndex === headingIndex) {
        targetPosition = pos
        return false
      }

      return true
    })

    if (targetPosition === null) {
      return false
    }

    const selectionPosition = Math.min(targetPosition + 1, view.state.doc.content.size)
    const tr = view.state.tr.setSelection(
      TextSelection.near(view.state.doc.resolve(selectionPosition), 1),
    ).scrollIntoView()
    view.dispatch(tr)
    requestAnimationFrame(() => {
      const scrollElement = getScrollElement()
      if (!scrollElement) {
        return
      }

      const headingElement = view.dom.querySelectorAll('h1, h2, h3, h4, h5, h6').item(headingIndex)
      if (!(headingElement instanceof HTMLElement)) {
        return
      }

      const scrollRect = scrollElement.getBoundingClientRect()
      const headingRect = headingElement.getBoundingClientRect()
      const targetTop = scrollElement.scrollTop + headingRect.top - scrollRect.top - scrollElement.clientHeight * 0.12
      scrollElement.scrollTo({ top: Math.max(0, targetTop), behavior: 'smooth' })
    })
    view.focus()
    return true
  }

  function scrollSourceToLine(sourceLine: number): boolean {
    const textarea = sourceTextareaRef.value
    if (!textarea || sourceLine <= 0) {
      return false
    }

    const lineStartOffset = getSourceLineStartOffset(sourceContent.value, sourceLine)
    textarea.focus()
    textarea.setSelectionRange(lineStartOffset, lineStartOffset)
    updateCursorStatus()

    const computedStyle = window.getComputedStyle(textarea)
    const parsedLineHeight = Number.parseFloat(computedStyle.lineHeight)
    const parsedFontSize = Number.parseFloat(computedStyle.fontSize)
    const lineHeight = Number.isFinite(parsedLineHeight)
      ? parsedLineHeight
      : (Number.isFinite(parsedFontSize) ? parsedFontSize * 1.75 : 24)
    const targetTop = Math.max(0, (sourceLine - 1) * lineHeight - textarea.clientHeight * 0.22)
    const scrollElement = getScrollElement()
    if (!scrollElement) {
      return false
    }

    const headerHeight = Math.max(0, textarea.offsetTop - scrollElement.offsetTop)
    scrollElement.scrollTo({ top: headerHeight + targetTop, behavior: 'smooth' })
    return true
  }

  function 记录模式切换前滚动位置() {
    pendingScrollRatioAfterModeSwitch = getScrollRatio()
  }

  function restoreScrollAfterModeSwitch() {
    if (pendingScrollRatioAfterModeSwitch === null) {
      return
    }

    const scrollRatio = pendingScrollRatioAfterModeSwitch
    pendingScrollRatioAfterModeSwitch = null
    window.requestAnimationFrame(() => {
      setScrollRatio(scrollRatio)
    })
  }

  return {
    getScrollElement,
    getScrollRatio,
    setScrollRatio,
    scrollToHeading,
    记录模式切换前滚动位置,
    restoreScrollAfterModeSwitch,
  }
}

export function getSourceLineStartOffset(source: string, sourceLine: number): number {
  if (sourceLine <= 1) {
    return 0
  }

  let currentLine = 1
  for (let index = 0; index < source.length; index += 1) {
    if (source[index] !== '\n') {
      continue
    }

    currentLine += 1
    if (currentLine === sourceLine) {
      return index + 1
    }
  }

  return source.length
}
