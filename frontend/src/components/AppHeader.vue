<script setup lang="ts">
/* global HTMLElement, MouseEvent */
import { Bell, Connection, HomeFilled, Moon, Plus, Search, Sunny } from '@element-plus/icons-vue'
import { ElAvatar, ElBadge, ElButton, ElDropdown, ElDropdownItem, ElDropdownMenu, ElIcon, ElInput, ElSwitch } from 'element-plus'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useViewport } from '../composables/useViewport'
import { useAnnouncementCenter } from '../features/system/announcement-center'
import { useAuthStore } from '../stores/auth'
import { useSettingsStore } from '../stores/settings'
import { useThemeStore } from '../stores/theme'
import { isApiEnvironmentSwitchEnabled } from '../utils/runtime'
import ApiEnvironmentDialog from './ApiEnvironmentDialog.vue'

const emit = defineEmits<{ 'show-login': [tab?: 'login' | 'register'] }>()
const auth = useAuthStore()
const settings = useSettingsStore()
const theme = useThemeStore()
const router = useRouter()
const route = useRoute()
const { hasUnreadAnnouncement } = useAnnouncementCenter()
const showApiEnvironmentDialog = ref(false)

const showUserMenu = ref(false)
const showMobileUserMenu = ref(false)
const showThemePanel = ref(false)
const showPlusPanel = ref(false)

const userDropdownRef = ref<HTMLElement>()
const mobileUserDropdownRef = ref<HTMLElement>()
const themeDropdownRef = ref<HTMLElement>()
const plusDropdownRef = ref<HTMLElement>()

function adjustPanelPosition(wrapperEl?: HTMLElement) {
  if (!wrapperEl) return
  const panel = wrapperEl.querySelector('.custom-dropdown-panel') as HTMLElement | null
  if (!panel) return
  const wrapperRect = wrapperEl.getBoundingClientRect()
  const panelRect = panel.getBoundingClientRect()
  const viewportWidth = window.innerWidth
  const gap = 8

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
  wrapperEl.style.setProperty('--panel-left', `${relativeLeft}px`)
  wrapperEl.style.setProperty('--panel-transform', 'none')
}

watch(showUserMenu, async (v) => {
  if (v) {
    await nextTick()
    adjustPanelPosition(userDropdownRef.value)
  }
})

watch(showMobileUserMenu, async (v) => {
  if (v) {
    await nextTick()
    adjustPanelPosition(mobileUserDropdownRef.value)
  }
})

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

function closeAllDropdowns(e?: MouseEvent) {
  if (!e) {
    showUserMenu.value = false
    showMobileUserMenu.value = false
    showThemePanel.value = false
    showPlusPanel.value = false
    return
  }
  const path = e.composedPath ? e.composedPath() : []
  const insideUser = userDropdownRef.value && path.includes(userDropdownRef.value)
  const insideMobileUser = mobileUserDropdownRef.value && path.includes(mobileUserDropdownRef.value)
  const insideTheme = themeDropdownRef.value && path.includes(themeDropdownRef.value)
  const insidePlus = plusDropdownRef.value && path.includes(plusDropdownRef.value)
  if (!insideUser) showUserMenu.value = false
  if (!insideMobileUser) showMobileUserMenu.value = false
  if (!insideTheme) showThemePanel.value = false
  if (!insidePlus) showPlusPanel.value = false
}

const searchKeyword = ref('')
const navLinks = [
  { label: '首页', to: '/blog' },
]

onMounted(() => {
  void settings.ensurePublicSettingsLoaded()
  document.addEventListener('click', closeAllDropdowns)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', closeAllDropdowns)
})

// 执行搜索 - 跳转到搜索页面
function doSearch() {
  const query: Record<string, string> = {}
  if (searchKeyword.value) query.search = searchKeyword.value
  router.push({ path: '/search', query: Object.keys(query).length ? query : undefined })
}

const isAuthed = computed(() => auth.isAuthenticated)
const displayName = computed(() => auth.user?.nickname || auth.user?.username || '')
const avatarText = computed(() => displayName.value.slice(0, 1).toUpperCase() || 'U')
const isDashboardPage = computed(() => route.path.startsWith('/dashboard'))
const { isMobileViewport } = useViewport()
const canShowApiEnvironmentEntry = isApiEnvironmentSwitchEnabled()
type UserMenuItem = { label: string; key: string; type?: 'divider' }

