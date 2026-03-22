<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { ElButton, ElDialog, ElForm, ElFormItem, ElInput, ElMessage, ElTabPane, ElTabs } from 'element-plus'
import { useAuthStore } from '../stores/auth'
import { useSettingsStore } from '../stores/settings'

const props = defineProps<{ show: boolean; initialTab?: 'login' | 'register' }>()
const emit = defineEmits<{ 'update:show': [value: boolean] }>()
const auth = useAuthStore()
const settings = useSettingsStore()

const activeTab = ref<'login' | 'register'>(props.initialTab || 'login')
const loginForm = ref({ username: '', password: '' })
const registerForm = ref({ username: '', nickname: '', email: '', password: '', confirmPassword: '' })
const loading = ref(false)

async function handleLogin() {
  loading.value = true
  try {
    await auth.login(loginForm.value.username, loginForm.value.password)
    ElMessage.success('登录成功！')
    emit('update:show', false)
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '登录失败')
  } finally {
    loading.value = false
  }
}

async function handleRegister() {
  if (registerForm.value.password !== registerForm.value.confirmPassword) {
    ElMessage.error('两次输入的密码不一致')
    return
  }
  loading.value = true
  try {
    await auth.register(
      registerForm.value.username,
      registerForm.value.email,
      registerForm.value.password,
      registerForm.value.nickname.trim() || undefined,
    )
    ElMessage.success('注册成功，请登录')
    activeTab.value = 'login'
    loginForm.value.username = registerForm.value.username
    // 清空注册表单
    registerForm.value = { username: '', nickname: '', email: '', password: '', confirmPassword: '' }
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '注册失败')
  } finally {
    loading.value = false
  }
}

watch(() => props.initialTab, (val) => {
  if (val) activeTab.value = val
})

watch(() => props.show, (val) => {
  if (val && props.initialTab) activeTab.value = props.initialTab
})

onMounted(() => {
  if (!settings.loaded) {
    settings.fetchPublicSettings()
  }
})
</script>

<template>
  <ElDialog
    :model-value="show"
    title="欢迎"
    width="520px"

    :close-on-click-modal="false"
    class="login-dialog"
    @update:model-value="emit('update:show', $event)"
    @close="emit('update:show', false)"
  >
    <!-- 同时有登录和注册时显示 Tabs -->
    <ElTabs v-if="settings.registerEnabled" v-model="activeTab" stretch>
      <ElTabPane name="login" label="登录">
        <ElForm style="margin-top: 16px" label-width="72px" @submit.prevent="handleLogin">
          <ElFormItem label="用户名">
            <ElInput v-model="loginForm.username" placeholder="请输入用户名" />
          </ElFormItem>
          <ElFormItem label="密码">
            <ElInput v-model="loginForm.password" type="password" placeholder="请输入密码" show-password />
          </ElFormItem>
          <ElButton type="primary" style="width: 100%" :loading="loading" native-type="submit">登录</ElButton>
        </ElForm>
      </ElTabPane>
      <ElTabPane name="register" label="注册">
        <ElForm style="margin-top: 16px" label-width="72px" @submit.prevent="handleRegister">
          <ElFormItem label="用户名">
            <ElInput v-model="registerForm.username" placeholder="至少2个字符" />
          </ElFormItem>
          <ElFormItem label="昵称">
            <ElInput v-model="registerForm.nickname" placeholder="用于展示，可选" />
          </ElFormItem>
          <ElFormItem label="邮箱">
            <ElInput v-model="registerForm.email" placeholder="your@email.com" />
          </ElFormItem>
          <ElFormItem label="密码">
            <ElInput v-model="registerForm.password" type="password" placeholder="至少6位" show-password />
          </ElFormItem>
          <ElFormItem label="确认密码">
            <ElInput v-model="registerForm.confirmPassword" type="password" placeholder="再次输入密码" show-password />
          </ElFormItem>
          <ElButton type="primary" style="width: 100%" :loading="loading" native-type="submit">注册</ElButton>
        </ElForm>
      </ElTabPane>
    </ElTabs>

    <!-- 只有登录时直接显示表单 -->
    <ElForm v-else style="margin-top: 16px" @submit.prevent="handleLogin">
      <ElFormItem label="用户名">
        <ElInput v-model="loginForm.username" placeholder="请输入用户名" />
      </ElFormItem>
      <ElFormItem label="密码">
        <ElInput v-model="loginForm.password" type="password" placeholder="请输入密码" show-password />
      </ElFormItem>
      <ElButton type="primary" style="width: 100%" :loading="loading" native-type="submit">登录</ElButton>
    </ElForm>
  </ElDialog>
</template>

<style scoped>
.login-dialog :deep(.el-dialog) {
  border-radius: 16px;
  overflow: hidden;
  margin-top: auto !important;
  margin-bottom: auto !important;
  top: 50%;
  transform: translateY(-50%);
}

.login-dialog :deep(.el-dialog__header) {
  padding: 24px 24px 0;
}

.login-dialog :deep(.el-dialog__body) {
  padding: 20px 24px 24px;
}

.login-dialog :deep(.el-tabs__nav-wrap::after) {
  height: 1px;
}
</style>
