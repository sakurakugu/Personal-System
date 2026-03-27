import { onBeforeUnmount, reactive } from 'vue'

interface LongPressSelectionOptions<T> {
  delay?: number
  getId: (item: T) => string
  onLongPress: (item: T) => void
}

export function useLongPressSelection<T>(options: LongPressSelectionOptions<T>) {
  const delay = options.delay ?? 520
  const timers = reactive<Record<string, ReturnType<typeof setTimeout> | null>>({})
  const triggered = reactive<Record<string, boolean>>({})

  function clearTimer(id: string) {
    const timer = timers[id]
    if (timer !== null && timer !== undefined) {
      clearTimeout(timer)
      timers[id] = null
    }
  }

  function startLongPress(item: T, event?: Event) {
    if (event instanceof MouseEvent && event.button !== 0) {
      return
    }

    const id = options.getId(item)
    clearTimer(id)
    triggered[id] = false
    timers[id] = setTimeout(() => {
      triggered[id] = true
      options.onLongPress(item)
      timers[id] = null
    }, delay)
  }

  function cancelLongPress(item: T) {
    clearTimer(options.getId(item))
  }

  function consumeLongPress(item: T): boolean {
    const id = options.getId(item)
    const wasTriggered = Boolean(triggered[id])
    triggered[id] = false
    return wasTriggered
  }

  onBeforeUnmount(() => {
    Object.keys(timers).forEach(clearTimer)
  })

  return {
    startLongPress,
    cancelLongPress,
    consumeLongPress,
  }
}
