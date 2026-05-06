<script setup lang="ts">
import {
  AuthCredentialsFields,
  AuthDeveloperLoginButtons,
  AuthRegisterFields,
  useAuthEntry,
} from '@personal-system/modules/auth'
import { computed, watch } from 'vue'
import { ElButton, ElForm, ElMessage, ElTabPane, ElTabs } from 'element-plus'
import { useSettingsStore } from '../../shared/stores/settings'
import BaseDialog from '../../shared/components/BaseDialog.vue'
import { developerLoginActions } from '../../modules/auth/dev-login'

const props = defineProps<{ show: boolean; initialTab?: 'login' | 'register' }>()
const emit = defineEmits<{ 'update:show': [value: boolean] }>()
const settings = useSettingsStore()
const registerEnabled = computed(() => settings.registerEnabled)
const {
  activeTab,
  errorMessage,
  isDevMode,
  loading,
  loginForm,
  registerForm,
  handleDeveloperLogin,
  handleLogin,
  handleRegister,
} = useAuthEntry({
  messages: {
    loginFailed: '登录失败',
    developerLoginFailed: '开发者登录失败',
    registerFailed: '注册失败',
  },
  redirectHandler: {
    getRedirectPath: () => '',
    navigate: async () => {
      ElMessage.success('登录成功！')
      emit('update:show', false)
    },
  },
  registerOptions: {
    isRegisterEnabled: registerEnabled,
  },
})

watch(() => props.initialTab, (val) => {
  if (val) activeTab.value = val
})

watch(() => props.show, (val) => {
  if (val && props.initialTab) activeTab.value = props.initialTab
})
</script>

<template>
  <BaseDialog
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
          <AuthCredentialsFields :form="loginForm" label-position="left" />
          <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>
          <ElButton type="primary" style="width: 100%" :loading="loading" native-type="submit">登录</ElButton>
          <div v-if="isDevMode" class="dev-login-row">
            <AuthDeveloperLoginButtons :actions="developerLoginActions" button-class="dev-login-button" :loading="loading" @login="handleDeveloperLogin" />
          </div>
        </ElForm>
      </ElTabPane>
      <ElTabPane name="register" label="注册">
        <ElForm style="margin-top: 16px" label-width="72px" @submit.prevent="handleRegister">
          <AuthRegisterFields :form="registerForm" />
          <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>
          <ElButton type="primary" style="width: 100%" :loading="loading" native-type="submit">注册</ElButton>
        </ElForm>
      </ElTabPane>
    </ElTabs>

    <!-- 只有登录时直接显示表单 -->
    <ElForm v-else style="margin-top: 16px" label-width="72px" @submit.prevent="handleLogin">
      <AuthCredentialsFields :form="loginForm" label-position="left" />
      <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>
      <ElButton type="primary" style="width: 100%" :loading="loading" native-type="submit">登录</ElButton>
      <div v-if="isDevMode" class="dev-login-row">
        <AuthDeveloperLoginButtons :actions="developerLoginActions" button-class="dev-login-button" :loading="loading" @login="handleDeveloperLogin" />
      </div>
    </ElForm>
  </BaseDialog>
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

.dev-login-row {
  margin-top: 12px;
  gap: 0;
  overflow: hidden;
  border-radius: 8px;
}

.dev-login-button {
  margin: 0;
  border-radius: 0;
}

.dev-login-button:not(:first-child) {
  margin-left: -1px;
}

.dev-login-row .dev-login-button:first-child {
  border-top-left-radius: 8px;
  border-bottom-left-radius: 8px;
}

.dev-login-row .dev-login-button:last-child {
  border-top-right-radius: 8px;
  border-bottom-right-radius: 8px;
}

.form-error {
  margin: 0 0 12px;
  color: var(--el-color-danger);
  line-height: 1.5;
  font-size: 0.9rem;
}
</style>
