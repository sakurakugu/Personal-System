<script setup lang="ts">
import { Icon } from '@iconify/vue'
import { Moon, Sunny } from '@element-plus/icons-vue'
import { ElButton, ElIcon, ElInput } from 'element-plus'
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { 使用下拉面板 } from '@personal-system/ui'
import { 使用桌面小工具窗口 } from '../../shared/composables/使用桌面小工具窗口'
import { 使用主题存储 } from '../../shared/stores/theme'
import { desktopTopNavItems, 桌面顶栏导航项是否激活 } from '../navigation'
import {
  关闭当前窗口,
  获取当前窗口状态,
  最小化当前窗口,
  监听当前窗口状态变更,
  切换最大化当前窗口,
} from '@/shared/window-manager'
import DesktopPalettePanel from './桌面调色板.vue'
import DesktopRouteLink from './桌面路由链接.vue'
import DesktopThemePanel from './桌面主题面板.vue'

const theme = 使用主题存储()
const route = useRoute()
const router = useRouter()
const showThemePanel = ref(false)
const showPalettePanel = ref(false)
const themeDropdownRef = ref<globalThis.HTMLElement>()
const paletteDropdownRef = ref<globalThis.HTMLElement>()
const isMaximized = ref(false)
const desktopSearch = ref('')
type InputInstance = InstanceType<typeof ElInput>
const searchInputRef = ref<InputInstance | null>(null)
const 搜索框已激活 = ref(false)
let 搜索防抖定时器: number | null = null
let 忽略下一次搜索监听 = false
let removeWindowStateListener = () => {}
const { isDesktopWidgetWindowOpen, toggleDesktopWidgetWindow } = 使用桌面小工具窗口()

const isBlogHomeContext = computed(() => (
  route.path === '/home'
  || route.path === '/home/archive'
  || route.path === '/home/announcements'
  || route.path.startsWith('/home/blog/')
  || route.path.startsWith('/home/moments/')
))

function 获取搜索原生输入框() {
  return searchInputRef.value?.input ?? null
}

function 获取路由搜索词() {
  return typeof route.query.search === 'string' ? route.query.search : ''
}

function 同步搜索框属性() {
  const input = 获取搜索原生输入框()
  if (!input) return
  input.type = 'search'
  input.name = 'desktop-site-search'
  input.autocomplete = 'off'
  input.spellcheck = false
  input.readOnly = !搜索框已激活.value
  input.setAttribute('autocapitalize', 'off')
  input.setAttribute('autocorrect', 'off')
  input.setAttribute('enterkeyhint', 'search')
  input.setAttribute('data-form-type', 'other')
}

function 激活搜索框() {
  搜索框已激活.value = true
  同步搜索框属性()
}

function 重置搜索框防自动填充() {
  const input = 获取搜索原生输入框()
  if (!input || document.activeElement === input || desktopSearch.value.trim()) return
  搜索框已激活.value = false
  同步搜索框属性()
}

function 清理搜索防抖定时器() {
  if (搜索防抖定时器 !== null) {
    window.clearTimeout(搜索防抖定时器)
    搜索防抖定时器 = null
  }
}

function 同步路由搜索词到输入框() {
  const 路由搜索词 = 获取路由搜索词()
  if (desktopSearch.value === 路由搜索词) return
  忽略下一次搜索监听 = true
  desktopSearch.value = 路由搜索词
}

async function handleDesktopSearch(replace = false) {
  清理搜索防抖定时器()
  const keyword = desktopSearch.value.trim()
  const target = {
    path: '/home',
    query: keyword ? { search: keyword } : undefined,
  }
  const targetFullPath = router.resolve(target).fullPath

  if (targetFullPath === route.fullPath) {
    return
  }

  if (replace || route.path === '/home' || route.path === '/home/archive' || route.path === '/home/announcements') {
    await router.replace(target)
    return
  }

  await router.push(target)
}

async function handleToggleWidgetWindow() {
  try {
    await toggleDesktopWidgetWindow()
  } catch (error) {
    console.error('切换桌面小工具失败', error)
  }
}

async function handleMinimizeWindow() {
  try {
    await 最小化当前窗口()
  } catch (error) {
    console.error('最小化窗口失败', error)
  }
}

async function handleToggleMaximizeWindow() {
  try {
    const state = await 切换最大化当前窗口()
    isMaximized.value = state.maximized
  } catch (error) {
    console.error('切换窗口最大化状态失败', error)
  }
}

