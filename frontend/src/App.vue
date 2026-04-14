<script setup lang="ts">
import { watch, computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import AppHeader from './components/header/AppHeader.vue'
import LoginModal from './components/LoginModal.vue'
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
    <footer v-if="showBeian" class="app-footer">
      <div class="footer-inner">
        <span class="footer-copyright">© 2026 Sakurakugu. All Rights Reserved.</span>
        <span class="powered-by">
          Powered by
          <a class="powered-link" href="https://cn.vuejs.org/" target="_blank" rel="noopener noreferrer">Vue3</a>
          &
          <a class="powered-link" href="https://github.com/CuteLeaf/Firefly" target="_blank" rel="noopener noreferrer">Firefly</a>
        </span>
        <a class="beian beian-text" href="https://beian.miit.gov.cn" target="_blank" rel="noopener noreferrer">粤ICP备2026031237号</a>
        <a
          class="beian beian-gongan beian-text"
          href="https://beian.mps.gov.cn/#/query/webSearch?code=44011202003729"
          target="_blank"
          rel="noopener noreferrer"
        >
          <img class="logos" src="/备案图标.png" alt="">
          <span>粤公网安备44011202003729号</span>
        </a>
      </div>
    </footer>
    <LoginModal v-model:show="showLogin" :initial-tab="loginTab" />
  </div>
</template>
