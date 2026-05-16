import { onBeforeUnmount, onMounted, toValue } from 'vue'
import type { MaybeRefOrGetter } from 'vue'

interface SaveShortcutOptions {
  enabled?: MaybeRefOrGetter<boolean>
  onSave: () => void | Promise<unknown>
}

function 是否是保存快捷键(event: globalThis.KeyboardEvent): boolean {
  return (event.ctrlKey || event.metaKey)
    && !event.altKey
    && !event.shiftKey
    && event.key.toLowerCase() === 's'
}

export function 使用保存快捷键(options: SaveShortcutOptions) {
  function 处理按键(event: globalThis.KeyboardEvent) {
    if (!是否是保存快捷键(event)) {
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
    window.addEventListener('keydown', 处理按键)
  })

  onBeforeUnmount(() => {
    window.removeEventListener('keydown', 处理按键)
  })
}
