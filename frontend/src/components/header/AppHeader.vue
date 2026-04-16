<script setup lang="ts">
/* global HTMLElement, MouseEvent */
import { Icon } from '@iconify/vue'
import { Checked, Connection, Document, HomeFilled, House, Monitor, Moon, Plus, Search, Setting, Sunny, SwitchButton, User } from '@element-plus/icons-vue'
import { ElButton, ElDropdown, ElDropdownItem, ElDropdownMenu, ElIcon, ElInput } from 'element-plus'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import type { Component } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useViewport } from '../../composables/useViewport'
import { useAuthStore } from '../../stores/auth'
import { useBlogAppearanceStore } from '../../stores/blog-appearance'
import { useSettingsStore } from '../../stores/settings'
import { useThemeStore } from '../../stores/theme'
import { isApiEnvironmentSwitchEnabled } from '../../utils/runtime'
import ApiEnvironmentDialog from '../ApiEnvironmentDialog.vue'
import HeaderPalettePanel from './HeaderPalettePanel.vue'
import HeaderThemePanel from './HeaderThemePanel.vue'
import HeaderUserDropdown from './HeaderUserDropdown.vue'

const emit = defineEmits<{ 'show-login': [tab?: 'login' | 'register'] }>()
const auth = useAuthStore()
const settings = useSettingsStore()
const theme = useThemeStore()
const blogAppearance = useBlogAppearanceStore()
const router = useRouter()
const route = useRoute()
const showApiEnvironmentDialog = ref(false)

const showThemePanel = ref(false)
const showPlusPanel = ref(false)
const showPalettePanel = ref(false)

const themeDropdownRef = ref<HTMLElement>()
const plusDropdownRef = ref<HTMLElement>()
const paletteDropdownRef = ref<HTMLElement>()

function adjustPanelPosition(wrapperEl?: HTMLElement) {
  if (!wrapperEl) return
  const panel = wrapperEl.querySelector('.custom-dropdown-panel') as HTMLElement | null
  if (!panel) return
  const wrapperRect = wrapperEl.getBoundingClientRect()
  const panelRect = panel.getBoundingClientRect()
  const viewportWidth = window.innerWidth
  const viewportHeight = window.innerHeight
  const gap = 8
  const panelOffset = 20

  // 默认居中（相对于视口）
  let desiredLeft = wrapperRect.left + wrapperRect.width / 2 - panelRect.width / 2

  // 左边界检查
  if (desiredLeft < gap) {
    desiredLeft = gap
  }
  // 右边界检查
  if (desiredLeft + panelRect.width > viewportWidth - gap) {
    desiredLeft = viewportWidth - gap - panelRect.width
  }

  // 转换为相对于 wrapper 的 left
  const relativeLeft = desiredLeft - wrapperRect.left
  const availableHeight = Math.max(0, viewportHeight - wrapperRect.bottom - panelOffset - gap)
  wrapperEl.style.setProperty('--panel-left', `${relativeLeft}px`)
  wrapperEl.style.setProperty('--panel-transform', 'none')
  wrapperEl.style.setProperty('--panel-max-height', `${availableHeight}px`)
}

function adjustOpenPanels() {
  if (showThemePanel.value) adjustPanelPosition(themeDropdownRef.value)
  if (showPlusPanel.value) adjustPanelPosition(plusDropdownRef.value)
  if (showPalettePanel.value) adjustPanelPosition(paletteDropdownRef.value)
}

watch(showThemePanel, async (v) => {
  if (v) {
    await nextTick()
    adjustPanelPosition(themeDropdownRef.value)
  }
})

watch(showPlusPanel, async (v) => {
  if (v) {
    await nextTick()
    adjustPanelPosition(plusDropdownRef.value)
  }
})

watch(showPalettePanel, async (v) => {
  if (v) {
    await nextTick()
    adjustPanelPosition(paletteDropdownRef.value)
  }
})