const menuOptions = computed<UserMenuItem[]>(() => {
  const items: UserMenuItem[] = [
    { label: '个人资料', key: 'profile' },
    { label: '用户设置', key: 'user-settings' },
    { label: '个人看板', key: 'dashboard' },
    { label: '我的文章', key: 'articles' },
    { label: '我的待办', key: 'todos' },
  ]
  if (auth.isSuperAdmin) {
    items.push({ label: '系统状态', key: 'system' })
  }
  if (auth.isAdmin) {
    items.push({ label: '用户管理', key: 'users' })
  }
  if (auth.isSuperAdmin) {
    items.push({ label: '系统设置', key: 'settings' })
  }
  items.push({ type: 'divider' as const, key: 'd1', label: '' })
  items.push({ label: '退出登录', key: 'logout' })
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

function goToAnnouncements() {
  router.push('/announcements')
}

function handleMobileNav(path: string) {
  router.push(path)
}

const isSearchPage = computed(() => route.name === 'SearchPage')
const isAnnouncementsPage = computed(() => route.name === 'AnnouncementsPage')
const isHomePage = computed(() => route.path === '/blog' || route.path === '/')

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

function setLightMode() {
  theme.isDark = false
  theme.setFollowSystem(false)
}

function setDarkMode() {
  theme.isDark = true
  theme.setFollowSystem(false)
}

function openApiEnvironmentDialog() {
  showApiEnvironmentDialog.value = true
}
</script>

<template>
  <header class="app-header">
    <div
      class="header-inner"
      :class="{ 'header-inner-transparent': isHomePage && !isScrolled, 'header-inner-scrolled': isHomePage && isScrolled }"
    >
      <!-- 左侧区域 -->
      <div class="header-left">
        <!-- 移动端左侧头像入口 -->
        <div v-if="isMobileViewport && !isDashboardPage" class="mobile-user-entry">
          <template v-if="isAuthed">
            <div ref="mobileUserDropdownRef" class="dropdown-wrapper user-dropdown mobile-user-dropdown">
              <ElButton class="header-btn" @click.stop="showMobileUserMenu = !showMobileUserMenu">
                <ElAvatar
                  v-if="auth.user?.avatar_url"
                  :src="auth.user.avatar_url"
                  size="default"
                  class="user-avatar"
                />
                <ElAvatar v-else size="default" class="user-avatar user-avatar--fallback">
                  {{ avatarText }}
                </ElAvatar>
              </ElButton>
              <Transition name="dropdown">
                <div v-show="showMobileUserMenu" class="custom-dropdown-panel">
                  <template v-for="item in menuOptions" :key="item.key">
                    <div v-if="item.type === 'divider'" class="custom-divider" role="separator" />
                    <div v-else class="dropdown-item" @click="handleMenu(item.key); showMobileUserMenu = false">
                      {{ item.label }}
                    </div>
                  </template>
                </div>
              </Transition>
            </div>
          </template>
          <template v-else>
            <div ref="mobileUserDropdownRef" class="dropdown-wrapper user-dropdown mobile-user-dropdown" @mouseenter="showMobileUserMenu = true" @mouseleave="showMobileUserMenu = false">
              <ElButton class="header-btn">
                <ElAvatar size="default" :style="{ backgroundColor: '#e6f7ee', color: '#18a058' }">
                  登录
                </ElAvatar>
              </ElButton>
              <Transition name="dropdown">
                <div v-show="showMobileUserMenu" class="custom-dropdown-panel">
                  <div class="dropdown-item" @click="handleGuestMenu('login'); showMobileUserMenu = false">登录</div>
                  <div v-if="settings.registerEnabled" class="dropdown-item" @click="handleGuestMenu('register'); showMobileUserMenu = false">注册</div>
                </div>
              </Transition>
            </div>
          </template>
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

      <!-- 中间搜索框 - 仅在非搜索页面显示 -->
      <div v-if="!isSearchPage" class="header-search">
        <ElInput
          v-model="searchKeyword"
          placeholder="搜索文章..."
          clearable
          @keyup.enter="doSearch"
        >
          <template #suffix>
            <ElIcon class="search-icon" @click="doSearch">
              <Search />
            </ElIcon>
          </template>
        </ElInput>
      </div>

      <!-- 中间占位 -->
      <div v-else class="header-center-spacer" />

      <!-- 右侧功能区 -->
      <div class="header-right">
        <!-- 用户菜单 -->
        <template v-if="!isMobileViewport && isAuthed">
          <div
            ref="userDropdownRef"
            class="dropdown-wrapper user-dropdown desktop-user-dropdown"
            @mouseenter="showUserMenu = true"
            @mouseleave="showUserMenu = false"
          >
            <ElButton class="header-btn">
              <ElAvatar
                v-if="auth.user?.avatar_url"
                :src="auth.user.avatar_url"
                size="default"
                class="user-avatar"
              />
              <ElAvatar v-else size="default" class="user-avatar user-avatar--fallback">
                {{ avatarText }}
              </ElAvatar>
            </ElButton>
            <Transition name="dropdown">
              <div v-show="showUserMenu" class="custom-dropdown-panel">
                <template v-for="item in menuOptions" :key="item.key">
                  <div v-if="item.type === 'divider'" class="custom-divider" role="separator" />
                  <div v-else class="dropdown-item" @click="handleMenu(item.key); showUserMenu = false">
                    {{ item.label }}
                  </div>
                </template>
                <div class="custom-divider" role="separator" />
                <div class="follow-system-row click-effect-row">
                  <span>点击特效</span>
                  <ElSwitch
                    :model-value="theme.clickEffectEnabled"
                    @update:model-value="theme.setClickEffectEnabled"
                  />
                </div>
              </div>
            </Transition>
          </div>
        </template>
        <template v-else-if="!isMobileViewport">
          <div ref="userDropdownRef" class="dropdown-wrapper user-dropdown desktop-user-dropdown" @mouseenter="showUserMenu = true" @mouseleave="showUserMenu = false">
            <ElButton class="header-btn">
              <ElAvatar size="default" :style="{ backgroundColor: '#e6f7ee', color: '#18a058' }">
                登录
              </ElAvatar>
            </ElButton>
            <Transition name="dropdown">
              <div v-show="showUserMenu" class="custom-dropdown-panel">
                <div class="dropdown-item" @click="handleGuestMenu('login'); showUserMenu = false">登录</div>
                <div v-if="settings.registerEnabled" class="dropdown-item" @click="handleGuestMenu('register'); showUserMenu = false">注册</div>
                <div class="custom-divider" role="separator" />
                <div class="follow-system-row click-effect-row">
                  <span>点击特效</span>
                  <ElSwitch
                    :model-value="theme.clickEffectEnabled"
                    @update:model-value="theme.setClickEffectEnabled"
                  />
                </div>
              </div>
            </Transition>
          </div>
        </template>

        <ElButton
          class="notice-btn desktop-notice-btn header-btn"
          :class="{ 'is-active': isAnnouncementsPage }"
          @click="goToAnnouncements"
        >
          <ElBadge v-if="hasUnreadAnnouncement" is-dot>
            <ElIcon :size="20"><Bell /></ElIcon>
          </ElBadge>
          <ElIcon v-else :size="20"><Bell /></ElIcon>
        </ElButton>

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
              <div class="theme-dropdown-content">
                <div class="theme-title">主题设置</div>
                <div class="theme-options">
                  <div
                    class="theme-option"
                    :class="{ active: !theme.followSystem && !theme.isDark }"
                    @click="setLightMode"
                  >
                    <ElIcon><Sunny /></ElIcon>
                    <span>浅色</span>
                  </div>
                  <div
                    class="theme-option"
                    :class="{ active: !theme.followSystem && theme.isDark }"
                    @click="setDarkMode"
                  >
                    <ElIcon><Moon /></ElIcon>
                    <span>深色</span>
                  </div>
                </div>
                <div class="theme-divider" />
                <div class="follow-system-row">
                  <span>跟随系统</span>
                  <ElSwitch
                    :model-value="theme.followSystem"
                    @update:model-value="theme.setFollowSystem"
                  />
                </div>
              </div>
            </div>
          </Transition>
        </div>

        <div
          ref="plusDropdownRef"
          class="dropdown-wrapper header-plus-dropdown"
          @mouseenter="showPlusPanel = true"
          @mouseleave="showPlusPanel = false"
        >
          <ElButton 
            class="plus-btn header-btn"
            :class="{ 'is-active': isAnnouncementsPage }"
          >
            <ElBadge v-if="hasUnreadAnnouncement" is-dot>
              <ElIcon :size="20"><Plus /></ElIcon>
            </ElBadge>
            <ElIcon v-else :size="20"><Plus /></ElIcon>
          </ElButton>
          <Transition name="dropdown">
            <div v-show="showPlusPanel" class="custom-dropdown-panel">
              <div class="dropdown-item" :class="{ 'is-active': isAnnouncementsPage }" @click="goToAnnouncements(); showPlusPanel = false">
                <span class="plus-menu-main"><ElIcon><Bell /></ElIcon><span>公告中心</span></span>
                <span v-if="hasUnreadAnnouncement" class="plus-menu-dot" aria-hidden="true" />
              </div>
              <div v-if="canShowApiEnvironmentEntry" class="dropdown-item" @click="openApiEnvironmentDialog(); showPlusPanel = false">
                <span class="plus-menu-main"><ElIcon><Connection /></ElIcon><span>接口环境</span></span>
              </div>
              <div class="custom-divider" role="separator" />
              <div class="follow-system-row click-effect-row">
                <span>点击特效</span>
                <ElSwitch
                  :model-value="theme.clickEffectEnabled"
                  @update:model-value="theme.setClickEffectEnabled"
                />
              </div>
              <div class="custom-divider" role="separator" />
              <div class="theme-dropdown-content">
                <div class="theme-title">主题设置</div>
                <div class="theme-options">
                  <div
                    class="theme-option"
                    :class="{ active: !theme.followSystem && !theme.isDark }"
                    @click="setLightMode"
                  >
                    <ElIcon><Sunny /></ElIcon>
                    <span>浅色</span>
                  </div>
                  <div
                    class="theme-option"
                    :class="{ active: !theme.followSystem && theme.isDark }"
                    @click="setDarkMode"
                  >
                    <ElIcon><Moon /></ElIcon>
                    <span>深色</span>
                  </div>
                </div>
                <div class="theme-divider" />
                <div class="follow-system-row">
                  <span>跟随系统</span>
                  <ElSwitch
                    :model-value="theme.followSystem"
                    @update:model-value="theme.setFollowSystem"
                  />
                </div>
              </div>
            </div>
          </Transition>
        </div>
      </div>
    </div>
  </header>
  <ApiEnvironmentDialog v-model="showApiEnvironmentDialog" />
</template>

<style scoped>
@import '../styles/media.css';

/* ========== Firefly 风格导航栏 ========== */

.app-header {
  position: sticky;
  top: 0;
  z-index: 100;
  padding: 0 16px;
  background: transparent;
  border-bottom: none;
}

.header-inner {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 16px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border-radius: 0 0 14px 14px;
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-top: none;
  box-shadow: 0 6px 30px rgba(0, 0, 0, 0.05);
  transition: all 0.36s cubic-bezier(0.22, 1, 0.36, 1);
}

/* 首页 Banner 区域透明导航栏 */
.header-inner-transparent {
  background: transparent;
  backdrop-filter: none;
  -webkit-backdrop-filter: none;
  border-color: transparent;
  box-shadow: none;
}

.header-inner-transparent .logo {
  color: #ffffff !important;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

.header-inner-transparent .logo:hover {
  background: rgba(255, 255, 255, 0.15);
}

.header-inner-transparent .header-btn {
  color: rgba(255, 255, 255, 0.95);
}

.header-inner-transparent .header-btn::before {
  background: rgba(255, 255, 255, 0.15);
}

.header-inner-transparent .header-btn:active::before {
  background: rgba(255, 255, 255, 0.22);
}

.header-inner-transparent .nav-links a {
  color: rgba(255, 255, 255, 0.9);
}

.header-inner-transparent .nav-links a:hover {
  background: rgba(255, 255, 255, 0.12);
  color: #ffffff;
}

.header-inner-transparent .nav-links a.router-link-active {
  color: #4ade80;
  background: rgba(74, 222, 128, 0.15);
}

.header-inner-transparent .header-search :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.15);
  border-color: transparent;
}

.header-inner-transparent .header-search :deep(.el-input__wrapper:hover) {
  background: rgba(255, 255, 255, 0.22);
}

.header-inner-transparent .header-search :deep(.el-input__wrapper.is-focus) {
  background: rgba(255, 255, 255, 0.95);
  border-color: rgba(0, 0, 0, 0.08);
}

.header-inner-transparent .search-icon {
  color: rgba(255, 255, 255, 0.8);
}

.header-inner-transparent .search-icon:hover {
  color: #ffffff;
}

/* 首页滚动后恢复毛玻璃 */
.header-inner-scrolled {
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border-color: rgba(0, 0, 0, 0.06);
  box-shadow: 0 6px 30px rgba(0, 0, 0, 0.05);
}

.dark .header-inner-transparent {
  background: transparent;
  border-color: transparent;
  box-shadow: none;
}

.dark .header-inner-transparent .logo {
  color: #ffffff !important;
}

.dark .header-inner-transparent .logo:hover {
  background: rgba(255, 255, 255, 0.1);
}

.dark .header-inner-transparent .header-btn {
  color: rgba(255, 255, 255, 0.95);
}

.dark .header-inner-transparent .header-btn::before {
  background: rgba(255, 255, 255, 0.12);
}

.dark .header-inner-transparent .header-search :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.1);
}

