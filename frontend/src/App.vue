<script setup lang="ts">
import { onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from './stores/auth'
import AppHeader from './components/AppHeader.vue'
import LoginModal from './components/LoginModal.vue'
import { ref } from 'vue'

const auth = useAuthStore()
const route = useRoute()
const showLogin = ref(false)
const loginTab = ref<'login' | 'register'>('login')

onMounted(async () => {
  if (auth.accessToken) {
    await auth.fetchUser()
  }
})

// If redirected with ?login=1, show login modal
watch(() => route.query.login, (val) => {
  if (val === '1') {
    loginTab.value = 'login'
    showLogin.value = true
  }
})

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
  </div>
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background: #f5f7fa;
  color: #333;
  min-height: 100vh;
}

.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.main-content {
  flex: 1;
  width: 100%;
}

a {
  color: #18a058;
  text-decoration: none;
}

a:hover {
  text-decoration: underline;
}
</style>
