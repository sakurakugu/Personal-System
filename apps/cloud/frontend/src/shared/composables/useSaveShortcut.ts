import { onBeforeUnmount, onMounted, toValue } from 'vue'
import type { MaybeRefOrGetter } from 'vue'

interface SaveShortcutOptions {
  enabled?: MaybeRefOrGetter<boolean>
  onSave: () => void | Promise<unknown>
}

function 是否为保存快捷键(event: globalThis.KeyboardEvent): boolean {
  return (event.ctrlKey || event.metaKey)
    && !event.altKey
    && !event.shiftKey
    && event.key.toLowerCase() === 's'
}

export function useSaveShortcut(options: SaveShortcutOptions) {
  function 处理键盘事件(event: globalThis.KeyboardEvent) {
    if (!是否为保存快捷键(event)) {
      return
    }

    event.preventDefault()

    if (event.repeat || event.isComposing) {
      return
    }

    if (options.enabled !== undefined && !toValue(options.enabled)) {
      return
    }

    void options.onSave()
  }

  onMounted(() => {
    window.addEventListener('keydown', 处理键盘事件)
  })

  onBeforeUnmount(() => {
    window.removeEventListener('keydown', 处理键盘事件)
  })
}