.dark .header-inner-transparent .header-search :deep(.el-input__wrapper:hover) {
  background: rgba(255, 255, 255, 0.16);
}

.dark .header-inner-transparent .header-search :deep(.el-input__wrapper.is-focus) {
  background: rgba(15, 23, 42, 0.95);
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
  color: #18a058 !important;
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
  background: linear-gradient(135deg, #18a058, #4cb080);
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

.mobile-home-trigger {
  width: 40px;
  height: 40px;
  color: #18a058;
}

.mobile-home-trigger:hover {
  color: #18a058;
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
  color: #18a058;
  background: rgba(24, 160, 88, 0.08);
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
  background: rgba(255, 255, 255, 0.95);
  border-color: rgba(0, 0, 0, 0.12);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08) !important;
}

.search-icon {
  cursor: pointer;
  color: rgba(0, 0, 0, 0.45);
  transition: color 0.2s;
}

.search-icon:hover {
  color: #18a058;
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
  color: #e6a23c;
}

.notice-btn.is-active::before,
.notice-btn:hover::before {
  background: rgba(230, 162, 60, 0.12);
  opacity: 1;
  transform: scale(1);
}

.notice-btn:active::before {
  background: rgba(230, 162, 60, 0.18);
}

/* 主题按钮 */
.theme-btn {
  color: rgba(0, 0, 0, 0.7);
}

.theme-btn:hover {
  color: #18a058;
}

.theme-btn:hover::before {
  background: rgba(24, 160, 88, 0.12);
  opacity: 1;
  transform: scale(1);
}

.theme-btn:active::before {
  background: rgba(24, 160, 88, 0.18);
}

/* 加号按钮 */
.plus-btn {
  color: rgba(0, 0, 0, 0.7);
}

.plus-btn.is-active,
.plus-btn:hover {
  color: #18a058;
}

.plus-btn.is-active::before,
.plus-btn:hover::before {
  background: rgba(24, 160, 88, 0.12);
  opacity: 1;
  transform: scale(1);
}

.plus-btn:active::before {
  background: rgba(24, 160, 88, 0.18);
}

/* 加号菜单 */
.header-plus-dropdown {
  display: none;
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
  color: #18a058;
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

.theme-dropdown-content {
  padding: 8px 12px;
  min-width: 140px;
}

.theme-title {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-bottom: 8px;
}

.theme-options {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}

.theme-option {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 8px;
  border-radius: 6px;
  cursor: pointer;
  border: 1px solid var(--el-border-color-light);
  transition: all 0.2s;
}

.theme-option:hover {
  border-color: var(--el-color-primary);
  color: var(--el-color-primary);
}

.theme-option.active {
  border-color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
}

.theme-option .el-icon {
  font-size: 18px;
}

.theme-option span {
  font-size: 12px;
}

.custom-divider {
  height: 1px;
  background: var(--el-border-color-light);
  margin: 8px 0;
}

.theme-divider {
  height: 1px;
  background: var(--el-border-color-light);
  margin: 8px 0;
}

.follow-system-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 13px;
  color: var(--el-text-color-primary);
}

.click-effect-row {
  padding: 10px 16px;
  min-width: 180px;
}

.user-dropdown :deep(.click-effect-row) {
  padding: 10px 20px;
  min-width: 140px;
}

:global(.dark .theme-dropdown-content) {
  background: transparent !important;
}

:global(.dark .theme-title) {
  color: #e5e7eb !important;
}

:global(.dark .theme-option) {
  border-color: var(--border-color) !important;
  color: #e5e7eb !important;
}

:global(.dark .theme-option:hover) {
  border-color: var(--el-color-primary) !important;
  color: var(--el-color-primary) !important;
}

:global(.dark .theme-option.active) {
  background: var(--el-color-primary-dark-2) !important;
  border-color: var(--el-color-primary-dark-2) !important;
  color: var(--el-color-primary-light-9) !important;
}

:global(.dark .theme-divider) {
  background: var(--border-color) !important;
}

:global(.dark .follow-system-row) {
  color: #e5e7eb !important;
}

.dark .theme-divider {
  background: var(--el-border-color-dark);
}

.dark .follow-system-row {
  color: #e5e7eb;
}

/* 夜间模式 */
.dark .header-inner {
  background: rgba(30, 41, 59, 0.8);
  border-color: rgba(255, 255, 255, 0.08);
  box-shadow: 0 6px 30px rgba(0, 0, 0, 0.2);
}

.dark .logo {
  color: #4ade80 !important;
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

.dark .mobile-home-trigger {
  color: #4ade80;
}

.dark .nav-links a {
  color: rgba(255, 255, 255, 0.7);
}

.dark .nav-links a:hover {
  background: rgba(255, 255, 255, 0.06);
  color: rgba(255, 255, 255, 0.95);
}

.dark .nav-links a.router-link-active {
  color: #4ade80;
  background: rgba(74, 222, 128, 0.1);
}

.dark .header-search :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.06);
  box-shadow: none !important;
  border-color: transparent;
}

