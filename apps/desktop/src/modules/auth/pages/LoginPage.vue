<script setup lang="ts">
import { developerLoginActions } from '@/modules/auth/lib/dev-login'
import { AuthCredentialsFields, AuthDeveloperLoginButtons, useAuthEntry } from '@personal-system/modules/auth'
import { ElAlert, ElButton, ElCard, ElForm } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const {
  errorMessage,
  isDevMode,
  loading,
  loginForm,
  handleDeveloperLogin,
  handleLogin,
} = useAuthEntry({
  redirectHandler: {
    getRedirectPath: () => typeof route.query.redirect === 'string' ? route.query.redirect : '/',
    navigate: async (path) => router.replace(path),
  },
})
</script>

<template>
  <div class="login-page">
    <ElCard class="login-card">
      <div class="login-card__header">
        <h1>Personal System</h1>
      </div>

      <ElForm label-position="top" @submit.prevent="handleLogin">
        <AuthCredentialsFields :form="loginForm" label-position="top" />

        <ElAlert
          v-if="errorMessage"
          :closable="false"
          :title="errorMessage"
          class="login-error"
          type="error"
        />

        <ElButton :loading="loading" class="login-submit" native-type="submit" type="primary">
          登录
        </ElButton>

        <div v-if="isDevMode" class="dev-login-block">
          <p class="dev-login-title">开发快捷登录</p>
          <AuthDeveloperLoginButtons
            :actions="developerLoginActions"
            button-class="dev-login-button"
            :loading="loading"
            @login="handleDeveloperLogin"
          />
        </div>
      </ElForm>
    </ElCard>
  </div>
</template>

<style scoped>
.login-page {
  display: grid;
  place-items: center;
  min-height: 100vh;
  padding: 24px;
  background:
    radial-gradient(circle at top left, color-mix(in srgb, var(--desktop-accent) 22%, transparent), transparent 30%),
    var(--desktop-bg);
}

.login-card {
  width: min(100%, 420px);
  border-radius: 24px;
}

.login-card__header {
  margin-bottom: 20px;
}

.login-card__header h1 {
  margin: 0 0 8px;
}

.login-card__header p {
  margin: 0;
  color: var(--desktop-text-muted);
}

.login-error {
  margin-bottom: 14px;
}

.login-submit {
  width: 100%;
  min-height: 44px;
}

.dev-login-block {
  display: grid;
  gap: 10px;
  margin-top: 16px;
}

.dev-login-title {
  margin: 0;
  font-size: 0.9rem;
  color: var(--desktop-text-muted);
}

.dev-login-block :deep(.dev-login-row) {
  gap: 8px;
}

.dev-login-block :deep(.dev-login-button) {
  min-height: 40px;
  margin: 0;
  padding-left: 10px;
  padding-right: 10px;
  font-size: 0.76rem;
  line-height: 1.35;
  white-space: normal;
  text-align: center;
}
</style>
