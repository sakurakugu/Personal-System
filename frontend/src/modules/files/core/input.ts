import { nextTick } from 'vue'
import type { ComponentPublicInstance } from 'vue'

const 资源行编辑输入框选择器 = '.resource-row--editing .resource-row__input'

function 聚焦并选中文本(input: globalThis.HTMLInputElement | null) {
  input?.focus()
  input?.select()
}

export async function 聚焦输入框(input: globalThis.HTMLInputElement | null) {
  await nextTick()
  window.requestAnimationFrame(() => {
    聚焦并选中文本(input)
  })
}

export async function 聚焦资源行输入框(input: globalThis.HTMLInputElement | null) {
  await nextTick()
  window.requestAnimationFrame(() => {
    聚焦并选中文本(
      input ?? document.querySelector<globalThis.HTMLInputElement>(资源行编辑输入框选择器),
    )
  })
}

export function 提取输入框元素(
  element: globalThis.Element | ComponentPublicInstance | null,
): globalThis.HTMLInputElement | null {
  return element instanceof globalThis.HTMLInputElement ? element : null
}

export async function 处理编辑输入框失焦(
  正在提交: boolean,
  onSubmit: () => Promise<void>,
) {
  if (正在提交) {
    return
  }
  await onSubmit()
}

export function 处理编辑输入框键盘事件(
  event: globalThis.KeyboardEvent,
  onSubmit: () => void,
  onCancel: () => void,
) {
  if (event.isComposing) {
    return
  }
  if (event.key === 'Enter') {
    event.preventDefault()
    event.stopPropagation()
    onSubmit()
    return
  }
  if (event.key === 'Escape') {
    event.preventDefault()
    event.stopPropagation()
    onCancel()
  }
}
