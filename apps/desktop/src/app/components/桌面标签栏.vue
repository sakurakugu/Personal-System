<script setup lang="ts">
import { CloseBold, Plus } from '@element-plus/icons-vue'
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { 使用桌面路由标签 } from '../../shared/composables/使用桌面路由标签'
import { 使用桌面标签存储 } from '../../shared/stores/tabs'

const route = useRoute()
const { 打开桌面路由 } = 使用桌面路由标签()
const tabsStore = 使用桌面标签存储()

tabsStore.init(route.path)

watch(
  () => route.path,
  (path) => {
    tabsStore.syncActiveRoute(path)
  },
  { immediate: true },
)

const tabs = computed(() => tabsStore.tabs)
const activeTabId = computed(() => tabsStore.activeTabId)
const contextMenuRef = ref<globalThis.HTMLDivElement>()
const contextMenuVisible = ref(false)
const contextMenuTabId = ref('')
const contextMenuX = ref(0)
const contextMenuY = ref(0)

const contextMenuTab = computed(() => {
  return tabs.value.find((tab) => tab.id === contextMenuTabId.value) ?? null
})

const canCloseOthers = computed(() => {
  return tabs.value.length > 1
})

const canCloseRight = computed(() => {
  const currentIndex = tabs.value.findIndex((tab) => tab.id === contextMenuTabId.value)
  return currentIndex >= 0 && currentIndex < tabs.value.length - 1
})

function closeContextMenu() {
  contextMenuVisible.value = false
}

function updateContextMenuPosition() {
  const menuElement = contextMenuRef.value
  if (!menuElement) {
    return
  }

  const margin = 8
  contextMenuX.value = Math.min(contextMenuX.value, window.innerWidth - menuElement.offsetWidth - margin)
  contextMenuY.value = Math.min(contextMenuY.value, window.innerHeight - menuElement.offsetHeight - margin)
  contextMenuX.value = Math.max(margin, contextMenuX.value)
  contextMenuY.value = Math.max(margin, contextMenuY.value)
}

function handleActivateTab(id: string) {
  closeContextMenu()
  const tab = tabsStore.activateTab(id)
  if (!tab || tab.path === route.path) {
    return
  }

  void 打开桌面路由(tab.path)
}

function handleAddTab() {
  closeContextMenu()
  void 打开桌面路由('/', { newTab: true })
}

function handleCloseTab(event: globalThis.MouseEvent, id: string) {
  event.stopPropagation()
  closeContextMenu()
  const nextTab = tabsStore.closeTab(id)
  if (!nextTab || nextTab.path === route.path) {
    return
  }

  void 打开桌面路由(nextTab.path)
}

function handleTabContextMenu(event: globalThis.MouseEvent, id: string) {
  event.preventDefault()
  contextMenuTabId.value = id
  contextMenuX.value = event.clientX
  contextMenuY.value = event.clientY
  contextMenuVisible.value = true
  window.requestAnimationFrame(() => updateContextMenuPosition())
}

function handleCloseCurrentTab() {
  const targetTabId = contextMenuTabId.value
  closeContextMenu()
  if (!targetTabId) {
    return
  }

  const nextTab = tabsStore.closeTab(targetTabId)
  if (!nextTab || nextTab.path === route.path) {
    return
  }

  void 打开桌面路由(nextTab.path)
}

function handleCloseOtherTabs() {
  const targetTab = contextMenuTab.value
  closeContextMenu()
  if (!targetTab) {
    return
  }

  const nextTab = tabsStore.closeOtherTabs(targetTab.id)
  if (!nextTab || nextTab.path === route.path) {
    return
  }

  void 打开桌面路由(nextTab.path)
}

function handleCloseTabsToRight() {
  const targetTabId = contextMenuTabId.value
  closeContextMenu()
  if (!targetTabId) {
    return
  }

  const nextTab = tabsStore.closeTabsToRight(targetTabId)
  if (!nextTab || nextTab.path === route.path) {
    return
  }

  void 打开桌面路由(nextTab.path)
}

function handleDocumentPointerDown(event: globalThis.PointerEvent) {
  const target = event.target
  if (target instanceof globalThis.Node && contextMenuRef.value?.contains(target)) {
    return
  }

  closeContextMenu()
}

function handleDocumentKeyDown(event: globalThis.KeyboardEvent) {
  if (event.key === 'Escape') {
    closeContextMenu()
  }
}