async function handleCloseWindow() {
  try {
    await 关闭当前窗口()
  } catch (error) {
    console.error('关闭窗口失败', error)
  }
}

onMounted(async () => {
  removeWindowStateListener = 监听当前窗口状态变更((payload) => {
    isMaximized.value = payload.maximized
  })

  try {
    const state = await 获取当前窗口状态()
    isMaximized.value = state.maximized
  } catch (error) {
    console.error('读取窗口状态失败', error)
  }

  void nextTick().then(() => {
    同步搜索框属性()
    同步路由搜索词到输入框()
  })
})

onUnmounted(() => {
  清理搜索防抖定时器()
  removeWindowStateListener()
})

watch(
  () => route.fullPath,
  async () => {
    await nextTick()
    同步搜索框属性()
    重置搜索框防自动填充()
  },
)

watch(
  () => 获取路由搜索词(),
  () => {
    同步路由搜索词到输入框()
  },
  { immediate: true },
)

watch(desktopSearch, (value, oldValue) => {
  if (忽略下一次搜索监听) {
    忽略下一次搜索监听 = false
    return
  }
  if (value.trim() === oldValue.trim()) return
  清理搜索防抖定时器()
  搜索防抖定时器 = window.setTimeout(() => {
    void handleDesktopSearch(route.path === '/home' || route.path === '/home/archive' || route.path === '/home/announcements')
  }, 250)
})

使用下拉面板(
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
    <div class="desktop-header__left">
      <div class="desktop-header__brand">
        <div class="desktop-header__logo">PS</div>
        <strong>Personal System</strong>
      </div>

      <nav class="desktop-header__nav" aria-label="顶栏导航">
        <DesktopRouteLink
          v-for="item in desktopTopNavItems"
          :key="item.to"
          :to="item.to"
          :active="桌面顶栏导航项是否激活(route.path, item)"
          active-class="desktop-header__nav-link--active"
          class="desktop-header__nav-link"
        >
          <component :is="item.icon" class="desktop-header__nav-icon" aria-hidden="true" />
          <span>{{ item.label }}</span>
        </DesktopRouteLink>
      </nav>
    </div>

    <div class="desktop-header__center">
      <div v-if="isBlogHomeContext" class="desktop-header__search" data-form-type="other">
        <input
          class="search-autofill-decoy"
          type="text"
          name="username"
          autocomplete="username"
          tabindex="-1"
          aria-hidden="true"
        >
        <input
          class="search-autofill-decoy"
          type="password"
          name="password"
          autocomplete="current-password"
          tabindex="-1"
          aria-hidden="true"
        >
        <ElInput
          ref="searchInputRef"
          v-model="desktopSearch"
          type="search"
          clearable
          placeholder="搜索文章..."
          name="desktop-site-search"
          autocomplete="off"
          spellcheck="false"
          autocapitalize="off"
          autocorrect="off"
          @focus="激活搜索框"
          @pointerdown.capture="激活搜索框"
          @blur="重置搜索框防自动填充"
          @clear="handleDesktopSearch(route.path === '/home' || route.path === '/home/archive' || route.path === '/home/announcements')"
          @keyup.enter="handleDesktopSearch(route.path === '/home' || route.path === '/home/archive' || route.path === '/home/announcements')"
        >
          <template #suffix>
            <ElIcon class="desktop-header__search-icon" @click="handleDesktopSearch(route.path === '/home' || route.path === '/home/archive' || route.path === '/home/announcements')">
              <Icon icon="material-symbols:search-rounded" />
            </ElIcon>
          </template>
        </ElInput>
      </div>
    </div>

    <div class="desktop-header__actions">
      <ElButton
        class="header-btn"
        :title="isDesktopWidgetWindowOpen ? '关闭小工具' : '打开小工具'"
        @click="handleToggleWidgetWindow"
      >
        <Icon
          :icon="isDesktopWidgetWindowOpen ? 'mingcute:miniplayer-fill' : 'mingcute:miniplayer-line'"
          class="palette-icon"
        />
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
  position: relative;
  display: flex;
  align-items: center;
  gap: 16px;
  min-height: 64px;
  box-sizing: border-box;
  padding: 12px 18px;
  border-bottom: 1px solid var(--desktop-border);
  background: color-mix(in srgb, var(--desktop-panel) 96%, transparent);
  backdrop-filter: blur(16px) saturate(180%);
  -webkit-app-region: drag;
}

