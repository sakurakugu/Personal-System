<script setup lang="ts">
import { Close } from '@element-plus/icons-vue'
import AuthEntryPanel from '@personal-system/module-auth/components/AuthEntryPanel.vue'
import { useAuthEntry } from '@personal-system/module-auth/use-auth-entry'
import { ElMessage } from 'element-plus'
import { computed, watch } from 'vue'
import { developerLoginActions } from '../../modules/auth/dev-login'
import { BaseDialog } from '@personal-system/ui'
import { useSettingsStore } from '../../shared/stores/settings'

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
    :show-close="false"
    class="login-dialog"
    @update:model-value="emit('update:show', $event)"
    @close="emit('update:show', false)"
  >
    <div class="login-dialog__body">
      <AuthEntryPanel
        v-model:active-tab="activeTab"
        action-button-label="关闭登录弹窗"
        :can-register="registerEnabled"
        :developer-login-actions="developerLoginActions"
        :error-message="errorMessage"
        :is-dev-mode="isDevMode"
        :loading="loading"
        :login-form="loginForm"
        :register-form="registerForm"
        @action-button-click="emit('update:show', false)"
        @developer-login="handleDeveloperLogin"
        @login="handleLogin"
        @register="handleRegister"
      >
        <template #action-icon>
          <Close aria-hidden="true" />
        </template>
      </AuthEntryPanel>
    </div>
  </BaseDialog>
</template>

<style scoped>
.login-dialog :deep(.el-dialog) {
  border: 1px solid var(--theme-card-border);
  border-radius: 24px;
  overflow: hidden;
  margin-top: auto !important;
  margin-bottom: auto !important;
  top: 50%;
  transform: translateY(-50%);
  background: var(--theme-card-bg);
  backdrop-filter: blur(14px);
  box-shadow: var(--theme-card-shadow);
}

.login-dialog :deep(.el-dialog__header) {
  display: none !important;
  padding: 0;
  margin: 0;
  min-height: 0;
}

.login-dialog :deep(.el-dialog__body) {
  padding: 0;
}

.login-dialog__body {
  padding: 20px;
}
</style>
