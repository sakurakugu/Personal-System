<script setup lang="ts">
import { Icon } from '@iconify/vue'
import { CloseBold, Moon, Sunny } from '@element-plus/icons-vue'
import { ElButton, ElIcon } from 'element-plus'
import { onMounted, onUnmounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useDropdownPanels } from '@personal-system/ui'
import { useThemeStore } from '../../shared/stores/theme'
import { desktopTopNavItems, isDesktopTopNavItemActive } from '../navigation'
import {
  closeCurrentWindow,
  closeDesktopWidgetWindow,
  getCurrentWindowState,
  minimizeCurrentWindow,
  onCurrentWindowStateChange,
  openDesktopWidgetWindow,
  toggleMaximizeCurrentWindow,
} from '@/shared/window-manager'
import DesktopPalettePanel from './DesktopPalettePanel.vue'
import DesktopRouteLink from './DesktopRouteLink.vue'
import DesktopThemePanel from './DesktopThemePanel.vue'

const theme = useThemeStore()
const route = useRoute()
const showThemePanel = ref(false)
const showPalettePanel = ref(false)
const themeDropdownRef = ref<globalThis.HTMLElement>()
const paletteDropdownRef = ref<globalThis.HTMLElement>()
const isMaximized = ref(false)
let removeWindowStateListener = () => {}

async function handleOpenWidgetWindow() {
  try {
    await openDesktopWidgetWindow()
  } catch (error) {
    console.error('打开桌面小工具失败', error)
  }
}

async function handleCloseWidgetWindow() {
  try {
    await closeDesktopWidgetWindow()
  } catch (error) {
    console.error('关闭桌面小工具失败', error)
  }
}

async function handleMinimizeWindow() {
  try {
    await minimizeCurrentWindow()
  } catch (error) {
    console.error('最小化窗口失败', error)
  }
}

async function handleToggleMaximizeWindow() {
  try {
    const state = await toggleMaximizeCurrentWindow()
    isMaximized.value = state.maximized
  } catch (error) {
    console.error('切换窗口最大化状态失败', error)
  }
}

async function handleCloseWindow() {
  try {
    await closeCurrentWindow()
  } catch (error) {
    console.error('关闭窗口失败', error)
  }
}

onMounted(async () => {
  removeWindowStateListener = onCurrentWindowStateChange((payload) => {
    isMaximized.value = payload.maximized
  })

  try {
    const state = await getCurrentWindowState()
    isMaximized.value = state.maximized
  } catch (error) {
    console.error('读取窗口状态失败', error)
  }
})

onUnmounted(() => {
  removeWindowStateListener()
})

useDropdownPanels(
  [
    { isOpen: showThemePanel, wrapperRef: themeDropdownRef },
    { isOpen: showPalettePanel, wrapperRef: paletteDropdownRef },
  ],
  {
    panelOffset: 12,
    listenScroll: true,
  },
)
</script>

<template>
  <header class="desktop-header">
    <div class="desktop-header__brand">
      <div class="desktop-header__logo">PS</div>
      <strong>Personal System</strong>
    </div>

    <nav class="desktop-header__nav" aria-label="顶栏导航">
      <DesktopRouteLink
        v-for="item in desktopTopNavItems"
        :key="item.to"
        :to="item.to"
        :active="isDesktopTopNavItemActive(route.path, item)"
        active-class="desktop-header__nav-link--active"
        class="desktop-header__nav-link"
      >
        <component :is="item.icon" class="desktop-header__nav-icon" aria-hidden="true" />
        <span>{{ item.label }}</span>
      </DesktopRouteLink>
    </nav>

    <div class="desktop-header__actions">
      <ElButton class="header-btn" title="打开小工具" @click="handleOpenWidgetWindow">
        <Icon icon="material-symbols:widgets-outline-rounded" class="palette-icon" />
      </ElButton>
      <ElButton class="header-btn" title="关闭小工具" @click="handleCloseWidgetWindow">
        <ElIcon :size="18">
          <CloseBold />
        </ElIcon>
      </ElButton>
      <div
        ref="paletteDropdownRef"
        class="dropdown-wrapper dropdown-wrapper--align-end palette-dropdown"
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
        class="dropdown-wrapper dropdown-wrapper--align-end theme-dropdown"
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

      <div class="desktop-header__window-actions">
        <button type="button" class="window-control-btn" title="最小化" @click="handleMinimizeWindow">
          <Icon icon="codicon:chrome-minimize" class="window-control-icon" aria-hidden="true" />
        </button>
        <button
          type="button"
          class="window-control-btn"
          :title="isMaximized ? '还原' : '最大化'"
          @click="handleToggleMaximizeWindow"
        >
          <Icon
            :icon="isMaximized ? 'codicon:chrome-restore' : 'codicon:chrome-maximize'"
            class="window-control-icon"
            aria-hidden="true"
          />
        </button>
        <button
          type="button"
          class="window-control-btn window-control-btn--danger"
          title="关闭"
          @click="handleCloseWindow"
        >
          <Icon icon="codicon:chrome-close" class="window-control-icon" aria-hidden="true" />
        </button>
      </div>
    </div>
  </header>
