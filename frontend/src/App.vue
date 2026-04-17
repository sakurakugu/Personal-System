<script setup lang="ts">
import { watch, computed, defineAsyncComponent, ref } from 'vue'
import { useRoute } from 'vue-router'
import AppHeader from './components/header/AppHeader.vue'
import { useClickEffect } from './composables/useClickEffect'

const LoginModal = defineAsyncComponent(() => import('./components/LoginModal.vue'))
const FloatingControls = defineAsyncComponent(() => import('./components/FloatingControls.vue'))
const SakuraEffect = defineAsyncComponent(() => import('./components/SakuraEffect.vue'))

useClickEffect()

const route = useRoute()
const showLogin = ref(false)
const loginTab = ref<'login' | 'register'>('login')
const shouldMountLoginModal = ref(false)
const shouldMountSakuraEffect = ref(false)

const showBeian = computed(() => {
  return !route.path.startsWith('/dashboard')
})

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
  </div>
</template>