function closeAllDropdowns(e?: MouseEvent) {
  if (!e) {
    showThemePanel.value = false
    showPlusPanel.value = false
    showPalettePanel.value = false
    return
  }
  const path = e.composedPath ? e.composedPath() : []
  const insideTheme = themeDropdownRef.value && path.includes(themeDropdownRef.value)
  const insidePlus = plusDropdownRef.value && path.includes(plusDropdownRef.value)
  const insidePalette = paletteDropdownRef.value && path.includes(paletteDropdownRef.value)
  if (!insideTheme) showThemePanel.value = false
  if (!insidePlus) showPlusPanel.value = false
  if (!insidePalette) showPalettePanel.value = false
}

const searchKeyword = ref('')
let searchDebounceTimer: number | null = null
const navLinks = [
  { label: '首页', to: '/blog' },
]

onMounted(() => {
  void settings.ensurePublicSettingsLoaded()
  document.addEventListener('click', closeAllDropdowns)
  window.addEventListener('resize', adjustOpenPanels)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', closeAllDropdowns)
  window.removeEventListener('resize', adjustOpenPanels)
  if (searchDebounceTimer !== null) {
    window.clearTimeout(searchDebounceTimer)
  }
})

// 执行搜索 - 跳转到博客首页
function doSearch() {
  const query: Record<string, string> = {}
  if (searchKeyword.value) query.search = searchKeyword.value
  router.push({ path: '/blog', query: Object.keys(query).length ? query : undefined })
}

watch(searchKeyword, () => {
  if (searchDebounceTimer !== null) {
    window.clearTimeout(searchDebounceTimer)
  }
  searchDebounceTimer = window.setTimeout(() => {
    doSearch()
  }, 300)
})

const isAuthed = computed(() => auth.isAuthenticated)
const displayName = computed(() => auth.user?.nickname || auth.user?.username || '')
const avatarText = computed(() => displayName.value.slice(0, 1).toUpperCase() || 'U')
const isDashboardPage = computed(() => route.path.startsWith('/dashboard'))
const { isMobileViewport } = useViewport()
const canShowApiEnvironmentEntry = isApiEnvironmentSwitchEnabled()
type UserMenuItem = { label: string; key: string; type?: 'divider'; icon?: Component }

const menuOptions = computed<UserMenuItem[]>(() => {
  const items: UserMenuItem[] = [
    { label: '个人资料', key: 'profile', icon: User },
    { label: '用户设置', key: 'user-settings', icon: Setting },
    { label: '个人看板', key: 'dashboard', icon: House },
    { label: '我的文章', key: 'articles', icon: Document },
    { label: '我的待办', key: 'todos', icon: Checked },
  ]
  if (auth.isSuperAdmin) {
    items.push({ label: '系统状态', key: 'system', icon: Monitor })
  }
  if (auth.isAdmin) {
    items.push({ label: '用户管理', key: 'users', icon: User })
  }
  if (auth.isSuperAdmin) {
    items.push({ label: '系统设置', key: 'settings', icon: Setting })
  }
  items.push({ type: 'divider' as const, key: 'd1', label: '' })
  items.push({ label: '退出登录', key: 'logout', icon: SwitchButton })
  return items
})

async function handleMenu(key: string) {
  switch (key) {
    case 'profile': router.push('/dashboard/profile'); break
    case 'user-settings': router.push('/dashboard/user-settings'); break
    case 'dashboard': router.push('/dashboard'); break
    case 'articles': router.push('/dashboard/articles'); break
    case 'todos': router.push('/dashboard/todos'); break
    case 'system': router.push('/dashboard/system'); break
    case 'users': router.push('/dashboard/users'); break
    case 'settings': router.push('/dashboard/settings'); break
    case 'logout':
      await auth.logout()
      await router.push('/blog')
      break
  }
}

function handleGuestMenu(key: 'login' | 'register') {
  emit('show-login', key)
}

function handleMobileNav(path: string) {
  router.push(path)
}

