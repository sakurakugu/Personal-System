<script setup lang="ts">
import { AuthCredentialsFields, useAuthEntry } from '@personal-system/modules/auth'
import { ElAlert, ElButton, ElCard, ElForm } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const {
  errorMessage,
  loading,
  loginForm,
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
        <h1>Personal System Desktop</h1>
        <p>桌面端当前使用设备令牌登录。</p>
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
</style>
