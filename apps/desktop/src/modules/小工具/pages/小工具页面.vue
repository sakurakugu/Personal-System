<script setup lang="ts">
import { useThemeStore } from '@/shared/stores/theme'
import { setDesktopWidgetWindowContentHeight } from '@/shared/window-manager'
import type { WidgetUtilityPanel } from '../types'
import WidgetHeader from '../components/WidgetHeader.vue'
import WidgetSettingsPanel from '../components/WidgetSettingsPanel.vue'
import WidgetTodoComposerPanel from '../components/WidgetTodoComposerPanel.vue'
import WidgetTodoListPanel from '../components/WidgetTodoListPanel.vue'
import { useDesktopWidgetWindowState } from '../composables/useDesktopWidgetWindowState'
import { useWidgetTodos } from '../composables/useWidgetTodos'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const theme = useThemeStore()

const {
  creatingTodo,
  loading,
  orderedTodos,
  todoDraft,
  createTodo,
  formatEndDate,
  handleToggleComplete,
  handleTogglePin,
  isOverdue,
  loadTodos,
} = useWidgetTodos()

const {
  defaultWidgetSurfaceOpacity,
  pinButtonIcon,
  pinButtonIconClass,
  pinButtonIconShellClass,
  pinButtonTitle,
  settingWidgetState,
  widgetMovable,
  widgetShowCloseButton,
  widgetSurfaceOpacity,
  widgetSurfaceOpaque,
  beginPinLongPress,
  cancelPinLongPress,
  handleCloseWindow,
  handleOpenMainWindow,
  handlePinButtonClick,
  resetWidgetSurfaceOpacity,
} = useDesktopWidgetWindowState()

const todoListExpanded = ref(true)
const activeUtilityPanel = ref<WidgetUtilityPanel>('none')
const widgetContentElement = ref<globalThis.HTMLElement | null>(null)

let widgetHeightObserver: globalThis.ResizeObserver | null = null
let widgetHeightSyncFrame: number | null = null
let lastSyncedWidgetHeight = 0

const todoListButtonTitle = computed(() => (todoListExpanded.value ? '收起待办列表' : '展开待办列表'))
const widgetSettingsButtonTitle = computed(() => (activeUtilityPanel.value === 'settings' ? '收起卡片设置' : '打开卡片设置'))
const widgetSurfaceBackground = computed(() => {
  if (widgetSurfaceOpaque.value) {
    return theme.isDark ? 'rgb(15, 23, 42)' : 'rgb(255, 255, 255)'
  }
  return `color-mix(in srgb, var(--desktop-panel) ${widgetSurfaceOpacity.value}%, transparent)`
})

function toggleSection(section: 'list' | Exclude<WidgetUtilityPanel, 'none'>) {
  if (section === 'list') {
    todoListExpanded.value = !todoListExpanded.value
    return
  }
  if (activeUtilityPanel.value === section) {
    activeUtilityPanel.value = 'none'
    return
  }
  activeUtilityPanel.value = section
}

async function handleCreateTodo() {
  await createTodo()
  if (!todoDraft.value.trim()) {
    activeUtilityPanel.value = 'none'
    todoListExpanded.value = true
  }
}

async function syncWidgetWindowHeight() {
  await nextTick()
  const element = widgetContentElement.value
  if (!element) {
    return
  }

  const rectHeight = Math.ceil(element.getBoundingClientRect().height)
  const scrollHeight = Math.ceil(element.scrollHeight)
  const offsetHeight = Math.ceil(element.offsetHeight)
  const nextHeight = Math.max(rectHeight, scrollHeight, offsetHeight)
  if (nextHeight <= 0 || nextHeight === lastSyncedWidgetHeight) {
    return
  }

  lastSyncedWidgetHeight = nextHeight
  await setDesktopWidgetWindowContentHeight(nextHeight)
}

function scheduleWidgetWindowHeightSync() {
  if (widgetHeightSyncFrame !== null) {
    window.cancelAnimationFrame(widgetHeightSyncFrame)
  }

  widgetHeightSyncFrame = window.requestAnimationFrame(() => {
    widgetHeightSyncFrame = null
    void syncWidgetWindowHeight()
  })
}

onMounted(() => {
  widgetHeightObserver = new window.ResizeObserver(() => {
    scheduleWidgetWindowHeightSync()
  })
  if (widgetContentElement.value) {
    widgetHeightObserver.observe(widgetContentElement.value)
  }
  scheduleWidgetWindowHeightSync()
})

onBeforeUnmount(() => {
  widgetHeightObserver?.disconnect()
  widgetHeightObserver = null
  if (widgetHeightSyncFrame !== null) {
    window.cancelAnimationFrame(widgetHeightSyncFrame)
    widgetHeightSyncFrame = null
  }
})

watch(
  [
    loading,
    todoListExpanded,
    activeUtilityPanel,
    creatingTodo,
    todoDraft,
    orderedTodos,
  ],
  () => {
    scheduleWidgetWindowHeightSync()
  },
  { deep: true },
)
</script>

