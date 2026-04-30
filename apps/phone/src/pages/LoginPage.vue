<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@personal-system/domain/auth'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

const form = reactive({
  username: '',
  password: '',
})
const errorMessage = ref('')
const loading = ref(false)

async function handleSubmit() {
  errorMessage.value = ''
  loading.value = true

  try {
    await auth.login(form.username, form.password)
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/'
    await router.replace(redirect)
  } catch (error: any) {
    errorMessage.value = error?.response?.data?.detail || '登录失败，请检查用户名和密码'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="page auth-page">
    <div class="auth-card">
      <p class="eyebrow">手机端</p>
      <h1 class="page-title">登录 Personal System</h1>
      <p class="page-subtitle">先提供最小可用入口，后续再补注册与更多能力。</p>

      <form class="auth-form" @submit.prevent="handleSubmit">
        <label class="field">
          <span class="field-label">用户名</span>
          <input v-model="form.username" class="field-input" autocomplete="username" placeholder="请输入用户名">
        </label>

        <label class="field">
          <span class="field-label">密码</span>
          <input v-model="form.password" class="field-input" type="password" autocomplete="current-password" placeholder="请输入密码">
        </label>

        <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>

        <button class="primary-button" type="submit" :disabled="loading">
          {{ loading ? '登录中…' : '登录' }}
        </button>
      </form>
    </div>
  </section>
</template>
