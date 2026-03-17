<script setup lang="ts">
import { onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { NConfigProvider, NMessageProvider, NDialogProvider } from 'naive-ui'
import { useAuthStore } from './stores/auth'
import AppHeader from './components/AppHeader.vue'
import LoginModal from './components/LoginModal.vue'
import { ref } from 'vue'

const auth = useAuthStore()
const route = useRoute()
const showLogin = ref(false)

onMounted(async () => {
  if (auth.accessToken) {
    await auth.fetchUser()
  }
})

// If redirected with ?login=1, show login modal
watch(() => route.query.login, (val) => {
  if (val === '1') showLogin.value = true
})
</script>

<template>
  <NConfigProvider>
    <NMessageProvider>
      <NDialogProvider>
        <div class="app-container">
          <AppHeader @show-login="showLogin = true" />
          <main class="main-content">
            <RouterView />
          </main>
          <LoginModal v-model:show="showLogin" />
        </div>
      </NDialogProvider>
    </NMessageProvider>
  </NConfigProvider>
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