.dark .header-search :deep(.el-input__wrapper:hover) {
  background: rgba(255, 255, 255, 0.1);
}

.dark .header-search :deep(.el-input__wrapper.is-focus) {
  background: rgba(15, 23, 42, 0.95);
  border-color: rgba(255, 255, 255, 0.15);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important;
}

.dark .search-icon {
  color: rgba(255, 255, 255, 0.5);
}

.dark .search-icon:hover {
  color: #4ade80;
}

.dark .notice-btn {
  color: rgba(255, 255, 255, 0.8);
}

.dark .notice-btn.is-active,
.dark .notice-btn:hover {
  color: #e6a23c;
}

.dark .notice-btn.is-active::before,
.dark .notice-btn:hover::before {
  background: rgba(230, 162, 60, 0.15);
}

.dark .notice-btn:active::before {
  background: rgba(230, 162, 60, 0.22);
}

.dark .theme-btn:hover {
  color: #4ade80;
}

.dark .theme-btn:hover::before {
  background: rgba(74, 222, 128, 0.15);
}

.dark .theme-btn:active::before {
  background: rgba(74, 222, 128, 0.22);
}

.dark .plus-btn.is-active,
.dark .plus-btn:hover {
  color: #4ade80;
}

.dark .plus-btn.is-active::before,
.dark .plus-btn:hover::before {
  background: rgba(74, 222, 128, 0.15);
}