const isHomePage = computed(() => route.path === '/blog' || route.path === '/')
const shouldUseTransparentHeader = computed(() => isHomePage.value && blogAppearance.wallpaperMode === 'banner')
const headerInnerClass = computed(() => {
  const transparentEnabled = shouldUseTransparentHeader.value
  const mode = blogAppearance.navbarTransparentMode

  return {
    'header-inner-transparent': transparentEnabled && mode === 'semi',
    'header-inner-transparent-full': transparentEnabled && mode === 'full',
    'header-inner-transparent-dynamic': transparentEnabled && mode === 'semifull' && !isScrolled.value,
    'header-inner-scrolled': transparentEnabled && mode === 'semifull' && isScrolled.value,
  }
})
const headerInnerStyle = computed(() => {
  const shouldUseBlogBlur = shouldUseTransparentHeader.value
  const blurEnabled = shouldUseBlogBlur ? blogAppearance.navbarBlurEnabled : true
  const blurValue = shouldUseBlogBlur ? blogAppearance.navbarBlur : 20
  const blurCss = blurEnabled ? `blur(${blurValue}px) saturate(180%)` : 'none'

  return {
    '--blog-navbar-backdrop': blurCss,
    '--blog-navbar-webkit-backdrop': blurCss,
  }
})

const isScrolled = ref(false)
function updateScroll() {
  isScrolled.value = window.scrollY > 10
}

onMounted(() => {
  updateScroll()
  window.addEventListener('scroll', updateScroll, { passive: true })
})

onBeforeUnmount(() => {
  window.removeEventListener('scroll', updateScroll)
})

function openApiEnvironmentDialog() {
  showApiEnvironmentDialog.value = true
}
</script>

<template>
  <div
    id="top-row"
    class="header-top-row"
    :class="{ 'dashboard-header': isDashboardPage }"
  >
    <div
      id="navbar-wrapper"
      class="header-navbar-wrapper"
      :class="{ 'sticky-navbar': !isDashboardPage }"
    >
      <header class="app-header" :class="{ 'dashboard-header': isDashboardPage }">
        <div
          class="header-inner"
          :class="[headerInnerClass, { 'dashboard-header-inner': isDashboardPage }]"
          :style="headerInnerStyle"
        >
          <!-- 左侧区域 -->
          <div class="header-left">
            <!-- 移动端左侧头像入口 -->
            <div v-if="isMobileViewport && !isDashboardPage" class="mobile-user-entry">
              <HeaderUserDropdown
                class="mobile-user-dropdown"
                :mobile="true"
                :is-authed="isAuthed"
                :avatar-url="auth.user?.avatar_url"
                :avatar-text="avatarText"
                :menu-items="menuOptions"
                :register-enabled="settings.registerEnabled"
                @menu-select="handleMenu"
                @guest-select="handleGuestMenu"
              />
            </div>
            <router-link to="/blog" class="logo logo-desktop">
              <ElIcon><HomeFilled /></ElIcon>
              <span>Sakurakuguの小窝</span>
            </router-link>
            <ElDropdown v-if="isDashboardPage" trigger="click" class="mobile-nav-dropdown" @command="handleMobileNav">
              <button type="button" class="header-btn mobile-home-trigger" aria-label="打开导航菜单">
                <ElIcon><HomeFilled /></ElIcon>
              </button>
              <template #dropdown>
                <ElDropdownMenu>
                  <ElDropdownItem
                    v-for="item in navLinks"
                    :key="item.to"
                    :command="item.to"
                  >
                    {{ item.label }}
                  </ElDropdownItem>
                </ElDropdownMenu>
              </template>
            </ElDropdown>
            <nav v-if="isDashboardPage" class="nav-links">
              <router-link
                v-for="item in navLinks"
                :key="item.to"
                :to="item.to"
              >
                {{ item.label }}
              </router-link>
            </nav>
          </div>

          <!-- 中间搜索框 -->
          <div class="header-search">
            <ElInput
              v-model="searchKeyword"
              placeholder="搜索文章..."
              clearable
              @keyup.enter="doSearch"
              @clear="doSearch"
            >
              <template #suffix>
                <ElIcon class="search-icon" @click="doSearch">
                  <Search />
                </ElIcon>
              </template>
            </ElInput>
          </div>

          <!-- 右侧功能区 -->
          <div class="header-right">
            <!-- 用户菜单 -->
            <HeaderUserDropdown
              v-if="!isMobileViewport"
              class="desktop-user-dropdown"
              :is-authed="isAuthed"
              :avatar-url="auth.user?.avatar_url"
              :avatar-text="avatarText"
              :menu-items="menuOptions"
              :register-enabled="settings.registerEnabled"
              @menu-select="handleMenu"
              @guest-select="handleGuestMenu"
            />

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
                <div v-show="showPalettePanel" class="custom-dropdown-panel palette-panel">
                  <HeaderPalettePanel />
                </div>
              </Transition>
            </div>

            <div ref="themeDropdownRef" class="dropdown-wrapper theme-dropdown desktop-theme-dropdown" @mouseenter="showThemePanel = true" @mouseleave="showThemePanel = false">
              <ElButton
                class="theme-btn header-btn"
                @click="theme.toggleTheme"
              >
                <ElIcon :size="20">
                  <Moon v-if="theme.isDark" />
                  <Sunny v-else />
                </ElIcon>
              </ElButton>
              <Transition name="dropdown">
                <div v-show="showThemePanel" class="custom-dropdown-panel">
                  <HeaderThemePanel />
                </div>
              </Transition>
            </div>

            <div
              ref="plusDropdownRef"
              class="dropdown-wrapper header-plus-dropdown"
              @mouseenter="showPlusPanel = true"
              @mouseleave="showPlusPanel = false"
            >
              <ElButton class="plus-btn header-btn">
                <ElIcon :size="20"><Plus /></ElIcon>
              </ElButton>
              <Transition name="dropdown">
                <div v-show="showPlusPanel" class="custom-dropdown-panel plus-dropdown-panel">
                  <div v-if="canShowApiEnvironmentEntry" class="dropdown-item" @click="openApiEnvironmentDialog(); showPlusPanel = false">
                    <span class="plus-menu-main"><ElIcon><Connection /></ElIcon><span>接口环境</span></span>
                  </div>
                  <div v-if="canShowApiEnvironmentEntry" class="custom-divider" role="separator" />
                  <HeaderPalettePanel />
                  <div class="custom-divider" role="separator" />
                  <HeaderThemePanel compact />
                </div>
              </Transition>
            </div>
          </div>
        </div>
      </header>
    </div>
  </div>
  <ApiEnvironmentDialog v-model="showApiEnvironmentDialog" />