watch(contextMenuVisible, (visible) => {
  if (!visible) {
    document.removeEventListener('pointerdown', handleDocumentPointerDown)
    document.removeEventListener('keydown', handleDocumentKeyDown)
    window.removeEventListener('blur', closeContextMenu)
    window.removeEventListener('resize', closeContextMenu)
    return
  }

  document.addEventListener('pointerdown', handleDocumentPointerDown)
  document.addEventListener('keydown', handleDocumentKeyDown)
  window.addEventListener('blur', closeContextMenu)
  window.addEventListener('resize', closeContextMenu)
})

onBeforeUnmount(() => {
  closeContextMenu()
  document.removeEventListener('pointerdown', handleDocumentPointerDown)
  document.removeEventListener('keydown', handleDocumentKeyDown)
  window.removeEventListener('blur', closeContextMenu)
  window.removeEventListener('resize', closeContextMenu)
})
</script>

<template>
  <header class="desktop-tabbar">
    <div class="desktop-tabbar__tabs" role="tablist" aria-label="页面标签">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        type="button"
        class="desktop-tabbar__tab"
        :class="{ 'desktop-tabbar__tab--active': tab.id === activeTabId }"
        role="tab"
        :aria-selected="tab.id === activeTabId"
        @click="handleActivateTab(tab.id)"
        @contextmenu="handleTabContextMenu($event, tab.id)"
      >
        <component
          :is="tabsStore.getTabIcon(tab.path)"
          v-if="tabsStore.getTabIcon(tab.path)"
          class="desktop-tabbar__tab-icon"
          aria-hidden="true"
        />
        <span class="desktop-tabbar__tab-label">{{ tab.title }}</span>
        <span class="desktop-tabbar__tab-close" aria-hidden="true" @click="handleCloseTab($event, tab.id)">
          <CloseBold />
        </span>
      </button>

      <button
        type="button"
        class="desktop-tabbar__add"
        aria-label="新增标签页"
        @click="handleAddTab"
      >
        <Plus />
      </button>

      <div class="desktop-tabbar__tab-rail" aria-hidden="true" />
    </div>

    <Teleport to="body">
      <Transition name="desktop-tabbar-menu">
        <div
          v-if="contextMenuVisible"
          ref="contextMenuRef"
          class="desktop-tabbar__context-menu"
          :style="{ left: `${contextMenuX}px`, top: `${contextMenuY}px` }"
          @contextmenu.prevent
        >
          <button type="button" class="desktop-tabbar__context-menu-item" @click="handleCloseCurrentTab">
            关闭当前标签页
          </button>
          <button
            type="button"
            class="desktop-tabbar__context-menu-item"
            :disabled="!canCloseOthers"
            @click="handleCloseOtherTabs"
          >
            关闭其他标签页
          </button>
          <button
            type="button"
            class="desktop-tabbar__context-menu-item"
            :disabled="!canCloseRight"
            @click="handleCloseTabsToRight"
          >
            关闭右侧标签页
          </button>
        </div>
      </Transition>
    </Teleport>
  </header>
</template>

<style scoped>
.desktop-tabbar {
  display: flex;
  align-items: center;
  min-height: 34px;
  border-bottom: 1px solid var(--desktop-border);
  background: color-mix(in srgb, var(--desktop-panel) 72%, transparent);
}

.desktop-tabbar__tabs {
  position: relative;
  display: flex;
  align-items: stretch;
  min-width: 0;
  width: 100%;
  height: 34px;
}

.desktop-tabbar__tab,
.desktop-tabbar__add {
  appearance: none;
  border: none;
  outline: none;
}

.desktop-tabbar__tab {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  min-width: 0;
  max-width: min(260px, 100%);
  height: 100%;
  padding: 0 6px 0 12px;
  border-right: 1px solid color-mix(in srgb, var(--desktop-border) 82%, transparent);
  color: color-mix(in srgb, var(--desktop-text) 82%, transparent);
  background: color-mix(in srgb, var(--desktop-panel) 58%, transparent);
  cursor: pointer;
  transition:
    background-color 0.2s ease,
    color 0.2s ease;
}

.desktop-tabbar__tab::before {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  left: 0;
  height: 2px;
  background: transparent;
  transition: background-color 0.2s ease;
}

