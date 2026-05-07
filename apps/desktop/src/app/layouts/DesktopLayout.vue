<script setup lang="ts">
import { SidebarBottomHandle, useSidebarLayout } from '@personal-system/ui'
import { computed } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'
import DesktopHeader from '../components/DesktopHeader.vue'
import DesktopTabbar from '../components/DesktopTabbar.vue'
import { getDesktopSidebarNavItems, isDesktopNavItemActive } from '../navigation'

const route = useRoute()
const currentSidebarNavItems = computed(() => getDesktopSidebarNavItems(route.path))
const {
  handleBottom,
  isHandleDragging,
  isResizing,
  isCompact,
  isHidden,
  showResizeHandle,
  currentSiderWidth,
  triggerText,
  onHandleTouchStart,
  onHandleClick,
  onResizerPointerDown,
} = useSidebarLayout('desktop_sider_mode', {
  默认展开宽度: 260,
  最小展开宽度: 180,
  最大展开宽度: 360,
  主内容最小宽度: 420,
})
</script>

<template>
  <div class="desktop-layout" :class="{ 'desktop-layout--sidebar-hidden': isHidden }">
    <DesktopHeader class="desktop-layout__header" />

    <aside
      class="desktop-sidebar"
      :class="{
        'desktop-sidebar--compact': isCompact,
        'desktop-sidebar--hidden': isHidden,
        'desktop-sidebar--resizing': isResizing,
      }"
      :style="{ width: `${currentSiderWidth}px` }"
    >
      <div class="desktop-sidebar__inner">
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

        <SidebarBottomHandle
          :hidden="isHidden"
          :compact="isCompact"
          :dragging="isHandleDragging"
          :bottom="handleBottom"
          :text="triggerText"
          @toggle="onHandleClick"
          @drag-start="onHandleTouchStart"
        />
      </div>

      <button
        v-if="showResizeHandle"
        type="button"
        class="desktop-sidebar__resizer"
        :class="{ 'is-dragging': isResizing }"
        aria-label="拖动调整侧栏宽度"
        @pointerdown="onResizerPointerDown"
      >
        <span class="desktop-sidebar__resizer-handle" />
      </button>
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
  grid-template-columns: auto minmax(0, 1fr);
  height: 100vh;
  overflow: hidden;
  background: var(--desktop-bg);
}

.desktop-layout__header {
  grid-column: 1 / -1;
}

.desktop-sidebar {
  position: relative;
  display: flex;
  min-width: 0;
  min-height: 0;
  background:
    linear-gradient(180deg, color-mix(in srgb, var(--desktop-panel) 96%, #ffffff 4%), var(--desktop-panel));
  transition: width 0.24s cubic-bezier(0.22, 1, 0.36, 1);
  overflow: hidden;
}

.desktop-sidebar--resizing {
  transition: none;
}

.desktop-sidebar__inner {
  display: flex;
  flex: 1;
  flex-direction: column;
  padding: 16px;
  overflow: hidden;
}

.desktop-nav {
  display: grid;
  gap: 8px;
  flex: 1;
  align-content: start;
  min-height: 0;
  overflow-y: auto;
  scrollbar-width: none;
}

.desktop-nav::-webkit-scrollbar {
  display: none;
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
  flex: 0 0 auto;
}

.desktop-sidebar__resizer {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  width: 8px;
  padding: 0;
  border: none;
  background: transparent;
  cursor: col-resize;
  touch-action: none;
}

.desktop-sidebar__resizer::before {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  width: 1px;
  background: transparent;
  opacity: 0;
}

.desktop-sidebar__resizer-handle {
  position: absolute;
  top: 50%;
  right: 2px;
  width: 3px;
  height: 92px;
  border-radius: 999px;
  transform: translateY(-50%);
  background: linear-gradient(
    180deg,
    color-mix(in srgb, var(--desktop-accent) 14%, transparent),
    color-mix(in srgb, var(--desktop-accent) 48%, transparent),
    color-mix(in srgb, var(--desktop-accent) 14%, transparent)
  );
  opacity: 0;
}

.desktop-sidebar--compact .desktop-nav__link span {
  opacity: 0;
  transform: translateX(-8px);
  pointer-events: none;
  position: absolute;
  width: 0;
  min-width: 0;
  overflow: hidden;
  white-space: nowrap;
}

.desktop-sidebar--compact .desktop-sidebar__inner {
  padding-right: 12px;
  padding-left: 12px;
}

.desktop-sidebar--compact .desktop-nav__link {
  position: relative;
  justify-content: center;
  gap: 0;
  padding-inline: 0;
}

.desktop-sidebar--hidden {
  width: 0 !important;
  min-width: 0 !important;
  border-right-color: transparent;
  overflow: visible;
}

.desktop-sidebar--hidden .desktop-sidebar__inner {
  padding: 0;
  overflow: visible;
}

.desktop-sidebar--hidden .desktop-nav {
  opacity: 0;
  pointer-events: none;
}

.desktop-main {
  min-width: 0;
  min-height: 0;
  padding: 24px;
  overflow: hidden;
}

.desktop-workspace {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  min-width: 0;
  min-height: 0;
  overflow: hidden;
}

@media (max-width: 960px) {
  .desktop-main {
    padding: 18px;
  }
}
</style>