</template>

<style scoped>
@import '../../styles/media.css';

/* ========== Firefly 风格导航栏 ========== */

.header-top-row {
  position: sticky;
  top: 0;
  z-index: 100;
  pointer-events: none;
  transition: all 0.36s cubic-bezier(0.22, 1, 0.36, 1);
  width: 100%;
  max-width: 1600px;
  margin: 0 auto;
  padding: 0 16px;
}

.header-top-row.dashboard-header {
  position: relative;
}

.header-navbar-wrapper {
  pointer-events: auto;
  transition: all 0.36s cubic-bezier(0.22, 1, 0.36, 1);
}

.app-header {
  --header-accent: var(--el-color-primary);
  --header-accent-strong: var(--el-color-primary-dark-2);
  --header-accent-soft: var(--el-color-primary-light-3);
  --header-accent-bright: var(--el-color-primary-light-5);
  --header-accent-surface: color-mix(in srgb, var(--el-color-primary) 12%, white);
  --header-accent-surface-hover: color-mix(in srgb, var(--el-color-primary) 18%, white);
  --header-accent-surface-dark: color-mix(in srgb, var(--el-color-primary-light-5) 18%, #0f172a);
  --header-accent-surface-dark-hover: color-mix(in srgb, var(--el-color-primary-light-5) 24%, #0f172a);
  --header-accent-overlay-08: color-mix(in srgb, var(--el-color-primary) 8%, transparent);
  --header-accent-overlay-10: color-mix(in srgb, var(--el-color-primary-light-5) 10%, transparent);
  --header-accent-overlay-12: color-mix(in srgb, var(--el-color-primary) 12%, transparent);
  --header-accent-overlay-15: color-mix(in srgb, var(--el-color-primary-light-5) 15%, transparent);
  --header-accent-overlay-18: color-mix(in srgb, var(--el-color-primary) 18%, transparent);
  --header-accent-overlay-22: color-mix(in srgb, var(--el-color-primary-light-5) 22%, transparent);
  --header-avatar-gradient: linear-gradient(135deg, var(--el-color-primary), var(--el-color-primary-light-3));
  --header-avatar-gradient-dark: linear-gradient(135deg, var(--el-color-primary-dark-2), var(--el-color-primary-light-3));
  position: relative;
  z-index: 100;
  padding: 0;
  background: transparent;
  border-bottom: none;
  transition: all 0.36s cubic-bezier(0.22, 1, 0.36, 1);
}

.header-inner {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 16px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: rgba(255, 255, 255, 0.55);
  backdrop-filter: var(--blog-navbar-backdrop, blur(20px) saturate(180%));
  -webkit-backdrop-filter: var(--blog-navbar-webkit-backdrop, blur(20px) saturate(180%));
  border-radius: 0 0 14px 14px;
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-top: none;
  box-shadow: 0 6px 30px rgba(0, 0, 0, 0.05);
  transition: all 0.36s cubic-bezier(0.22, 1, 0.36, 1);
}

/* 首页 Banner 区域导航栏 */
.header-inner-transparent {
  background: rgba(255, 255, 255, 0.65);
  backdrop-filter: var(--blog-navbar-backdrop, blur(20px) saturate(180%));
  -webkit-backdrop-filter: var(--blog-navbar-webkit-backdrop, blur(20px) saturate(180%));
  border-color: rgba(0, 0, 0, 0.06);
  box-shadow: 0 6px 30px rgba(0, 0, 0, 0.05);
}

.header-inner-transparent-full,
.header-inner-transparent-dynamic {
  background: transparent;
  backdrop-filter: var(--blog-navbar-backdrop, blur(20px) saturate(180%));
  -webkit-backdrop-filter: var(--blog-navbar-webkit-backdrop, blur(20px) saturate(180%));
  border-color: transparent;
  box-shadow: none;
}

/* 首页滚动后导航栏 */
.header-inner-scrolled {
  background: rgba(255, 255, 255, 0.55);
  backdrop-filter: var(--blog-navbar-backdrop, blur(20px) saturate(180%));
  -webkit-backdrop-filter: var(--blog-navbar-webkit-backdrop, blur(20px) saturate(180%));
  border-color: rgba(0, 0, 0, 0.06);
  box-shadow: 0 6px 30px rgba(0, 0, 0, 0.05);
}

/* 左侧区域 */
.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
  width: 300px;
}

.logo {
  font-size: 18px;
  font-weight: 700;
  color: var(--header-accent) !important;
  text-decoration: none !important;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border-radius: 10px;
  transition: background 0.15s ease-out;
}

.logo:hover {
  background: rgba(0, 0, 0, 0.05);
}

.mobile-nav-dropdown {
  display: none;
}

.mobile-user-entry {
  display: flex;
  align-items: center;
}

.mobile-user-dropdown {
  margin-right: 0;
  margin-left: 0;
}

.user-avatar {
  flex-shrink: 0;
}

.user-avatar--fallback {
  background: var(--header-avatar-gradient);
  color: #fff;
  font-weight: 700;
}

/* 通用按钮风格 - Firefly btn-plain */
.header-btn {
  position: relative;
  z-index: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  padding: 0;
  border: none;
  border-radius: 10px;
  background: transparent;
  color: rgba(0, 0, 0, 0.7);
  cursor: pointer;
  transition: color 0.15s ease-out;
  overflow: hidden;
  outline: none;
}

.header-btn::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  background: rgba(0, 0, 0, 0.06);
  transform: scale(0.85);
  opacity: 0;
  z-index: -1;
  transition: all 0.15s ease-out;
}

