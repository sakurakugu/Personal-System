<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'
import DesktopHeader from '../components/DesktopHeader.vue'
import DesktopTabbar from '../components/DesktopTabbar.vue'
import { getDesktopSidebarNavItems, isDesktopNavItemActive } from '../navigation'

const route = useRoute()
const currentSidebarNavItems = computed(() => getDesktopSidebarNavItems(route.path))
</script>

<template>
  <div class="desktop-layout">
    <DesktopHeader class="desktop-layout__header" />

    <aside class="desktop-sidebar">
      <nav class="desktop-nav">
        <RouterLink
          v-for="item in currentSidebarNavItems.filter((navItem) => !navItem.disabled)"
          :key="item.to"
          :to="item.to"
          class="desktop-nav__link"
          :class="{ 'desktop-nav__link--active': isDesktopNavItemActive(route.path, item.to) }"
        >
          <component :is="item.icon" class="desktop-nav__icon" />
          <span>{{ item.label }}</span>
        </RouterLink>
        <div
          v-for="item in currentSidebarNavItems.filter((navItem) => navItem.disabled)"
          :key="item.to"
          class="desktop-nav__link desktop-nav__link--disabled"
        >
          <component :is="item.icon" class="desktop-nav__icon" />
          <span>{{ item.label }}</span>
        </div>
      </nav>
    </aside>

    <section class="desktop-workspace">
      <DesktopTabbar />
      <main class="desktop-main">
        <RouterView />
      </main>
    </section>
  </div>
</template>

<style scoped>
.desktop-layout {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  grid-template-columns: 260px minmax(0, 1fr);
  min-height: 100vh;
  background: var(--desktop-bg);
}

.desktop-layout__header {
  grid-column: 1 / -1;
}

.desktop-sidebar {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 16px;
  border-right: 1px solid var(--desktop-border);
  background: var(--desktop-panel);
}

.desktop-nav {
  display: grid;
  gap: 8px;
}

.desktop-nav__link {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  border-radius: 14px;
  color: var(--desktop-text);
  text-decoration: none;
  transition: background-color 0.2s ease;
}

.desktop-nav__link:hover {
  background: var(--desktop-hover);
}

.desktop-nav__link--active {
  color: #fff;
  background: var(--desktop-accent);
}

.desktop-nav__link--disabled {
  color: color-mix(in srgb, var(--desktop-text) 48%, transparent);
  cursor: not-allowed;
}

.desktop-nav__icon {
  width: 18px;
  height: 18px;
}

.desktop-main {
  min-width: 0;
  padding: 24px;
}

.desktop-workspace {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  min-width: 0;
}

@media (max-width: 960px) {
  .desktop-layout {
    grid-template-columns: 1fr;
    grid-template-rows: auto auto minmax(0, 1fr);
  }

  .desktop-sidebar {
    border-right: 0;
    border-bottom: 1px solid var(--desktop-border);
  }
}
</style>