.dark .plus-btn:active::before {
  background: rgba(74, 222, 128, 0.22);
}

.dark .user-avatar--fallback {
  background: linear-gradient(135deg, #1d9c64, #62c491);
}

.dark .custom-divider {
  background: rgba(255, 255, 255, 0.08);
}

@media (--mobile-viewport) {
  .app-header {
    padding: 0 12px;
  }

  .header-inner {
    padding: 0 12px;
    height: 58px;
    border-radius: 0 0 12px 12px;
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
  .desktop-theme-dropdown {
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
  .app-header {
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
  width: 260px;
  height: 20px;
  transform: var(--panel-transform, translateX(-50%));
}

.custom-dropdown-panel {
  position: absolute;
  top: calc(100% + 20px);
  left: var(--panel-left, 50%);
  transform: var(--panel-transform, translateX(-50%));
  min-width: 160px;
  padding: 8px;
  border-radius: 14px;
  border: 1px solid rgba(0, 0, 0, 0.06);
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(16px) saturate(180%);
  -webkit-backdrop-filter: blur(16px) saturate(180%);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.12);
  z-index: 200;
}



.dropdown-item {
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
  color: #18a058;
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
  background: rgba(30, 41, 59, 0.92);
  border-color: rgba(255, 255, 255, 0.08);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.35);
}

.dark .dropdown-item {
  color: rgba(255, 255, 255, 0.85);
}

.dark .dropdown-item:hover {
  background: rgba(255, 255, 255, 0.06);
  color: #4ade80;
}
</style>