.header-btn:hover::before {
  transform: scale(1);
  opacity: 1;
}

.header-btn:active::before {
  background: rgba(0, 0, 0, 0.1);
}

.avatar-btn,
.avatar-btn:hover,
.avatar-btn:focus {
  background: transparent !important;
}

.avatar-btn::before,
.avatar-btn:hover::before,
.avatar-btn:active::before {
  opacity: 0;
  transform: scale(0.85);
  background: transparent;
}

.mobile-home-trigger {
  width: 40px;
  height: 40px;
  color: var(--header-accent);
}

.mobile-home-trigger:hover {
  color: var(--header-accent);
}

.nav-links {
  display: flex;
  gap: 12px;
}

.nav-links a {
  color: rgba(0, 0, 0, 0.65);
  font-size: 14px;
  font-weight: 500;
  text-decoration: none;
  padding: 6px 12px;
  border-radius: 8px;
  transition: all 0.15s ease-out;
}

.nav-links a:hover {
  background: rgba(0, 0, 0, 0.05);
  color: rgba(0, 0, 0, 0.9);
}

.nav-links a.router-link-active {
  color: var(--header-accent);
  background: var(--header-accent-overlay-08);
}

/* 中间搜索框 */
.header-search {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
}

.header-search :deep(.el-input) {
  width: 260px;
}

