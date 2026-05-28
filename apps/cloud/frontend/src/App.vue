<script setup lang="ts">
import { computed, defineAsyncComponent, ref, watch } from 'vue'
import { 使用认证存储 } from '@personal-system/domain/auth'
import type { 聊天请求配置 } from '@personal-system/ui'
import { useRoute } from 'vue-router'
import AppHeader from './app/components/header/应用顶栏.vue'
import { 使用点击效果 } from './app/composables/使用点击效果'
import { 判断是否控制台路由 } from './app/router/route-meta'

const LoginModal = defineAsyncComponent(() => import('./app/components/登录弹窗.vue'))
const FloatingControls = defineAsyncComponent(() => import('./app/components/浮动控制.vue'))
const SakuraEffect = defineAsyncComponent(() => import('./app/components/樱花特效.vue'))
const AIChatWidget = defineAsyncComponent(() =>
  import('@personal-system/ui').then((module) => module.AIChatWidget),
)

使用点击效果()

const route = useRoute()
const auth = 使用认证存储()
const showLogin = ref(false)
const loginTab = ref<'login' | 'register'>('login')
const shouldMountLoginModal = ref(false)
const shouldMountSakuraEffect = ref(false)

const showBeian = computed(() => {
  return !判断是否控制台路由(route)
})
const shouldShowAIChat = computed(() => auth.isAuthenticated)

watch(() => route.query.login, (val) => {
  if (val) {
    loginTab.value = 'login'
    shouldMountLoginModal.value = true
    showLogin.value = true
  }
}, { immediate: true })

function openAuth(tab?: 'login' | 'register') {
  if (tab) loginTab.value = tab
  shouldMountLoginModal.value = true
  showLogin.value = true
}

function 读取Cookie(name: string): string | null {
  const prefix = `${name}=`
  for (const item of document.cookie.split(';')) {
    const normalized = item.trim()
    if (normalized.startsWith(prefix)) {
      return decodeURIComponent(normalized.slice(prefix.length))
    }
  }
  return null
}

function 注入AI聊天请求头(config: 聊天请求配置): 聊天请求配置 {
  const headers = new globalThis.Headers(config.init.headers)
  const csrfToken = 读取Cookie('csrf_token')
  if (csrfToken) {
    headers.set('X-CSRF-Token', csrfToken)
  }
  return {
    ...config,
    init: {
      ...config.init,
      headers,
    },
  }
}

watch(showBeian, (visible) => {
  if (visible) {
    shouldMountSakuraEffect.value = true
  }
}, { immediate: true })
</script>

<template>
  <div class="app-container">
    <AppHeader @show-login="openAuth" />
    <main class="main-content">
      <RouterView />
    </main>
    <LoginModal v-if="shouldMountLoginModal" v-model:show="showLogin" :initial-tab="loginTab" />
    <FloatingControls v-if="showBeian" />
    <SakuraEffect v-if="shouldMountSakuraEffect" />
    <AIChatWidget v-if="shouldShowAIChat" url="/api/v1/ai/chat" :before-request="注入AI聊天请求头" />
  </div>
</template>
