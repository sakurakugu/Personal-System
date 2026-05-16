<script setup lang="ts">
import { Close } from '@element-plus/icons-vue'
import { 开发者登录操作 } from '@/modules/认证/lib/dev-login'
import { useApiEnvironmentStore } from '@/shared/stores/api-environment'
import { 使用认证存储, 使用登录门禁存储 } from '@personal-system/domain/auth'
import { AuthEntryCard } from '@personal-system/module-auth'
import { AppIconButton, BaseDialog } from '@personal-system/ui'
import { computed, watch } from 'vue'

const auth = 使用认证存储()
const loginGate = 使用登录门禁存储()

const visible = computed({
  get: () => loginGate.visible,
  set: (value: boolean) => {
    if (!value) {
      loginGate.close()
    }
  },
})

watch(
  () => auth.isAuthenticated,
  (authenticated) => {
    if (authenticated && loginGate.visible) {
      loginGate.close()
    }
  },
)
</script>

<template>
  <BaseDialog
    v-model="visible"
    width="min(100vw - 24px, 520px)"
    :close-on-click-modal="true"
    :show-close="false"
    append-to-body
    class="phone-login-dialog"
  >
    <AuthEntryCard
      :default-redirect-path="loginGate.redirectPath"
      :developer-login-actions="开发者登录操作"
      :framed="false"
      settings-panel-class="stack"
      :use-api-environment-store="useApiEnvironmentStore"
    >
      <template #headerActions>
        <AppIconButton label="关闭登录弹窗" @click="visible = false">
          <Close aria-hidden="true" />
        </AppIconButton>
      </template>
    </AuthEntryCard>
  </BaseDialog>
</template>

<style scoped>
@import '@personal-system/ui/styles/dropdown.css';

:deep(.phone-login-dialog .el-dialog) {
  max-width: calc(100vw - 24px);
  margin: 0 auto;
  border: 1px solid var(--theme-card-border);
  border-radius: 28px;
  overflow: hidden;
  background: var(--theme-card-bg);
  backdrop-filter: blur(14px);
  box-shadow: var(--theme-card-shadow);
}

:deep(.phone-login-dialog .el-dialog__header) {
  display: none;
}

:deep(.phone-login-dialog .el-dialog__body) {
  padding: 16px;
}

@media (max-width: 480px) {
  :deep(.phone-login-dialog .el-dialog__body) {
    padding: 12px;
  }
}
</style>
