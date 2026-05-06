<script setup lang="ts">
/* global HTMLElement, MouseEvent */
import { Icon } from '@iconify/vue'
import { Moon, Sunny } from '@element-plus/icons-vue'
import { ElButton, ElIcon } from 'element-plus'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useThemeStore } from '../../shared/stores/theme'
import DesktopPalettePanel from './DesktopPalettePanel.vue'
import DesktopThemePanel from './DesktopThemePanel.vue'

const route = useRoute()
const theme = useThemeStore()
const showThemePanel = ref(false)
const showPalettePanel = ref(false)
const themeDropdownRef = ref<HTMLElement>()
const paletteDropdownRef = ref<HTMLElement>()

const currentTitle = computed(() => {
  const routeTitle = route.meta.title
  return typeof routeTitle === 'string' ? routeTitle : '工作区'
})

function adjustPanelPosition(wrapperEl?: HTMLElement) {
  if (!wrapperEl) {
    return
  }
  const panel = wrapperEl.querySelector('.custom-dropdown-panel') as HTMLElement | null
  if (!panel) {
    return
  }
  const wrapperRect = wrapperEl.getBoundingClientRect()
  const panelRect = panel.getBoundingClientRect()
  const viewportWidth = window.innerWidth
  const viewportHeight = window.innerHeight
  const gap = 8
  const panelOffset = 12
  let desiredLeft = wrapperRect.left + wrapperRect.width / 2 - panelRect.width / 2
  if (wrapperEl.classList.contains('theme-dropdown') || wrapperEl.classList.contains('palette-dropdown')) {
    desiredLeft = wrapperRect.right - panelRect.width
  }
  if (desiredLeft < gap) {
    desiredLeft = gap
  }
  if (desiredLeft + panelRect.width > viewportWidth - gap) {
    desiredLeft = viewportWidth - gap - panelRect.width
  }
  const relativeLeft = desiredLeft - wrapperRect.left
  const availableHeight = Math.max(0, viewportHeight - wrapperRect.bottom - panelOffset - gap)
  wrapperEl.style.setProperty('--panel-left', `${relativeLeft}px`)
  wrapperEl.style.setProperty('--panel-transform', 'none')
  wrapperEl.style.setProperty('--panel-max-height', `${availableHeight}px`)
  wrapperEl.style.setProperty('--panel-bridge-width', `${panelRect.width}px`)
}

function adjustOpenPanels() {
  if (showThemePanel.value) {
    adjustPanelPosition(themeDropdownRef.value)
  }
  if (showPalettePanel.value) {
    adjustPanelPosition(paletteDropdownRef.value)
  }
}

function closeAllDropdowns(event?: MouseEvent) {
  if (!event) {
    showThemePanel.value = false
    showPalettePanel.value = false
    return
  }
  const path = event.composedPath ? event.composedPath() : []
  const insideTheme = themeDropdownRef.value && path.includes(themeDropdownRef.value)
  const insidePalette = paletteDropdownRef.value && path.includes(paletteDropdownRef.value)
  if (!insideTheme) {
    showThemePanel.value = false
  }
  if (!insidePalette) {
    showPalettePanel.value = false
  }
}

watch(showThemePanel, async (value) => {
  if (!value) {
    return
  }
  await nextTick()
  adjustPanelPosition(themeDropdownRef.value)
})

watch(showPalettePanel, async (value) => {
  if (!value) {
    return
  }
  await nextTick()
  adjustPanelPosition(paletteDropdownRef.value)
})

onMounted(() => {
  document.addEventListener('click', closeAllDropdowns)
  window.addEventListener('resize', adjustOpenPanels)
  window.addEventListener('scroll', adjustOpenPanels, { passive: true })
})

onBeforeUnmount(() => {
  document.removeEventListener('click', closeAllDropdowns)
  window.removeEventListener('resize', adjustOpenPanels)
  window.removeEventListener('scroll', adjustOpenPanels)
})
</script>