.header-search :deep(.el-input__wrapper) {
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.04);
  box-shadow: none !important;
  border: 1px solid transparent;
  transition: all 0.2s ease-out;
}

.header-search :deep(.el-input__wrapper:hover) {
  background: rgba(0, 0, 0, 0.07);
}

.header-search :deep(.el-input__wrapper.is-focus) {
  background: rgba(0, 0, 0, 0.1);
  border-color: rgba(0, 0, 0, 0.12);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08) !important;
}

.search-icon {
  cursor: pointer;
  color: rgba(0, 0, 0, 0.45);
  transition: color 0.2s;
}

.search-icon:hover {
  color: var(--header-accent);
}

.header-center-spacer {
  flex: 1;
}

/* 右侧功能区 */
.header-right {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 6px;
  width: 300px;
}

.header-right > * {
  margin: 0;
}

/* 头像和按钮间距 */
.user-dropdown {
  margin-right: 4px;
}

/* 通知按钮 */
.notice-btn {
  color: rgba(0, 0, 0, 0.7);
}

.notice-btn.is-active,
.notice-btn:hover {
  color: var(--header-accent-soft);
}

.notice-btn.is-active::before,
.notice-btn:hover::before {
  background: var(--header-accent-overlay-12);
  opacity: 1;
  transform: scale(1);
}

.notice-btn:active::before {
  background: var(--header-accent-overlay-18);
}

/* 主题按钮 */
.theme-btn {
  color: rgba(0, 0, 0, 0.7);
}

.theme-btn:hover {
  color: var(--header-accent);
}

.theme-btn:hover::before {
  background: var(--header-accent-overlay-12);
  opacity: 1;
  transform: scale(1);
}

.theme-btn:active::before {
  background: var(--header-accent-overlay-18);
}

/* 加号按钮 */
.plus-btn {
  color: rgba(0, 0, 0, 0.7);
}

.plus-btn.is-active,
.plus-btn:hover {
  color: var(--header-accent);
}

.plus-btn.is-active::before,
.plus-btn:hover::before {
  background: var(--header-accent-overlay-12);
  opacity: 1;
  transform: scale(1);
}

.plus-btn:active::before {
  background: var(--header-accent-overlay-18);
}

/* 画板按钮 */
.palette-btn {
  color: rgba(0, 0, 0, 0.7);
}

.palette-btn:hover {
  color: var(--header-accent);
}

.palette-btn:hover::before {
  background: var(--header-accent-overlay-12);
  opacity: 1;
  transform: scale(1);
}

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

/* 加号菜单 */
.header-plus-dropdown {
  display: none;
}

.custom-dropdown-panel.plus-dropdown-panel {
  width: min(360px, calc(100vw - 24px));
  padding: 16px;
}

.header-plus-menu {
  padding: 6px 0;
}

.announcement-entry {
  padding: 0 !important;
}

.plus-menu-row {
  width: 100%;
  min-width: 180px;
  padding: 10px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  color: var(--text-primary);
}

.plus-menu-row.is-active {
  color: var(--header-accent);
}

.plus-menu-main {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.plus-menu-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: #f56c6c;
  flex: 0 0 auto;
}

.custom-divider {
  height: 1px;
  background: var(--el-border-color-light);
  margin: 8px 0;
}
/* 夜间模式 */
.dark .header-inner {
  background: rgba(30, 41, 59, 0.55);
  border-color: rgba(255, 255, 255, 0.08);
  box-shadow: 0 6px 30px rgba(0, 0, 0, 0.2);
}

.dark .header-inner-transparent-full,
.dark .header-inner-transparent-dynamic {
  background: transparent;
  border-color: transparent;
  box-shadow: none;
}

.dark .logo {
  color: var(--header-accent-bright) !important;
}

