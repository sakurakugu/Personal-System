<script setup lang="ts">
import { ref } from 'vue'
import { NModal, NCard, NForm, NFormItem, NInput, NButton, NTabs, NTabPane, useMessage } from 'naive-ui'
import { useAuthStore } from '../stores/auth'
import { useRouter } from 'vue-router'

const props = defineProps<{ show: boolean }>()
const emit = defineEmits<{ 'update:show': [value: boolean] }>()
const message = useMessage()
const auth = useAuthStore()
const router = useRouter()

const activeTab = ref('login')
const loginForm = ref({ username: '', password: '' })
const registerForm = ref({ username: '', email: '', password: '' })
const loading = ref(false)

async function handleLogin() {
  loading.value = true
  try {
    await auth.login(loginForm.value.username, loginForm.value.password)
    message.success('登录成功！')
    emit('update:show', false)
    router.push('/dashboard')
  } catch (e: any) {
    message.error(e.response?.data?.detail || '登录失败')
  } finally {
    loading.value = false
  }
}

async function handleRegister() {
  loading.value = true
  try {
    await auth.register(registerForm.value.username, registerForm.value.email, registerForm.value.password)
    message.success('注册成功，请登录')
    activeTab.value = 'login'
    loginForm.value.username = registerForm.value.username
  } catch (e: any) {
    message.error(e.response?.data?.detail || '注册失败')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <NModal :show="show" @update:show="emit('update:show', $event)">
    <NCard title="欢迎" :bordered="false" style="width: 400px; max-width: 90vw" closable @close="emit('update:show', false)">
      <NTabs v-model:value="activeTab" type="segment" animated>
        <NTabPane name="login" tab="登录">
          <NForm @submit.prevent="handleLogin" style="margin-top: 16px">
            <NFormItem label="用户名">
              <NInput v-model:value="loginForm.username" placeholder="请输入用户名" />
            </NFormItem>
            <NFormItem label="密码">
              <NInput v-model:value="loginForm.password" type="password" placeholder="请输入密码" show-password-on="click" />
            </NFormItem>
            <NButton type="primary" block :loading="loading" attr-type="submit">登录</NButton>
          </NForm>
        </NTabPane>
        <NTabPane name="register" tab="注册">
          <NForm @submit.prevent="handleRegister" style="margin-top: 16px">
            <NFormItem label="用户名">
              <NInput v-model:value="registerForm.username" placeholder="至少2个字符" />
            </NFormItem>
            <NFormItem label="邮箱">
              <NInput v-model:value="registerForm.email" placeholder="your@email.com" />
            </NFormItem>
            <NFormItem label="密码">
              <NInput v-model:value="registerForm.password" type="password" placeholder="至少6位" show-password-on="click" />
            </NFormItem>
            <NButton type="primary" block :loading="loading" attr-type="submit">注册</NButton>
          </NForm>
        </NTabPane>
      </NTabs>
    </NCard>
  </NModal>
</template>
