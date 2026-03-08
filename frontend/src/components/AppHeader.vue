<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { NButton, NAvatar, NDropdown } from 'naive-ui'
import { useAuthStore } from '../stores/auth'

const emit = defineEmits<{ 'show-login': [] }>()
const auth = useAuthStore()
const router = useRouter()

const isAuthed = computed(() => auth.isAuthenticated)
const username = computed(() => auth.user?.username ?? '')

const menuOptions = computed(() => {
  const items = [
    { label: '个人看板', key: 'dashboard' },
    { label: '我的文章', key: 'articles' },
    { label: '我的待办', key: 'todos' },
    { type: 'divider' as const, key: 'd1' },
    { label: '退出登录', key: 'logout' },
  ]
  if (auth.isAdmin) {
    items.splice(3, 0, { label: '系统状态', key: 'system' })
  }
  return items
})

function handleMenu(key: string) {
  switch (key) {
    case 'dashboard': router.push('/dashboard'); break
    case 'articles': router.push('/dashboard/articles'); break
    case 'todos': router.push('/dashboard/todos'); break
    case 'system': router.push('/dashboard/system'); break
    case 'logout':
      auth.logout()
      router.push('/blog')
      break
  }
}
</script>

<template>
  <header class="app-header">
    <div class="header-inner">
      <router-link to="/blog" class="logo">🌸 Sakura Blog</router-link>
      <nav class="nav-links">
        <router-link to="/blog">首页</router-link>
      </nav>
      <div class="header-right">
        <template v-if="isAuthed">
          <NDropdown :options="menuOptions" trigger="click" @select="handleMenu">
            <NButton quaternary circle>
              <NAvatar round size="small" :style="{ backgroundColor: '#18a058' }">
                {{ username.charAt(0).toUpperCase() }}
              </NAvatar>
            </NButton>
          </NDropdown>
        </template>
        <template v-else>
          <NButton type="primary" size="small" @click="emit('show-login')">
            登录
          </NButton>
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
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 16px;
  height: 56px;
  display: flex;
  align-items: center;
  gap: 24px;
}

.logo {
  font-size: 20px;
  font-weight: 700;
  color: #18a058 !important;
  text-decoration: none !important;
}

.nav-links {
  display: flex;
  gap: 16px;
  flex: 1;
}

.nav-links a {
  color: #555;
  font-size: 14px;
}

.nav-links a:hover,
.nav-links a.router-link-active {
  color: #18a058;
}

.header-right {
  display: flex;
  align-items: center;
}
</style>