.desktop-tabbar__tab:hover {
  color: var(--desktop-text);
  background: color-mix(in srgb, var(--desktop-panel) 90%, var(--desktop-accent) 10%);
}

.desktop-tabbar__tab:hover .desktop-tabbar__tab-close {
  opacity: 1;
}

.desktop-tabbar__tab--active {
  color: var(--desktop-text);
  background: color-mix(in srgb, var(--desktop-panel) 94%, var(--desktop-accent) 6%);
  box-shadow:
    inset 0 -1px 0 color-mix(in srgb, var(--desktop-panel) 96%, transparent),
    inset -1px 0 0 color-mix(in srgb, var(--desktop-border) 82%, transparent);
}

.desktop-tabbar__tab--active::before {
  background: var(--desktop-accent);
}

.desktop-tabbar__tab-label {
  display: inline-block;
  overflow: hidden;
  flex: 1;
  min-width: 0;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 12px;
  font-weight: 400;
  line-height: 1;
}

.desktop-tabbar__tab-icon {
  flex: 0 0 auto;
  width: 14px;
  height: 14px;
}

.desktop-tabbar__tab-close,
.desktop-tabbar__add {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
  border-radius: 5px;
  color: color-mix(in srgb, var(--desktop-text) 68%, transparent);
  transition:
    opacity 0.2s ease,
    color 0.2s ease,
    background-color 0.2s ease;
}

.desktop-tabbar__tab-close {
  width: 16px;
  height: 16px;
  margin-right: -2px;
  opacity: 0;
}

.desktop-tabbar__tab-close :deep(svg) {
  width: 10px;
  height: 10px;
}

.desktop-tabbar__add {
  width: 22px;
  height: 22px;
}

.desktop-tabbar__add :deep(svg) {
  width: 17px;
  height: 17px;
}

.desktop-tabbar__tab-close:hover,
.desktop-tabbar__add:hover {
  color: var(--desktop-text);
  background: color-mix(in srgb, var(--desktop-panel) 76%, var(--desktop-accent) 24%);
}

.desktop-tabbar__add {
  margin-left: 2px;
  align-self: center;
  background: transparent;
  cursor: pointer;
}

.desktop-tabbar__tab-rail {
  position: absolute;
  right: 0;
  bottom: 0;
  left: 0;
  height: 1px;
  background: var(--desktop-border);
  pointer-events: none;
}

.desktop-tabbar__context-menu {
  position: fixed;
  z-index: 3000;
  width: max-content;
  max-width: calc(100vw - 16px);
  padding: 6px;
  border: 1px solid color-mix(in srgb, var(--desktop-border) 86%, transparent);
  border-radius: 12px;
  background: color-mix(in srgb, var(--desktop-panel) 96%, #ffffff 4%);
  box-shadow:
    0 18px 40px rgba(15, 23, 42, 0.16),
    0 4px 12px rgba(15, 23, 42, 0.1);
  backdrop-filter: blur(18px) saturate(160%);
}

.desktop-tabbar__context-menu-item {
  display: block;
  width: 100%;
  padding: 8px 10px;
  border: none;
  border-radius: 8px;
  color: var(--desktop-text);
  background: transparent;
  text-align: left;
  font-size: 13px;
  white-space: nowrap;
  cursor: pointer;
  transition:
    color 0.2s ease,
    background-color 0.2s ease;
}

.desktop-tabbar__context-menu-item:hover {
  color: var(--desktop-text);
  background: color-mix(in srgb, var(--desktop-panel) 78%, var(--desktop-accent) 22%);
}

.desktop-tabbar__context-menu-item:disabled {
  color: color-mix(in srgb, var(--desktop-text) 42%, transparent);
  background: transparent;
  cursor: not-allowed;
}

.desktop-tabbar__context-menu-item:disabled:hover {
  background: transparent;
}

.desktop-tabbar-menu-enter-active,
.desktop-tabbar-menu-leave-active {
  transition:
    opacity 0.16s ease,
    transform 0.16s ease;
}

.desktop-tabbar-menu-enter-from,
.desktop-tabbar-menu-leave-to {
  opacity: 0;
  transform: translateY(4px) scale(0.98);
}

@media (max-width: 960px) {
  .desktop-tabbar__tab {
    max-width: 180px;
    padding: 0 5px 0 10px;
  }

  .desktop-tabbar__tab-close {
    width: 16px;
  }
}
</style>
