<script setup lang="ts">
import { HomeFilled, Search } from '@element-plus/icons-vue'
import { ElAvatar, ElButton, ElDropdown, ElDropdownItem, ElDropdownMenu, ElIcon, ElInput } from 'element-plus'
import { computed, ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useSettingsStore } from '../stores/settings'

const emit = defineEmits<{ 'show-login': [tab?: 'login' | 'register'] }>()
const auth = useAuthStore()
const settings = useSettingsStore()
const router = useRouter()
const route = useRoute()

const searchKeyword = ref('')

// 执行搜索 - 跳转到搜索页面
function doSearch() {
  const query: Record<string, string> = {}
  if (searchKeyword.value) query.search = searchKeyword.value
  router.push({ path: '/search', query: Object.keys(query).length ? query : undefined })
}

const isAuthed = computed(() => auth.isAuthenticated)
const displayName = computed(() => auth.user?.nickname || auth.user?.username || '')

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

onMounted(() => {
  if (!settings.loaded) {
    settings.fetchPublicSettings()
  }
})

// 是否在搜索页面
const isSearchPage = computed(() => route.name === 'SearchPage')
</script>

<template>
  <header class="app-header">
    <div class="header-inner">
      <!-- 左侧区域 -->
      <div class="header-left">
        <router-link to="/blog" class="logo">
          <ElIcon><HomeFilled /></ElIcon>
          <span>Sakurakuguの小窝</span>
        </router-link>
        <nav class="nav-links">
          <router-link to="/blog">首页</router-link>
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
        <template v-if="isAuthed">
          <ElDropdown trigger="click" class="user-dropdown" @command="handleMenu">
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
        <template v-else>
          <ElDropdown trigger="hover" class="user-dropdown" @command="handleGuestMenu">
            <ElButton circle text>
              <ElAvatar size="default" :style="{ backgroundColor: '#e6f7ee', color: '#18a058' }">
                游
              </ElAvatar>
            </ElButton>
            <template #dropdown>
              <ElDropdownMenu>
                <ElDropdownItem command="login">登录</ElDropdownItem>
                <ElDropdownItem v-if="settings.registerEnabled" command="register">注册</ElDropdownItem>
              </ElDropdownMenu>
            </template>
          </ElDropdown>
        </template>
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
  gap: 12px;
  width: 300px;
}

.search-btn {
  color: #666;
}

.search-btn:hover {
  color: #18a058;
  background: #e6f7ee;
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

.user-dropdown .custom-divider {
  display: block;
  height: 1px;
  margin: 6px 12px;
  background: #e4e7ed;
  padding: 0;
  list-style: none;
}
</style>
