<script setup lang="ts">
import { ElAlert, ElButton, ElCard, ElForm, ElFormItem, ElInput } from 'element-plus'
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@personal-system/domain/auth'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const loading = ref(false)
const errorMessage = ref('')
const form = reactive({
  username: '',
  password: '',
})

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
  <div class="login-page">
    <ElCard class="login-card">
      <div class="login-card__header">
        <h1>Personal System Desktop</h1>
        <p>桌面端当前使用设备令牌登录。</p>
      </div>

      <ElForm label-position="top" @submit.prevent="handleSubmit">
        <ElFormItem label="用户名">
          <ElInput
            v-model="form.username"
            autocomplete="username"
            clearable
            placeholder="请输入用户名"
          />
        </ElFormItem>

        <ElFormItem label="密码">
          <ElInput
            v-model="form.password"
            autocomplete="current-password"
            placeholder="请输入密码"
            show-password
            type="password"
          />
        </ElFormItem>

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
