<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { findDesktopNavItem } from '../navigation'

const route = useRoute()

const currentNavItem = computed(() => findDesktopNavItem(route.path))

const currentTitle = computed(() => {
  return currentNavItem.value?.label ?? (typeof route.meta.title === 'string' ? route.meta.title : '工作区')
})
</script>

<template>
  <header class="desktop-tabbar">
    <div class="desktop-tabbar__tabs" role="tablist" aria-label="页面标签">
      <div class="desktop-tabbar__tab desktop-tabbar__tab--active" role="tab" aria-selected="true">
        <component
          :is="currentNavItem?.icon"
          v-if="currentNavItem"
          class="desktop-tabbar__tab-icon"
          aria-hidden="true"
        />
        <span class="desktop-tabbar__tab-label">{{ currentTitle }}</span>
      </div>
      <div class="desktop-tabbar__tab-rail" aria-hidden="true" />
    </div>
  </header>
</template>

<style scoped>
.desktop-tabbar {
  /* 不加padding */
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
  height: 34px;
}

.desktop-tabbar__tab {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  max-width: min(260px, 100%);
  height: 100%;
  padding: 0 12px;
  border: none;
  border-right: 1px solid color-mix(in srgb, var(--desktop-border) 82%, transparent);
  color: color-mix(in srgb, var(--desktop-text) 82%, transparent);
  background: color-mix(in srgb, var(--desktop-panel) 58%, transparent);
  cursor: default;
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
  max-width: 180px;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 12px;
  font-weight: 600;
  line-height: 1;
}

.desktop-tabbar__tab-icon {
  flex: 0 0 auto;
  width: 14px;
  height: 14px;
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
  .desktop-tabbar {
    padding-top: 6px;
    padding-bottom: 6px;
  }

  .desktop-tabbar__tabs {
    width: 100%;
  }

  .desktop-tabbar__tab {
    max-width: 180px;
    padding: 0 10px;
  }
}
</style>
