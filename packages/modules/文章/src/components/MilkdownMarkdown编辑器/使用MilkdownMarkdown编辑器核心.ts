import {
  defaultValueCtx,
  Editor,
  editorViewCtx,
  rootCtx,
  serializerCtx,
} from '@milkdown/core'
import { listenerCtx } from '@milkdown/plugin-listener'
import { redo, undo } from '@milkdown/prose/history'
import type { EditorView } from '@milkdown/prose/view'
import { insert, replaceAll } from '@milkdown/utils'
import { ref, shallowRef, type Ref } from 'vue'
import { buildToolbarMarkdownSnippet } from './MilkdownMarkdown工具栏动作辅助'
import { configureMarkdownSerializer } from './MilkdownMarkdown标记语法'
import { normalizeSerializedMarkdown } from './MilkdownMarkdown序列化'
import { 创建MilkdownMarkdown编辑器插件 } from './创建MilkdownMarkdown编辑器插件'

export interface 使用MilkdownMarkdown编辑器核心选项 {
  rootRef: Ref<HTMLDivElement | null>
  sourceTextareaRef: Ref<HTMLTextAreaElement | null>
  isSourceMode: Ref<boolean>
  sourceContent: Ref<string>
  lastMarkdown: Ref<string>
  getModelValue: () => string
  updateCursorStatus: () => void
  emitModelValue: (value: string) => void
  emitReady: () => void
  emitLoadingChange: (value: boolean) => void
}

export function 使用MilkdownMarkdown编辑器核心({
  rootRef,
  sourceTextareaRef,
  isSourceMode,
  sourceContent,
  lastMarkdown,
  getModelValue,
  updateCursorStatus,
  emitModelValue,
  emitReady,
  emitLoadingChange,
}: 使用MilkdownMarkdown编辑器核心选项) {
  const editor = shallowRef<Editor | null>(null)
  const loading = ref(true)
  const isApplyingExternalMarkdown = ref(false)
  const isEditorReadyForLocalUpdates = ref(false)

  async function createEditor() {
    const root = rootRef.value
    if (!root) {
      return
    }

    loading.value = true
    emitLoadingChange(true)

    const milkdownEditor = Editor.make()
      .config((ctx) => {
        ctx.set(rootCtx, root)
        ctx.set(defaultValueCtx, getModelValue())
        configureMarkdownSerializer(ctx)
        ctx.get(listenerCtx).markdownUpdated((_ctx, markdown) => {
          if (isApplyingExternalMarkdown.value || !isEditorReadyForLocalUpdates.value) {
            return
          }

          const normalizedMarkdown = normalizeSerializedMarkdown(markdown)
          lastMarkdown.value = normalizedMarkdown
          emitModelValue(normalizedMarkdown)
        })
      })

    for (const plugin of 创建MilkdownMarkdown编辑器插件({ 更新光标状态: updateCursorStatus })) {
      milkdownEditor.use(plugin)
    }

    try {
      editor.value = await milkdownEditor.create()
      lastMarkdown.value = getModelValue()
      isEditorReadyForLocalUpdates.value = true
      updateCursorStatus()
      emitReady()
    } finally {
      loading.value = false
      emitLoadingChange(false)
    }
  }

  function destroyEditor() {
    void editor.value?.destroy()
    editor.value = null
  }

  function getMarkdown(): string {
    const currentEditor = editor.value
    if (!currentEditor) {
      return isSourceMode.value ? sourceContent.value : lastMarkdown.value
    }

    return currentEditor.action((ctx) => {
      const view = ctx.get(editorViewCtx)
      const serializer = ctx.get(serializerCtx)
      return normalizeSerializedMarkdown(serializer(view.state.doc))
    })
  }

  function setMarkdown(markdown: string) {
    lastMarkdown.value = markdown

    if (isSourceMode.value) {
      sourceContent.value = markdown
      return
    }

    replaceEditorMarkdown(markdown)
  }

  function replaceEditorMarkdown(markdown: string): boolean {
    const currentEditor = editor.value
    if (!currentEditor) {
      return false
    }

    isApplyingExternalMarkdown.value = true
    try {
      currentEditor.action(replaceAll(markdown, true))
      return true
    } finally {
      isApplyingExternalMarkdown.value = false
    }
  }

  function formatMarkdown(): string | null {
    const sourceMarkdown = isSourceMode.value ? sourceContent.value : getMarkdown()
    if (!replaceEditorMarkdown(sourceMarkdown)) {
      return null
    }

    const formattedMarkdown = getMarkdown()
    lastMarkdown.value = formattedMarkdown
    if (isSourceMode.value) {
      sourceContent.value = formattedMarkdown
    }
    emitModelValue(formattedMarkdown)
    return formattedMarkdown
  }

  function insertMarkdown(markdown: string) {
    if (!markdown) {
      return
    }

    if (isSourceMode.value) {
      const textarea = sourceTextareaRef.value
      const selectionStart = textarea?.selectionStart ?? sourceContent.value.length
      const selectionEnd = textarea?.selectionEnd ?? selectionStart
      sourceContent.value = `${sourceContent.value.slice(0, selectionStart)}${markdown}${sourceContent.value.slice(selectionEnd)}`
      lastMarkdown.value = sourceContent.value
      updateCursorStatus()
      emitModelValue(sourceContent.value)
      return
    }

    const currentEditor = editor.value
    if (!currentEditor) {
      return
    }

    currentEditor.action(insert(markdown))
    lastMarkdown.value = getMarkdown()
    emitModelValue(lastMarkdown.value)
  }

  function getEditorView(): EditorView | null {
    return editor.value?.action((ctx) => ctx.get(editorViewCtx)) ?? null
  }

  function redoEdit(): boolean {
    const view = getEditorView()
    if (!view) {
      return false
    }

    return redo(view.state, view.dispatch)
  }

  function undoEdit(): boolean {
    const view = getEditorView()
    if (!view) {
      return false
    }

    return undo(view.state, view.dispatch)
  }

  function toggleHighlight() {
    const view = getEditorView()
    if (!view) {
      insertMarkdown(buildToolbarMarkdownSnippet('highlight'))
      return
    }

    const markType = view.state.schema.marks.highlight
    if (!markType) {
      insertMarkdown(buildToolbarMarkdownSnippet('highlight'))
      return
    }

    const { from, to, empty } = view.state.selection
    if (empty) {
      insertMarkdown(buildToolbarMarkdownSnippet('highlight'))
      return
    }

    const hasHighlight = view.state.doc.rangeHasMark(from, to, markType)
    const tr = hasHighlight
      ? view.state.tr.removeMark(from, to, markType)
      : view.state.tr.addMark(from, to, markType.create())
    view.dispatch(tr.scrollIntoView())
    lastMarkdown.value = getMarkdown()
    emitModelValue(lastMarkdown.value)
  }

  return {
    editor,
    loading,
    createEditor,
    destroyEditor,
    getMarkdown,
    setMarkdown,
    formatMarkdown,
    insertMarkdown,
    getEditorView,
    redoEdit,
    undoEdit,
    toggleHighlight,
  }
}
