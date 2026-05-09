<script setup lang="ts">
import { Close } from '@element-plus/icons-vue'
import { AuthEntryCard } from '@personal-system/module-auth'
import { ElMessage } from 'element-plus'
import { computed } from 'vue'
import { developerLoginActions } from '../../modules/auth/dev-login'
import { BaseDialog } from '@personal-system/ui'
import { useSettingsStore } from '../../shared/stores/settings'

const props = defineProps<{ show: boolean; initialTab?: 'login' | 'register' }>()
const emit = defineEmits<{ 'update:show': [value: boolean] }>()
const settings = useSettingsStore()
const registerEnabled = computed(() => settings.registerEnabled)
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
      <AuthEntryCard
        action-button-label="关闭登录弹窗"
        action-button-type="close"
        :active-tab-reset-key="show"
        :developer-login-actions="developerLoginActions"
        :framed="false"
        :initial-tab="initialTab"
        :messages="{
          loginFailed: '登录失败',
          developerLoginFailed: '开发者登录失败',
          registerFailed: '注册失败',
        }"
        :on-action-button-click="() => emit('update:show', false)"
        :redirect-handler="{
          getRedirectPath: () => '',
          navigate: async () => {
            ElMessage.success('登录成功！')
            emit('update:show', false)
          },
        }"
        :register-enabled="registerEnabled"
      >
        <template #action-icon>
          <Close aria-hidden="true" />
        </template>
      </AuthEntryCard>
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
