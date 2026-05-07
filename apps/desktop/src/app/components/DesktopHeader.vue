<script setup lang="ts">
import { Icon } from '@iconify/vue'
import { Moon, Sunny } from '@element-plus/icons-vue'
import { ElButton, ElIcon } from 'element-plus'
import { ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { useDropdownPanels } from '@personal-system/ui'
import { useThemeStore } from '../../shared/stores/theme'
import { desktopTopNavItems, isDesktopTopNavItemActive } from '../navigation'
import DesktopPalettePanel from './DesktopPalettePanel.vue'
import DesktopThemePanel from './DesktopThemePanel.vue'

const theme = useThemeStore()
const route = useRoute()
const router = useRouter()
const showThemePanel = ref(false)
const showPalettePanel = ref(false)
const themeDropdownRef = ref<globalThis.HTMLElement>()
const paletteDropdownRef = ref<globalThis.HTMLElement>()

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

function handleTopNavClick(event: globalThis.MouseEvent, to: string) {
  event.preventDefault()
  void router.push(to)
}
</script>

<template>
  <header class="desktop-header">
    <div class="desktop-header__brand">
      <div class="desktop-header__logo">PS</div>
      <strong>Personal System</strong>
    </div>

    <nav class="desktop-header__nav" aria-label="顶栏导航">
      <RouterLink
        v-for="item in desktopTopNavItems"
        :key="item.to"
        :to="item.to"
        class="desktop-header__nav-link"
        :class="{ 'desktop-header__nav-link--active': isDesktopTopNavItemActive(route.path, item) }"
        @click="handleTopNavClick($event, item.to)"
      >
        <component :is="item.icon" class="desktop-header__nav-icon" aria-hidden="true" />
        <span>{{ item.label }}</span>
      </RouterLink>
    </nav>

    <div class="desktop-header__actions">
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
}

.desktop-header__brand {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
  color: var(--desktop-text);
}

.desktop-header__nav {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
  margin-right: 8px;
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
