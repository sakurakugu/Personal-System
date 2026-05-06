<script setup lang="ts">
import { House, Monitor, SwitchButton, User } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { computed, ref } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@personal-system/domain/auth'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const loggingOut = ref(false)

const navItems = computed(() => [
  { to: '/', label: '概览', icon: House },
  { to: '/device-sessions', label: '登录设备', icon: Monitor },
  { to: '/profile', label: '账户信息', icon: User },
])

async function handleLogout() {
  loggingOut.value = true
  let errorMessage = ''
  try {
    try {
      await auth.logout()
    } catch (error: any) {
      errorMessage = error?.response?.data?.detail || '退出登录失败'
    }
    await router.replace('/login')
    if (errorMessage) {
      ElMessage.error(errorMessage)
    }
  } finally {
    loggingOut.value = false
  }
}
</script>

<template>
  <div class="desktop-layout">
    <aside class="desktop-sidebar">
      <div class="desktop-brand">
        <div class="desktop-brand__logo">PS</div>
        <div>
          <strong>Personal System</strong>
          <p>Desktop</p>
        </div>
      </div>

      <nav class="desktop-nav">
        <RouterLink
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="desktop-nav__link"
          :class="{ 'desktop-nav__link--active': route.path === item.to }"
        >
          <component :is="item.icon" class="desktop-nav__icon" />
          <span>{{ item.label }}</span>
        </RouterLink>
      </nav>

      <div class="desktop-sidebar__footer">
        <div class="desktop-user">
          <strong>{{ auth.user?.nickname || auth.user?.username }}</strong>
          <span>{{ auth.user?.role || 'guest' }}</span>
        </div>
        <button class="desktop-logout" :disabled="loggingOut" @click="handleLogout">
          <SwitchButton class="desktop-nav__icon" />
          <span>{{ loggingOut ? '退出中' : '退出登录' }}</span>
        </button>
      </div>
    </aside>

    <main class="desktop-main">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.desktop-layout {
  display: grid;
  grid-template-columns: 260px minmax(0, 1fr);
  min-height: 100vh;
  background: var(--desktop-bg);
}

.desktop-sidebar {
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding: 24px;
  border-right: 1px solid var(--desktop-border);
  background: var(--desktop-panel);
}

.desktop-brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.desktop-brand__logo {
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  border-radius: 14px;
  color: #fff;
  background: var(--desktop-accent);
}

.desktop-brand p {
  margin: 4px 0 0;
  color: var(--desktop-text-muted);
}

.desktop-nav {
  display: grid;
  gap: 8px;
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

.desktop-nav__icon {
  width: 18px;
  height: 18px;
}

.desktop-sidebar__footer {
  display: grid;
  gap: 12px;
  margin-top: auto;
}

.desktop-user {
  display: grid;
  gap: 4px;
  padding: 14px;
  border: 1px solid var(--desktop-border);
  border-radius: 16px;
}

.desktop-user span {
  color: var(--desktop-text-muted);
}

.desktop-logout {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 44px;
  border: 0;
  border-radius: 14px;
  color: #fff;
  background: #e85d75;
  cursor: pointer;
}

.desktop-logout:disabled {
  cursor: default;
  opacity: 0.7;
}

.desktop-main {
  min-width: 0;
}
</style>
