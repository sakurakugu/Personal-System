import { ref } from 'vue'
import type {
  ToolbarAction,
  ToolbarItem,
  ToolbarOverflowMenuOption,
  ToolbarOverflowSubmenuEntry,
} from './MilkdownMarkdown工具栏类型'

interface 使用MilkdownMarkdown工具栏菜单选项 {
  moreKey: string
  getToolbarItemKey: (item: ToolbarItem, index: number) => string
  runAction: (action: ToolbarAction, payload?: string | number) => void
}

export function 使用MilkdownMarkdown工具栏菜单(options: 使用MilkdownMarkdown工具栏菜单选项) {
  const activeDropdownKey = ref('')
  const activeDropdownStyle = ref<Record<string, string>>({})
  const activeOverflowSubmenuKey = ref('')

  function toggleToolbarDropdown(item: ToolbarItem, index: number, event: MouseEvent) {
    const itemKey = options.getToolbarItemKey(item, index)
    if (activeDropdownKey.value === itemKey) {
      closeToolbarDropdown()
      return
    }

    openToolbarDropdown(item, index, event)
  }

  function openToolbarDropdown(item: ToolbarItem, index: number, event: MouseEvent | FocusEvent) {
    const target = event.currentTarget
    if (!(target instanceof HTMLElement)) {
      return
    }

    const rect = target.getBoundingClientRect()
    activeDropdownKey.value = options.getToolbarItemKey(item, index)
    activeDropdownStyle.value = {
      left: `${rect.left}px`,
      top: `${rect.bottom + 4}px`,
    }
  }

  function toggleToolbarMoreDropdown(event: MouseEvent) {
    if (activeDropdownKey.value === options.moreKey) {
      closeToolbarDropdown()
      return
    }

    openToolbarMoreDropdown(event)
  }

  function openToolbarMoreDropdown(event: MouseEvent | FocusEvent) {
    const target = event.currentTarget
    if (!(target instanceof HTMLElement)) {
      return
    }

    const rect = target.getBoundingClientRect()
    activeDropdownKey.value = options.moreKey
    activeOverflowSubmenuKey.value = ''
    activeDropdownStyle.value = {
      left: `${rect.left}px`,
      top: `${rect.bottom + 4}px`,
    }
  }

  function handleToolbarOverflowMenuClick(entry: ToolbarOverflowMenuOption) {
    if (entry.disabled?.()) {
      return
    }

    if (entry.children?.length) {
      activeOverflowSubmenuKey.value = activeOverflowSubmenuKey.value === entry.key ? '' : entry.key
      return
    }

    options.runAction(entry.action, entry.payload)
    closeToolbarDropdown()
  }

  function openToolbarOverflowSubmenu(entry: ToolbarOverflowMenuOption) {
    if (!entry.children?.length || entry.disabled?.()) {
      activeOverflowSubmenuKey.value = ''
      return
    }

    activeOverflowSubmenuKey.value = entry.key
  }

  function handleToolbarOverflowSubmenuClick(entry: ToolbarOverflowSubmenuEntry) {
    if (entry.kind === 'divider') {
      return
    }

    options.runAction(entry.action, entry.payload)
    closeToolbarDropdown()
  }

  function closeToolbarDropdown() {
    activeDropdownKey.value = ''
    activeOverflowSubmenuKey.value = ''
  }

  function handleDocumentPointerDown(event: PointerEvent) {
    const target = event.target
    if (!(target instanceof Element)) {
      return
    }

    if (
      target.closest('.milkdown-markdown-editor__toolbar-dropdown')
      || target.closest('.milkdown-markdown-editor__toolbar-menu')
    ) {
      return
    }

    closeToolbarDropdown()
  }

  return {
    activeDropdownKey,
    activeDropdownStyle,
    activeOverflowSubmenuKey,
    toggleToolbarDropdown,
    openToolbarDropdown,
    toggleToolbarMoreDropdown,
    openToolbarMoreDropdown,
    handleToolbarOverflowMenuClick,
    openToolbarOverflowSubmenu,
    handleToolbarOverflowSubmenuClick,
    closeToolbarDropdown,
    handleDocumentPointerDown,
  }
}