.desktop-header__left {
  display: flex;
  align-items: center;
  flex: 0 0 auto;
  gap: 16px;
  min-width: max-content;
}

.desktop-header__brand {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
  color: var(--desktop-text);
  -webkit-app-region: no-drag;
}

.desktop-header__center {
  position: absolute;
  top: 50%;
  left: 50%;
  display: flex;
  justify-content: center;
  width: min(260px, calc(100% - 40px));
  transform: translate(-50%, -50%);
  z-index: 1;
}

.desktop-header__nav {
  display: inline-flex;
  align-items: center;
  flex-wrap: nowrap;
  gap: 6px;
  min-width: 0;
  margin-right: 8px;
  -webkit-app-region: no-drag;
}

.desktop-header__search {
  min-width: 220px;
  max-width: 260px;
  width: 100%;
  -webkit-app-region: no-drag;
}

.search-autofill-decoy {
  position: absolute;
  top: 0;
  left: 0;
  width: 1px;
  height: 1px;
  padding: 0;
  border: 0;
  opacity: 0;
  pointer-events: none;
  transform: translateY(-200vh);
}

.desktop-header__search :deep(.el-input) {
  width: 260px;
}

.desktop-header__search :deep(.el-input__wrapper) {
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.03);
  box-shadow: none !important;
  border: 1px solid transparent;
  transition: all 0.2s ease-out;
}

.desktop-header__search :deep(.el-input__wrapper:hover) {
  background: rgba(0, 0, 0, 0.05);
}

.desktop-header__search :deep(.el-input__wrapper.is-focus) {
  background: rgba(0, 0, 0, 0.06);
  border-color: color-mix(in srgb, var(--header-accent) 16%, transparent);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05) !important;
}

.desktop-header__search :deep(input[type='search']::-webkit-search-cancel-button) {
  -webkit-appearance: none;
  appearance: none;
  display: none;
}

.desktop-header__search :deep(input[type='search']::-ms-clear) {
  display: none;
}

.desktop-header__search-icon {
  cursor: pointer;
  color: rgba(0, 0, 0, 0.45);
  transition: color 0.2s;
}

.desktop-header__search-icon:hover {
  color: var(--header-accent);
}

.desktop-header__nav-link {
  display: inline-flex;
  align-items: center;
  flex-shrink: 0;
  gap: 6px;
  min-height: 36px;
  padding: 0 12px;
  border-radius: 10px;
  color: color-mix(in srgb, var(--desktop-text) 80%, transparent);
  text-decoration: none;
  white-space: nowrap;
  transition:
    color 0.2s ease,
    background-color 0.2s ease;
}

.desktop-header__nav-link span {
  white-space: nowrap;
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
  margin-left: auto;
  gap: 4px;
  flex: 0 0 auto;
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

.dark .desktop-header__search :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.05) !important;
  box-shadow: none !important;
  border-color: transparent !important;
}

.dark .desktop-header__search :deep(.el-input__wrapper:hover) {
  background: rgba(255, 255, 255, 0.08) !important;
}

.dark .desktop-header__search :deep(.el-input__wrapper.is-focus) {
  background: rgba(255, 255, 255, 0.09) !important;
  border-color: color-mix(in srgb, var(--header-accent-bright) 24%, transparent) !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.22) !important;
}

.dark .desktop-header__search-icon {
  color: rgba(255, 255, 255, 0.5);
}

.dark .desktop-header__search-icon:hover {
  color: var(--header-accent-bright);
}

@media (max-width: 1080px) {
  .desktop-header__brand strong {
    display: none;
  }
}

@media (max-width: 960px) {
  .desktop-header {
    gap: 10px;
    padding: 10px 16px;
  }

  .desktop-header__search {
    width: 100%;
    min-width: 0;
    max-width: 200px;
  }

  .desktop-header__search :deep(.el-input) {
    width: 100%;
    min-width: 0;
  }
}

@media (max-width: 820px) {
  .desktop-header {
    gap: 8px;
    padding: 10px 12px;
  }

  .desktop-header__search {
    max-width: 168px;
  }
}

@media (max-width: 720px) {
  .desktop-header__window-actions {
    gap: 4px;
    margin-left: 4px;
    padding-left: 8px;
  }
}
</style>