<template>
  <header class="desktop-topbar">
    <div class="desktop-topbar__tabs" role="tablist" aria-label="页面标签">
      <button
        class="desktop-topbar__tab desktop-topbar__tab--active"
        type="button"
        role="tab"
        aria-selected="true"
      >
        <span class="desktop-topbar__tab-label">{{ currentTitle }}</span>
      </button>
      <div class="desktop-topbar__tab-rail" aria-hidden="true" />
    </div>

    <div class="desktop-topbar__actions">
      <div
        ref="paletteDropdownRef"
        class="dropdown-wrapper palette-dropdown"
        @mouseenter="showPalettePanel = true"
        @mouseleave="showPalettePanel = false"
      >
        <ElButton class="palette-btn header-btn" @click.stop="showPalettePanel = !showPalettePanel">
          <Icon icon="material-symbols:palette-outline" class="palette-icon" />
        </ElButton>
        <Transition name="dropdown">
          <div v-if="showPalettePanel" class="custom-dropdown-panel palette-panel">
            <DesktopPalettePanel />
          </div>
        </Transition>
      </div>

      <div
        ref="themeDropdownRef"
        class="dropdown-wrapper theme-dropdown"
        @mouseenter="showThemePanel = true"
        @mouseleave="showThemePanel = false"
      >
        <ElButton class="theme-btn header-btn" @click="theme.setMode(theme.isDark ? 'light' : 'dark')">
          <ElIcon :size="18">
            <Moon v-if="theme.isDark" />
            <Sunny v-else />
          </ElIcon>
        </ElButton>
        <Transition name="dropdown">
          <div v-if="showThemePanel" class="custom-dropdown-panel">
            <DesktopThemePanel />
          </div>
        </Transition>
      </div>
    </div>
  </header>
</template>

