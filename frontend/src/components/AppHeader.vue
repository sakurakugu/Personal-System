<script setup lang="ts">
import { Bell, HomeFilled, Search, Moon, Plus, Sunny } from '@element-plus/icons-vue'
import { ElAvatar, ElBadge, ElButton, ElDropdown, ElDropdownItem, ElDropdownMenu, ElIcon, ElInput, ElSwitch } from 'element-plus'
import { computed, ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAnnouncementCenter } from '../features/system/announcement-center'
import { useAuthStore } from '../stores/auth'
import { useSettingsStore } from '../stores/settings'
import { useThemeStore } from '../stores/theme'

const emit = defineEmits<{ 'show-login': [tab?: 'login' | 'register'] }>()
const auth = useAuthStore()
const settings = useSettingsStore()
const theme = useThemeStore()
const router = useRouter()
const route = useRoute()
const { hasUnreadAnnouncement } = useAnnouncementCenter()

const searchKeyword = ref('')
const navLinks = [
  { label: '首页', to: '/blog' },
]

onMounted(() => {
  void settings.ensurePublicSettingsLoaded()
})

// 执行搜索 - 跳转到搜索页面
function doSearch() {
  const query: Record<string, string> = {}
  if (searchKeyword.value) query.search = searchKeyword.value
  router.push({ path: '/search', query: Object.keys(query).length ? query : undefined })
}

const isAuthed = computed(() => auth.isAuthenticated)
const displayName = computed(() => auth.user?.nickname || auth.user?.username || '')
const isDashboardPage = computed(() => route.path.startsWith('/dashboard'))
const showUserAvatar = computed(() => !isDashboardPage.value)

const menuOptions = computed(() => {
  const items = [
    { label: '个人资料', key: 'profile' },
    { label: '个人看板', key: 'dashboard' },
    { label: '我的文章', key: 'articles' },
    { label: '我的待办', key: 'todos' },
    { type: 'divider' as const, key: 'd1', label: '' },
    { label: '退出登录', key: 'logout' },
  ]
  if (auth.isAdmin) {
    items.splice(3, 0, { label: '系统状态', key: 'system' })
  }
  if (auth.isSuperAdmin) {
    items.splice(4, 0, { label: '用户管理', key: 'users' })
    items.splice(5, 0, { label: '系统设置', key: 'settings' })
  }
  return items
})

