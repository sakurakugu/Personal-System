<script setup lang="ts">
import { watch, computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import AppHeader from './components/header/AppHeader.vue'
import LoginModal from './components/LoginModal.vue'
import FloatingControls from './components/FloatingControls.vue'
import { useClickEffect } from './composables/useClickEffect'

useClickEffect()

const route = useRoute()
const showLogin = ref(false)
const loginTab = ref<'login' | 'register'>('login')

const showBeian = computed(() => {
  return !route.path.startsWith('/dashboard')
})

watch(() => route.query.login, (val) => {
  if (val) {
    loginTab.value = 'login'
    showLogin.value = true
  }
}, { immediate: true })

function openAuth(tab?: 'login' | 'register') {
  if (tab) loginTab.value = tab
  showLogin.value = true
}
</script>

<template>
  <div class="app-container">
    <AppHeader @show-login="openAuth" />
    <main class="main-content">
      <RouterView />
    </main>
    <LoginModal v-model:show="showLogin" :initial-tab="loginTab" />
    <FloatingControls v-if="showBeian" />
  </div>
</template>
