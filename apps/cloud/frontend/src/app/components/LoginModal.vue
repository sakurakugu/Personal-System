<script setup lang="ts">
import {
  AuthEntryPanel,
  useAuthEntry,
} from '@personal-system/modules/auth'
import { computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
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
    width="520px"
    :close-on-click-modal="false"
    class="login-dialog"
    @update:model-value="emit('update:show', $event)"
    @close="emit('update:show', false)"
  >
    <div class="login-dialog__body">
      <AuthEntryPanel
        v-model:active-tab="activeTab"
        :can-register="registerEnabled"
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
  </BaseDialog>
</template>

<style scoped>
.login-dialog :deep(.el-dialog) {
  border-radius: 24px;
  overflow: hidden;
  margin-top: auto !important;
  margin-bottom: auto !important;
  top: 50%;
  transform: translateY(-50%);
  background: transparent;
  box-shadow: none;
}

.login-dialog :deep(.el-dialog__header) {
  display: none;
}

.login-dialog :deep(.el-dialog__body) {
  padding: 0;
}

.login-dialog__body {
  padding: 20px;
  border: 1px solid var(--theme-card-border);
  border-radius: 24px;
  background: var(--theme-card-bg);
  backdrop-filter: blur(14px);
  box-shadow: var(--theme-card-shadow);
}
</style>