<template>
  <div class="widget-page">
    <div
      ref="widgetContentElement"
      class="widget-shell"
      :class="{
        'widget-shell--movable': widgetMovable,
        'widget-shell--dark': theme.isDark,
        'widget-shell--opaque': widgetSurfaceOpaque,
      }"
      :style="{
        '--widget-surface-background': widgetSurfaceBackground,
      }"
    >
      <WidgetHeader
        :active-utility-panel="activeUtilityPanel"
        :pin-button-icon="pinButtonIcon"
        :pin-button-icon-class="pinButtonIconClass"
        :pin-button-icon-shell-class="pinButtonIconShellClass"
        :pin-button-title="pinButtonTitle"
        :setting-widget-state="settingWidgetState"
        :todo-list-button-title="todoListButtonTitle"
        :todo-list-expanded="todoListExpanded"
        :widget-movable="widgetMovable"
        :widget-settings-button-title="widgetSettingsButtonTitle"
        :widget-show-close-button="widgetShowCloseButton"
        @close-window="handleCloseWindow"
        @open-main-window="handleOpenMainWindow"
        @pin-button-click="handlePinButtonClick"
        @pin-long-press-end="cancelPinLongPress"
        @pin-long-press-start="beginPinLongPress"
        @toggle-settings-panel="toggleSection('settings')"
        @toggle-todo-list="toggleSection('list')"
      />

      <WidgetSettingsPanel
        :visible="activeUtilityPanel === 'settings'"
        :widget-show-close-button="widgetShowCloseButton"
        :widget-surface-opacity="widgetSurfaceOpacity"
        :default-widget-surface-opacity="defaultWidgetSurfaceOpacity"
        :theme-hue="theme.hue"
        :default-theme-hue="theme.defaultHue"
        @reset-widget-surface-opacity="resetWidgetSurfaceOpacity"
        @update:theme-hue="theme.setHue"
        @update:widget-show-close-button="widgetShowCloseButton = $event"
        @update:widget-surface-opacity="widgetSurfaceOpacity = $event"
      />

      <WidgetTodoListPanel
        :visible="todoListExpanded"
        :active-utility-panel="activeUtilityPanel"
        :loading="loading"
        :ordered-todos="orderedTodos"
        :format-end-date="formatEndDate"
        :is-overdue="isOverdue"
        @refresh="loadTodos"
        @toggle-add-panel="toggleSection('add')"
        @toggle-complete="handleToggleComplete"
        @toggle-pin="handleTogglePin"
      />

      <WidgetTodoComposerPanel
        :visible="activeUtilityPanel === 'add'"
        :draft="todoDraft"
        :creating-todo="creatingTodo"
        @clear="todoDraft = ''"
        @submit="handleCreateTodo"
        @update:draft="todoDraft = $event"
      />
    </div>
  </div>
</template>

<style>
.widget-page {
  --widget-window-radius: 8px;
  --widget-surface-background: color-mix(in srgb, var(--desktop-panel) 100%, transparent);
  padding: 0;
  background: transparent;
  overflow: hidden;
  scrollbar-width: none;
  overscroll-behavior: none;
}

.widget-page::-webkit-scrollbar {
  display: none;
}

.widget-shell {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 0;
  border-radius: 0;
  overflow: visible;
  background: transparent;
  border: none;
  box-shadow: none;
}

.widget-shell--dark {
  background: transparent;
}

.widget-header,
.widget-panel {
  position: relative;
  z-index: 1;
}

.widget-no-drag {
  -webkit-app-region: no-drag;
}

.panel-header p,
.composer__label,
.setting-row p,
.todo-item__main p {
  margin: 0;
  color: var(--desktop-text-muted);
}

.widget-icon-button {
  width: 34px;
  height: 34px;
  padding: 0;
}

.widget-panel {
  border-radius: var(--widget-window-radius);
  border: none;
  background: var(--widget-surface-background);
  backdrop-filter: blur(10px);
}

.widget-shell--opaque .widget-panel {
  backdrop-filter: none;
}

.widget-panel--list {
  overflow: hidden;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding: 16px 18px 8px;
  border: none;
  background: transparent;
  color: inherit;
  text-align: left;
  cursor: pointer;
}

.panel-header--static {
  cursor: default;
}

.panel-header__left,
.panel-header__right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.panel-header__right {
  gap: 0;
}

.panel-header__title {
  position: relative;
  margin: 0 0 0 16px;
  color: var(--desktop-text);
  font-size: 1.125rem;
  font-weight: 700;
  line-height: 1.4;
}

.panel-header__title::before {
  content: '';
  position: absolute;
  top: 50%;
  left: -16px;
  width: 4px;
  height: 16px;
  border-radius: 2px;
  background: var(--desktop-accent);
  transform: translateY(-50%);
}

.panel-body {
  padding: 0 16px 16px;
}

.panel-body--settings {
  display: grid;
  gap: 16px;
}

.settings-divider {
  height: 1px;
  background: color-mix(in srgb, var(--desktop-border) 84%, transparent);
}

@media (max-width: 480px) {
  .widget-page {
    padding: 0;
  }

  .widget-shell {
    padding: 0;
    border-radius: 0;
  }
}
</style>