function handleMenu(key: string) {
  switch (key) {
    case 'profile': router.push('/dashboard/profile'); break
    case 'dashboard': router.push('/dashboard'); break
    case 'articles': router.push('/dashboard/articles'); break
    case 'todos': router.push('/dashboard/todos'); break
    case 'system': router.push('/dashboard/system'); break
    case 'users': router.push('/dashboard/users'); break
    case 'settings': router.push('/dashboard/settings'); break
    case 'logout':
      auth.logout()
      router.push('/blog')
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

function setLightMode() {
  theme.isDark = false
  theme.setFollowSystem(false)
}

function setDarkMode() {
  theme.isDark = true
  theme.setFollowSystem(false)
}
</script>

<template>
  <header class="app-header">
    <div class="header-inner">
      <!-- 左侧区域 -->
      <div class="header-left">
        <!-- 移动端左侧头像入口 -->
        <template v-if="showUserAvatar && isAuthed">
          <ElDropdown trigger="click" class="user-dropdown mobile-user-dropdown" @command="handleMenu">
            <ElButton circle text>
              <ElAvatar size="default" :style="{ backgroundColor: '#18a058' }">
                {{ displayName.charAt(0).toUpperCase() }}
              </ElAvatar>
            </ElButton>
            <template #dropdown>
              <ElDropdownMenu>
                <template v-for="(item, index) in menuOptions" :key="item.key">
                  <li v-if="item.type === 'divider'" class="custom-divider" role="separator" />
                  <ElDropdownItem v-else :command="item.key" :divided="index > 0 && menuOptions[index - 1]?.type === 'divider'">
                    {{ item.label }}
                  </ElDropdownItem>
                </template>
              </ElDropdownMenu>
            </template>
          </ElDropdown>
        </template>
        <template v-else-if="showUserAvatar">
          <ElDropdown trigger="hover" class="user-dropdown mobile-user-dropdown" @command="handleGuestMenu">
            <ElButton circle text>
              <ElAvatar size="default" :style="{ backgroundColor: '#e6f7ee', color: '#18a058' }">
                登录
              </ElAvatar>
            </ElButton>
            <template #dropdown>
              <ElDropdownMenu>
                <ElDropdownItem command="login">登录后台</ElDropdownItem>
                <ElDropdownItem v-if="settings.registerEnabled" command="register">注册</ElDropdownItem>
              </ElDropdownMenu>
            </template>
          </ElDropdown>
        </template>
        <router-link to="/blog" class="logo logo-desktop">
          <ElIcon><HomeFilled /></ElIcon>
          <span>Sakurakuguの小窝</span>
        </router-link>
        <ElDropdown v-if="isDashboardPage" trigger="click" class="mobile-nav-dropdown" @command="handleMobileNav">
          <button type="button" class="mobile-home-trigger" aria-label="打开导航菜单">
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
        <template v-if="showUserAvatar && isAuthed">
          <ElDropdown trigger="click" class="user-dropdown desktop-user-dropdown" @command="handleMenu">
            <ElButton circle text>
              <ElAvatar size="default" :style="{ backgroundColor: '#18a058' }">
                {{ displayName.charAt(0).toUpperCase() }}
              </ElAvatar>
            </ElButton>
            <template #dropdown>
              <ElDropdownMenu>
                <template v-for="(item, index) in menuOptions" :key="item.key">
                  <li v-if="item.type === 'divider'" class="custom-divider" role="separator" />
                  <ElDropdownItem v-else :command="item.key" :divided="index > 0 && menuOptions[index - 1]?.type === 'divider'">
                    {{ item.label }}
                  </ElDropdownItem>
                </template>
              </ElDropdownMenu>
            </template>
          </ElDropdown>
        </template>
        <template v-else-if="showUserAvatar">
          <ElDropdown trigger="hover" class="user-dropdown desktop-user-dropdown" @command="handleGuestMenu">
            <ElButton circle text>
              <ElAvatar size="default" :style="{ backgroundColor: '#e6f7ee', color: '#18a058' }">
                登录
              </ElAvatar>
            </ElButton>
            <template #dropdown>
              <ElDropdownMenu>
                <ElDropdownItem command="login">登录后台</ElDropdownItem>
                <ElDropdownItem v-if="settings.registerEnabled" command="register">注册</ElDropdownItem>
              </ElDropdownMenu>
            </template>
          </ElDropdown>
        </template>

        <ElButton
          circle
          text
          class="notice-btn desktop-notice-btn"
          :class="{ 'is-active': isAnnouncementsPage }"
          @click="goToAnnouncements"
        >
          <ElBadge v-if="hasUnreadAnnouncement" is-dot>
            <ElIcon :size="20"><Bell /></ElIcon>
          </ElBadge>
          <ElIcon v-else :size="20"><Bell /></ElIcon>
        </ElButton>

        <ElDropdown trigger="hover" class="theme-dropdown desktop-theme-dropdown">
          <ElButton
            circle
            text
            class="theme-btn"
            @click="theme.toggleTheme"
          >
            <ElIcon :size="20">
              <Moon v-if="theme.isDark" />
              <Sunny v-else />
            </ElIcon>
          </ElButton>
          <template #dropdown>
            <ElDropdownMenu class="theme-dropdown-menu">
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
            </ElDropdownMenu>
          </template>
        </ElDropdown>

        <ElDropdown trigger="click" class="header-plus-dropdown" :hide-on-click="false">
          <ElButton 
            circle
            text
            class="plus-btn"
            :class="{ 'is-active': isAnnouncementsPage }"
          >
            <ElBadge v-if="hasUnreadAnnouncement" is-dot>
              <ElIcon :size="20"><Plus /></ElIcon>
            </ElBadge>
            <ElIcon v-else :size="20"><Plus /></ElIcon>
          </ElButton>
          <template #dropdown>
            <ElDropdownMenu class="header-plus-menu">
              <ElDropdownItem class="announcement-entry" @click="goToAnnouncements">
                <div class="plus-menu-row" :class="{ 'is-active': isAnnouncementsPage }">
                  <span class="plus-menu-main">
                    <ElIcon><Bell /></ElIcon>
                    <span>公告中心</span>
                  </span>
                  <span v-if="hasUnreadAnnouncement" class="plus-menu-dot" aria-hidden="true" />
                </div>
              </ElDropdownItem>
              <li class="custom-divider" role="separator" />
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
            </ElDropdownMenu>
          </template>
        </ElDropdown>
      </div>
    </div>
  </header>
</template>

<style scoped>
.app-header {
  background: #fff;
  border-bottom: 1px solid #e8e8e8;
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-inner {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 16px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

/* 左侧区域 - 固定宽度 */
.header-left {
  display: flex;
  align-items: center;
  gap: 24px;
  width: 300px;
}

.logo {
  font-size: 20px;
  font-weight: 700;
  color: #18a058 !important;
  text-decoration: none !important;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.mobile-nav-dropdown {
  display: none;
}

.mobile-user-dropdown {
  display: none;
  margin-right: 0;
  margin-left: 4px;
}

.mobile-home-trigger {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  padding: 0;
  border: none;
  border-radius: 999px;
  background: transparent;
  color: #18a058;
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
}

.mobile-home-trigger .el-icon {
  font-size: 20px;
}

.mobile-home-trigger:hover {
  background: #e6f7ee;
}

.nav-links {
  display: flex;
  gap: 16px;
}

.nav-links a {
  color: #555;
  font-size: 14px;
  text-decoration: none;
}

.nav-links a:hover,
.nav-links a.router-link-active {
  color: #18a058;
}

/* 中间搜索框 */
.header-search {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
}

.header-search :deep(.el-input) {
  width: 240px;
}

.header-search :deep(.el-input__wrapper) {
  border-radius: 20px;
}

.search-icon {
  cursor: pointer;
  color: #999;
  transition: color 0.2s;
}

.search-icon:hover {
  color: #18a058;
}

.header-center-spacer {
  flex: 1;
}

/* 右侧功能区 - 固定宽度 */
.header-right {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 16px;
  width: 300px;
}

.header-right > * {
  margin: 0;
}

.search-btn {
  color: #666;
}

.search-btn:hover {
  color: #18a058;
  background: #e6f7ee;
}

/* 头像和公告之间增加间距 */
.user-dropdown {
  margin-right: 12px;
}

/* 通知按钮 */
.notice-btn {
  color: #666;
}

.notice-btn.is-active {
  color: #e6a23c;
  background: #fff9e6;
}

.notice-btn:hover {
  color: #e6a23c;
  background: #fff9e6;
}

.dark .notice-btn {
  color: #cbd5e1;
}

.dark .notice-btn.is-active {
  color: #e6a23c;
  background: rgba(230, 162, 60, 0.1);
}

.dark .notice-btn:hover {
  color: #e6a23c;
  background: rgba(230, 162, 60, 0.1);
}

.theme-btn {
  color: #666;
}

.theme-btn:hover {
  color: #18a058;
  background: #e6f7ee;
}

.dark .theme-btn {
  color: #cbd5e1;
}

.dark .theme-btn:hover {
  color: #4ade80;
  background: rgba(74, 222, 128, 0.1);
}

.plus-btn {
  color: #666;
}

.plus-btn.is-active {
  color: #18a058;
  background: #e6f7ee;
}

.plus-btn:hover {
  color: #18a058;
  background: #e6f7ee;
}

.dark .plus-btn {
  color: #cbd5e1;
}

.dark .plus-btn.is-active {
  color: #4ade80;
  background: rgba(74, 222, 128, 0.1);
}

.dark .plus-btn:hover {
  color: #4ade80;
  background: rgba(74, 222, 128, 0.1);
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
  color: var(--el-text-color-primary);
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

/* 下拉菜单样式 */
.user-dropdown :deep(.el-dropdown__list) {
  padding: 6px;
}

.user-dropdown :deep(.el-dropdown-menu) {
  padding: 8px 0;
  min-width: 140px;
}

.user-dropdown :deep(.el-dropdown-menu__item) {
  padding: 10px 20px;
  font-size: 15px;
  line-height: 1.5;
}

.custom-divider {
  display: block;
  height: 1px;
  margin: 6px 12px;
  background: #e4e7ed;
  padding: 0;
  list-style: none;
}

/* 夜间模式 */
.dark .app-header {
  background: var(--header-bg);
  border-bottom-color: var(--border-color);
}

.dark .logo {
  color: #4ade80 !important;
}

.dark .mobile-home-trigger {
  color: #4ade80;
}

.dark .mobile-home-trigger:hover {
  background: rgba(74, 222, 128, 0.1);
}

.dark .nav-links a {
  color: var(--text-secondary);
}

.dark .nav-links a:hover,
.dark .nav-links a.router-link-active {
  color: #4ade80;
}

.dark .search-icon {
  color: var(--text-tertiary);
}

.dark .search-icon:hover {
  color: #4ade80;
}

.dark .custom-divider {
  background: var(--border-color);
}

@media (max-width: 768px) {
  .header-inner {
    padding: 0 12px;
    gap: 10px;
  }

  .header-left {
    width: auto;
    gap: 12px;
    flex: 0 0 auto;
  }

  .logo-desktop,
  .nav-links,
  .desktop-user-dropdown {
    display: none;
  }

  .mobile-user-dropdown,
  .mobile-nav-dropdown {
    display: inline-flex;
  }

  .mobile-nav-dropdown {
    margin-left: 6px;
  }

  .header-search {
    position: static;
    left: auto;
    transform: none;
    flex: 1;
    min-width: 0;
  }

  .header-search :deep(.el-input) {
    width: 100%;
    min-width: 0;
  }

  .header-right {
    width: auto;
    gap: 8px;
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
    margin-left: 6px;
    margin-right: 6px;
  }
}

@media (max-width: 480px) {
  .header-inner {
    padding: 0 8px;
    gap: 8px;
  }

  .header-right {
    gap: 4px;
  }
}
</style>