<style scoped>
.desktop-topbar {
  --header-accent: var(--el-color-primary);
  --header-accent-soft: var(--el-color-primary-light-3);
  --header-accent-bright: var(--el-color-primary-light-5);
  --header-accent-surface: color-mix(in srgb, var(--el-color-primary) 12%, white);
  --header-accent-surface-hover: color-mix(in srgb, var(--el-color-primary) 18%, white);
  --header-accent-surface-dark: color-mix(in srgb, var(--el-color-primary-light-5) 18%, #0f172a);
  --header-accent-surface-dark-hover: color-mix(in srgb, var(--el-color-primary-light-5) 24%, #0f172a);
  --header-accent-overlay-12: color-mix(in srgb, var(--el-color-primary) 12%, transparent);
  --header-accent-overlay-15: color-mix(in srgb, var(--el-color-primary-light-5) 15%, transparent);
  --header-accent-overlay-18: color-mix(in srgb, var(--el-color-primary) 18%, transparent);
  --header-accent-overlay-22: color-mix(in srgb, var(--el-color-primary-light-5) 22%, transparent);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  min-height: 34px;
  padding: 0;
  border-bottom: 1px solid var(--desktop-border);
  background: color-mix(in srgb, var(--desktop-panel) 96%, transparent);
  backdrop-filter: blur(16px) saturate(180%);
}

.desktop-topbar__tabs {
  position: relative;
  display: flex;
  align-items: stretch;
  min-width: 0;
  height: 34px;
}

.desktop-topbar__tab {
  position: relative;
  display: inline-flex;
  align-items: center;
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

.desktop-topbar__tab::before {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  left: 0;
  height: 2px;
  background: transparent;
  transition: background-color 0.2s ease;
}

.desktop-topbar__tab--active {
  color: var(--desktop-text);
  background: color-mix(in srgb, var(--desktop-panel) 94%, var(--desktop-accent) 6%);
  box-shadow:
    inset 0 -1px 0 color-mix(in srgb, var(--desktop-panel) 96%, transparent),
    inset -1px 0 0 color-mix(in srgb, var(--desktop-border) 82%, transparent);
}

.desktop-topbar__tab--active::before {
  background: var(--desktop-accent);
}

.desktop-topbar__tab-label {
  display: inline-block;
  overflow: hidden;
  max-width: 180px;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 12px;
  font-weight: 600;
  line-height: 1;
}

.desktop-topbar__tab-rail {
  position: absolute;
  right: 0;
  bottom: 0;
  left: 0;
  height: 1px;
  background: var(--desktop-border);
  pointer-events: none;
}

.desktop-topbar__actions {
  display: flex;
  align-items: center;
  gap: 4px;
  flex: 0 0 auto;
  height: 100%;
  padding: 0 6px;
}

.header-btn {
  position: relative;
  z-index: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  padding: 0;
  border: none;
  border-radius: 6px;
  color: rgba(0, 0, 0, 0.7);
  background: transparent;
  cursor: pointer;
  overflow: hidden;
  outline: none;
  transition: color 0.2s ease-out;
}

.header-btn::before {
  content: '';
  position: absolute;
  inset: 0;
  z-index: -1;
  border-radius: inherit;
  opacity: 0;
  transform: scale(0.85);
  background: rgba(0, 0, 0, 0.06);
  transition: all 0.2s ease-out;
}

.header-btn:hover::before {
  opacity: 1;
  transform: scale(1);
}

.header-btn:active::before {
  background: rgba(0, 0, 0, 0.1);
}

.theme-btn:hover,
.palette-btn:hover {
  color: var(--header-accent);
}

.theme-btn:hover::before,
.palette-btn:hover::before {
  opacity: 1;
  transform: scale(1);
  background: var(--header-accent-overlay-12);
}

.theme-btn:active::before,
.palette-btn:active::before {
  background: var(--header-accent-overlay-18);
}

.palette-icon {
  width: 16px;
  height: 16px;
}

.dropdown-wrapper {
  position: relative;
}

.dropdown-wrapper:hover::after,
.dropdown-wrapper:focus-within::after {
  content: '';
  position: absolute;
  top: 100%;
  left: var(--panel-left, 50%);
  width: var(--panel-bridge-width, 100%);
  height: 12px;
  transform: var(--panel-transform, translateX(-50%));
}

.custom-dropdown-panel {
  position: absolute;
  top: calc(100% + 12px);
  left: var(--panel-left, 50%);
  right: var(--panel-right, auto);
  transform: var(--panel-transform, translateX(-50%));
  min-width: 160px;
  max-width: calc(100vw - 24px);
  max-height: var(--panel-max-height, calc(100dvh - 92px));
  padding: 8px;
  box-sizing: border-box;
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 14px;
  background-color: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(16px) saturate(180%);
  -webkit-backdrop-filter: blur(16px) saturate(180%);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.12);
  overflow-x: hidden;
  overflow-y: auto;
  overscroll-behavior: contain;
  z-index: 200;
}

.custom-dropdown-panel.palette-panel {
  width: min(360px, calc(100vw - 24px));
  padding: 20px;
}

.theme-dropdown:hover::after,
.theme-dropdown:focus-within::after,
.palette-dropdown:hover::after,
.palette-dropdown:focus-within::after {
  left: auto;
  right: 0;
  transform: none;
}

.theme-dropdown .custom-dropdown-panel,
.palette-dropdown .custom-dropdown-panel {
  left: auto;
  right: 0;
  transform: none;
}

.dropdown-enter-active,
.dropdown-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translate3d(0, -6px, 0);
}

.dark .header-btn {
  color: rgba(255, 255, 255, 0.8);
}

.dark .header-btn::before {
  background: rgba(255, 255, 255, 0.1);
}

.dark .header-btn:active::before {
  background: rgba(255, 255, 255, 0.15);
}

.dark .theme-btn:hover,
.dark .palette-btn:hover {
  color: var(--header-accent-bright);
}

.dark .theme-btn:hover::before,
.dark .palette-btn:hover::before {
  background: var(--header-accent-overlay-15);
}

.dark .theme-btn:active::before,
.dark .palette-btn:active::before {
  background: var(--header-accent-overlay-22);
}

.dark .custom-dropdown-panel {
  background-color: rgba(30, 41, 59, 0.88);
  border-color: rgba(255, 255, 255, 0.08);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.35);
}

@media (max-width: 960px) {
  .desktop-topbar__tab {
    max-width: 180px;
    padding: 0 10px;
  }

  .desktop-topbar__actions {
    padding: 0 4px;
  }
}
</style>
