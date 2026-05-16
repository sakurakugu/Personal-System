import { onBeforeUnmount, reactive } from 'vue'

interface LongPressSelectionOptions<T> {
  delay?: number
  getId: (item: T) => string
  onLongPress: (item: T) => void
}

export function 使用长按选择<T>(options: LongPressSelectionOptions<T>) {
  const delay = options.delay ?? 520
  const timers = reactive<Record<string, ReturnType<typeof setTimeout> | null>>({})
  const triggered = reactive<Record<string, boolean>>({})

  function 清除定时器(id: string) {
    const timer = timers[id]
    if (timer !== null && timer !== undefined) {
      clearTimeout(timer)
      timers[id] = null
    }
  }

  function 开始长按(item: T, event?: Event) {
    if (event instanceof MouseEvent && event.button !== 0) {
      return
    }

    const id = options.getId(item)
    清除定时器(id)
    triggered[id] = false
    timers[id] = setTimeout(() => {
      triggered[id] = true
      options.onLongPress(item)
      timers[id] = null
    }, delay)
  }

  function 取消长按(item: T) {
    清除定时器(options.getId(item))
  }

  function 消费长按(item: T): boolean {
    const id = options.getId(item)
    const wasTriggered = Boolean(triggered[id])
    triggered[id] = false
    return wasTriggered
  }

  onBeforeUnmount(() => {
    Object.keys(timers).forEach(清除定时器)
  })

  return {
    开始长按,
    取消长按,
    消费长按,
    startLongPress: 开始长按,
    cancelLongPress: 取消长按,
    consumeLongPress: 消费长按,
  }
}
