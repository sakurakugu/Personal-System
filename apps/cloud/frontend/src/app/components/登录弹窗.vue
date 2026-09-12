<script setup lang="ts">
import { Close } from '@element-plus/icons-vue'
import { AuthEntryCard } from '@personal-system/module-auth'
import { ElMessage } from 'element-plus'
import { 开发者登录操作 } from '../../modules/认证/dev-login'
import { BaseDialog } from '@personal-system/ui'

const props = defineProps<{ show: boolean }>()
const emit = defineEmits<{ 'update:show': [value: boolean] }>()
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
        :developer-login-actions="开发者登录操作"
        :framed="false"
        :messages="{
          loginFailed: '登录失败',
          developerLoginFailed: '开发者登录失败',
        }"
        :on-action-button-click="() => emit('update:show', false)"
        :redirect-handler="{
          getRedirectPath: () => '',
          navigate: async () => {
            ElMessage.success('登录成功！')
            emit('update:show', false)
          },
        }"
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