.dark .logo:hover {
  background: rgba(255, 255, 255, 0.06);
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

.dark .avatar-btn::before,
.dark .avatar-btn:hover::before,
.dark .avatar-btn:active::before {
  opacity: 0;
  transform: scale(0.85);
  background: transparent;
}

.dark .mobile-home-trigger {
  color: var(--header-accent-bright);
}

.dark .nav-links a {
  color: rgba(255, 255, 255, 0.7);
}

.dark .nav-links a:hover {
  background: rgba(255, 255, 255, 0.06);
  color: rgba(255, 255, 255, 0.95);
}

.dark .nav-links a.router-link-active {
  color: var(--header-accent-bright);
  background: var(--header-accent-overlay-10);
}

.dark .header-search :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.06) !important;
  box-shadow: none !important;
  border-color: transparent !important;
}

.dark .header-search :deep(.el-input__wrapper:hover) {
  background: rgba(255, 255, 255, 0.1) !important;
}

.dark .header-search :deep(.el-input__wrapper.is-focus) {
  background: rgba(255, 255, 255, 0.1) !important;
  border-color: rgba(255, 255, 255, 0.15) !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important;
}

.dark .search-icon {
  color: rgba(255, 255, 255, 0.5);
}

.dark .search-icon:hover {
  color: var(--header-accent-bright);
}

.dark .notice-btn {
  color: rgba(255, 255, 255, 0.8);
}

.dark .notice-btn.is-active,
.dark .notice-btn:hover {
  color: var(--header-accent-bright);
}

.dark .notice-btn.is-active::before,
.dark .notice-btn:hover::before {
  background: var(--header-accent-overlay-15);
}

.dark .notice-btn:active::before {
  background: var(--header-accent-overlay-22);
}

.dark .theme-btn:hover {
  color: var(--header-accent-bright);
}

.dark .theme-btn:hover::before {
  background: var(--header-accent-overlay-15);
}

.dark .theme-btn:active::before {
  background: var(--header-accent-overlay-22);
}

.dark .plus-btn.is-active,
.dark .plus-btn:hover {
  color: var(--header-accent-bright);
}

.dark .plus-btn.is-active::before,
.dark .plus-btn:hover::before {
  background: var(--header-accent-overlay-15);
}

.dark .plus-btn:active::before {
  background: var(--header-accent-overlay-22);
}

.dark .palette-btn:hover {
  color: var(--header-accent-bright);
}

.dark .palette-btn:hover::before {
  background: var(--header-accent-overlay-15);
}

.dark .palette-btn:active::before {
  background: var(--header-accent-overlay-22);
}

.dark .user-avatar--fallback {
  background: var(--header-avatar-gradient-dark);
}

.dark .custom-divider {
  background: rgba(255, 255, 255, 0.08);
}

/* Dashboard 页面：Header 贴边、无圆角 */
.header-top-row.dashboard-header {
  padding: 0;
  max-width: none;
}

.app-header.dashboard-header {
  padding: 0;
}

.dashboard-header-inner {
  max-width: none;
  margin: 0;
  border-radius: 0;
}

@media (--mobile-viewport) {
  .header-top-row {
    padding: 0 12px;
  }

  .header-top-row.dashboard-header {
    padding: 0;
  }

  .header-inner {
    padding: 0 12px;
    height: 58px;
    border-radius: 0 0 12px 12px;
  }

  .dashboard-header-inner {
    border-radius: 0;
  }

  .header-left {
    width: auto;
    gap: 8px;
    flex: 0 0 auto;
  }

  .logo-desktop,
  .nav-links,
  .desktop-user-dropdown {
    display: none;
  }

  .mobile-nav-dropdown {
    display: inline-flex;
  }

  .header-search {
    position: static;
    left: auto;
    transform: none;
    flex: 1;
    min-width: 0;
    margin: 0 8px;
  }

  .header-search :deep(.el-input) {
    width: 100%;
    min-width: 0;
  }

  .header-right {
    width: auto;
    gap: 2px;
    flex: 0 0 auto;
  }

  .desktop-notice-btn,
  .desktop-theme-dropdown,
  .palette-dropdown {
    display: none;
  }

  .header-plus-dropdown {
    display: inline-flex;
  }

  .user-dropdown {
    margin-right: 0;
  }

  .mobile-user-dropdown {
    margin-left: 2px;
    margin-right: 2px;
  }
}