</template>

<style scoped>
@import '@personal-system/ui/styles/dropdown.css';

.desktop-header {
  --header-accent: var(--el-color-primary);
  --header-accent-bright: var(--el-color-primary-light-5);
  --header-accent-overlay-12: color-mix(in srgb, var(--el-color-primary) 12%, transparent);
  --header-accent-overlay-15: color-mix(in srgb, var(--el-color-primary-light-5) 15%, transparent);
  --header-accent-overlay-18: color-mix(in srgb, var(--el-color-primary) 18%, transparent);
  --header-accent-overlay-22: color-mix(in srgb, var(--el-color-primary-light-5) 22%, transparent);
  --dropdown-panel-offset: 12px;
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 18px;
  border-bottom: 1px solid var(--desktop-border);
  background: color-mix(in srgb, var(--desktop-panel) 96%, transparent);
  backdrop-filter: blur(16px) saturate(180%);
  -webkit-app-region: drag;
}

.desktop-header__brand {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
  color: var(--desktop-text);
  -webkit-app-region: no-drag;
}

.desktop-header__nav {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
  margin-right: 8px;
  -webkit-app-region: no-drag;
}

.desktop-header__nav-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 36px;
  padding: 0 12px;
  border-radius: 10px;
  color: color-mix(in srgb, var(--desktop-text) 80%, transparent);
  text-decoration: none;
  transition:
    color 0.2s ease,
    background-color 0.2s ease;
}

.desktop-header__nav-link:hover {
  color: var(--desktop-text);
  background: color-mix(in srgb, var(--desktop-panel) 88%, var(--desktop-accent) 12%);
}

.desktop-header__nav-link--active {
  color: var(--desktop-accent);
  background: color-mix(in srgb, var(--desktop-panel) 84%, var(--desktop-accent) 16%);
}

.desktop-header__nav-icon {
  width: 14px;
  height: 14px;
}

.desktop-header__brand strong {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.desktop-header__logo {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  border-radius: 12px;
  color: #fff;
  background: var(--desktop-accent);
  flex: 0 0 auto;
}

.desktop-header__actions {
  display: flex;
  align-items: center;
  gap: 4px;
  flex: 0 0 auto;
  margin-left: auto;
  -webkit-app-region: no-drag;
}

.header-btn {
  position: relative;
  z-index: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  padding: 0;
  border: none;
  border-radius: 10px;
  color: rgba(0, 0, 0, 0.7);
  background: transparent;
  cursor: pointer;
  overflow: hidden;
  outline: none;
  transition: color 0.2s ease-out;
}

.desktop-header__window-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-left: 6px;
  padding-left: 10px;
  border-left: 1px solid color-mix(in srgb, var(--desktop-border) 82%, transparent);
}

.window-control-btn {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  padding: 0;
  border: none;
  border-radius: 10px;
  color: rgba(0, 0, 0, 0.7);
  background: transparent;
  cursor: pointer;
  transition:
    background-color 0.2s ease,
    color 0.2s ease;
}

.window-control-icon {
  width: 14px;
  height: 14px;
}

.window-control-btn:hover {
  color: var(--desktop-text);
  background: rgba(0, 0, 0, 0.08);
}

.window-control-btn:active {
  background: rgba(0, 0, 0, 0.12);
}

.window-control-btn--danger:hover {
  color: #fff;
  background: #e5484d;
}

.window-control-btn--danger:active {
  background: #cc3d43;
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
  width: 20px;
  height: 20px;
}

.custom-dropdown-panel.palette-panel {
  width: min(360px, calc(100vw - 24px));
  padding: 20px;
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

.dark .window-control-btn {
  color: rgba(255, 255, 255, 0.82);
}

.dark .window-control-btn:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.12);
}

.dark .window-control-btn:active {
  background: rgba(255, 255, 255, 0.18);
}

.dark .window-control-btn--danger:hover {
  background: #e5484d;
}

.dark .window-control-btn--danger:active {
  background: #cc3d43;
}

@media (max-width: 960px) {
  .desktop-header {
    flex-wrap: wrap;
    padding: 10px 16px;
  }

  .desktop-header__brand strong {
    font-size: 14px;
  }

  .desktop-header__nav {
    order: 3;
    width: 100%;
    margin: 0;
  }

  .desktop-header__actions {
    margin-left: auto;
  }
}
</style>
