<script setup lang="ts">
import { developerLoginActions } from '@/modules/auth/lib/dev-login'
import { useSettingsStore } from '@personal-system/domain/system'
import { AuthEntryPanel, useAuthEntry } from '@personal-system/module-auth'
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const settings = useSettingsStore()
const registerEnabled = computed(() => settings.registerEnabled)
const {
  activeTab,
  canRegister,
  errorMessage,
  isDevMode,
  loading,
  loginForm,
  registerForm,
  handleDeveloperLogin,
  handleLogin,
  handleRegister,
} = useAuthEntry({
  redirectHandler: {
    getRedirectPath: () => typeof route.query.redirect === 'string' ? route.query.redirect : '/',
    navigate: async (path) => router.replace(path),
  },
  registerOptions: {
    isRegisterEnabled: registerEnabled,
  },
})
</script>

<template>
  <section class="page auth-page">
    <div class="auth-card">
      <div class="auth-card__title">
        <h1 class="page-title">Personal System</h1>
      </div>

      <AuthEntryPanel
        v-model:active-tab="activeTab"
        :can-register="canRegister"
        :developer-login-actions="developerLoginActions"
        :error-message="errorMessage"
        :is-dev-mode="isDevMode"
        :loading="loading"
        :login-form="loginForm"
        :register-form="registerForm"
        @developer-login="handleDeveloperLogin"
        @login="handleLogin"
        @register="handleRegister"
      />
    </div>
  </section>
</template>

<style scoped>
.auth-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  min-height: 100dvh;
  padding: 24px;
}

.auth-card {
  width: min(100%, 460px);
  padding: 20px;
  border: 1px solid var(--theme-card-border);
  border-radius: 24px;
  background: var(--theme-card-bg);
  backdrop-filter: blur(14px);
  box-shadow: var(--theme-card-shadow);
}

.auth-card__title {
  margin: 20px 0 24px;
  text-align: center;
}

.auth-card__title .page-title {
  margin: 0;
}
</style>