@media (max-width: 480px) {
  .header-top-row {
    padding: 0;
  }

  .header-inner {
    padding: 0 10px;
    border-radius: 0 0 10px 10px;
  }

  .header-right {
    gap: 0;
  }
}

/* 自定义下拉面板 - 绕过 ElDropdown */
.dropdown-wrapper {
  position: relative;
}

.dropdown-wrapper:hover::after,
.dropdown-wrapper:focus-within::after {
  content: '';
  position: absolute;
  top: 100%;
  left: var(--panel-left, 50%);
  right: var(--panel-right, auto);
  width: 260px;
  height: 20px;
  transform: var(--panel-transform, translateX(-50%));
}

.custom-dropdown-panel {
  position: absolute;
  top: calc(100% + 20px);
  left: var(--panel-left, 50%);
  right: var(--panel-right, auto);
  transform: var(--panel-transform, translateX(-50%));
  min-width: 160px;
  max-width: calc(100vw - 24px);
  max-height: var(--panel-max-height, calc(100dvh - 92px));
  padding: 8px;
  box-sizing: border-box;
  border-radius: 14px;
  border: 1px solid rgba(0, 0, 0, 0.06);
  background-color: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(16px) saturate(180%);
  -webkit-backdrop-filter: blur(16px) saturate(180%);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.12);
  z-index: 200;
  overflow-x: hidden;
  overflow-y: auto;
  overscroll-behavior: contain;
  transition: background-color 0.24s ease, border-color 0.24s ease, box-shadow 0.24s ease;
  scrollbar-width: thin;
  scrollbar-color: rgba(255, 255, 255, 0.5) rgba(255, 255, 255, 0.18);
}

.custom-dropdown-panel::-webkit-scrollbar {
  width: 10px;
}

.custom-dropdown-panel::-webkit-scrollbar-track {
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.18);
}

.custom-dropdown-panel::-webkit-scrollbar-thumb {
  border: 2px solid transparent;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.5);
  background-clip: padding-box;
}

.custom-dropdown-panel::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.62);
  background-clip: padding-box;
}

.custom-dropdown-panel::-webkit-scrollbar-corner {
  background: transparent;
}



.dropdown-item {
  display: flex;
  align-items: center;
  gap: 8px;
  border-radius: 10px;
  margin: 2px 0;
  padding: 10px 14px;
  font-size: 14px;
  line-height: 1.5;
  color: rgba(0, 0, 0, 0.8);
  cursor: pointer;
  transition: all 0.15s ease-out;
}

.dropdown-item:hover {
  background: rgba(0, 0, 0, 0.04);
  color: var(--header-accent);
}

.theme-dropdown:hover::after,
.theme-dropdown:focus-within::after,
.palette-dropdown:hover::after,
.palette-dropdown:focus-within::after,
.header-plus-dropdown:hover::after,
.header-plus-dropdown:focus-within::after {
  left: auto;
  right: 0;
  transform: none;
}

.theme-dropdown .custom-dropdown-panel,
.palette-dropdown .custom-dropdown-panel,
.header-plus-dropdown .custom-dropdown-panel {
  left: auto;
  right: 0;
  transform: none;
}

.dropdown-enter-active,
.dropdown-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

.dark .custom-dropdown-panel {
  background-color: rgba(30, 41, 59, 0.55);
  border-color: rgba(255, 255, 255, 0.08);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.35);
  scrollbar-color: rgba(255, 255, 255, 0.32) rgba(255, 255, 255, 0.1);
}

.dark .custom-dropdown-panel::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.1);
}

.dark .custom-dropdown-panel::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.32);
  background-clip: padding-box;
}

.dark .custom-dropdown-panel::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.42);
  background-clip: padding-box;
}

/* 页面滚动后下拉框更不透明 */
.header-inner-scrolled .custom-dropdown-panel {
  background-color: rgba(255, 255, 255, 0.95);
}

.dark .header-inner-scrolled .custom-dropdown-panel {
  background-color: rgba(30, 41, 59, 0.8);
}

.dark .dropdown-item {
  color: rgba(255, 255, 255, 0.85);
}

.dark .dropdown-item:hover {
  background: rgba(255, 255, 255, 0.06);
  color: var(--header-accent-bright);
}

</style>
