<script setup lang="ts">
import { CloseBold, Plus } from '@element-plus/icons-vue'
import { computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useDesktopRouteTabs } from '../../shared/composables/useDesktopRouteTabs'
import { useDesktopTabsStore } from '../../shared/stores/tabs'

const route = useRoute()
const { openDesktopRoute } = useDesktopRouteTabs()
const tabsStore = useDesktopTabsStore()

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

function handleActivateTab(id: string) {
  const tab = tabsStore.activateTab(id)
  if (!tab || tab.path === route.path) {
    return
  }

  void openDesktopRoute(tab.path)
}

function handleAddTab() {
  const tab = tabsStore.openRoute('/')
  if (tab.path === route.path) {
    return
  }

  void openDesktopRoute(tab.path)
}

function handleCloseTab(event: globalThis.MouseEvent, id: string) {
  event.stopPropagation()
  const nextTab = tabsStore.closeTab(id)
  if (!nextTab || nextTab.path === route.path) {
    return
  }

  void openDesktopRoute(nextTab.path)
}
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
