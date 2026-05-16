import { redo } from '@codemirror/commands'
import type { EditorView } from '@codemirror/view'
import { onBeforeUnmount, onMounted, toValue, watch } from 'vue'
import type { MaybeRefOrGetter } from 'vue'
import type { ExposeParam } from 'md-editor-v3'

interface EditorShortcutOptions {
  editorRef: MaybeRefOrGetter<ExposeParam | undefined>
  editorId: MaybeRefOrGetter<string>
  enabled?: MaybeRefOrGetter<boolean>
  onFormatAndSave?: () => void | Promise<unknown>
  onRedo?: (view: EditorView) => boolean | void | Promise<boolean | void>
}

function 是否是格式化并保存快捷键(event: globalThis.KeyboardEvent): boolean {
  return (event.ctrlKey || event.metaKey)
    && !event.altKey
    && event.shiftKey
    && event.key.toLowerCase() === 's'
}

function 是否是重做快捷键(event: globalThis.KeyboardEvent): boolean {
  return (event.ctrlKey || event.metaKey)
    && !event.altKey
    && event.shiftKey
    && event.key.toLowerCase() === 'z'
}

function 快捷键是否启用(enabled?: MaybeRefOrGetter<boolean>): boolean {
  return enabled === undefined || Boolean(toValue(enabled))
}

function 阻止快捷键事件(event: globalThis.KeyboardEvent) {
  event.preventDefault()
  event.stopPropagation()
  event.stopImmediatePropagation()
}

export function 使用编辑器快捷键(options: EditorShortcutOptions) {
  watch(() => toValue(options.editorRef), async (editor, _, onCleanup) => {
    if (!editor) {
      return
    }

    const editorView = editor.getEditorView()
    if (!editorView) {
      return
    }

    // 捕获阶段先拦截，避免编辑器自己的快捷键继续落下去。
    const handleEditorKeydown = (event: globalThis.KeyboardEvent) => {
      if (是否是格式化并保存快捷键(event)) {
        阻止快捷键事件(event)

        if (event.repeat || event.isComposing || !快捷键是否启用(options.enabled)) {
          return
        }

        void options.onFormatAndSave?.()
        return
      }

      if (!是否是重做快捷键(event)) {
        return
      }

      阻止快捷键事件(event)

      if (event.repeat || event.isComposing || !快捷键是否启用(options.enabled)) {
        return
      }

      if (options.onRedo) {
        void options.onRedo(editorView)
        return
      }

      redo(editorView)
    }

    editorView.dom.addEventListener('keydown', handleEditorKeydown, true)
    onCleanup(() => {
      editorView.dom.removeEventListener('keydown', handleEditorKeydown, true)
    })
  }, { flush: 'post' })

  function handleWindowKeydown(event: globalThis.KeyboardEvent) {
    if (!options.onFormatAndSave || !是否是格式化并保存快捷键(event)) {
      return
    }

    const eventTarget = event.target
    const editorId = toValue(options.editorId)
    if (eventTarget instanceof globalThis.Element && eventTarget.closest(`#${editorId}`)) {
      return
    }

    event.preventDefault()

    if (event.repeat || event.isComposing || !快捷键是否启用(options.enabled)) {
      return
    }

    void options.onFormatAndSave()
  }

  onMounted(() => {
    window.addEventListener('keydown', handleWindowKeydown)
  })

  onBeforeUnmount(() => {
    window.removeEventListener('keydown', handleWindowKeydown)
  })
}
