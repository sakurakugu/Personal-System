import { onBeforeUnmount, onMounted, toValue } from 'vue'
import type { MaybeRefOrGetter } from 'vue'

interface SaveShortcutOptions {
  enabled?: MaybeRefOrGetter<boolean>
  onSave: () => void | Promise<unknown>
}

function isSaveShortcut(event: globalThis.KeyboardEvent): boolean {
  return (event.ctrlKey || event.metaKey)
    && !event.altKey
    && !event.shiftKey
    && event.key.toLowerCase() === 's'
}

export function useSaveShortcut(options: SaveShortcutOptions) {
  function handleKeydown(event: globalThis.KeyboardEvent) {
    if (!isSaveShortcut(event)) {
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
    window.addEventListener('keydown', handleKeydown)
  })

  onBeforeUnmount(() => {
    window.removeEventListener('keydown', handleKeydown)
  })
}
