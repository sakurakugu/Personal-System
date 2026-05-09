<script setup lang="ts">
import { Close } from '@element-plus/icons-vue'
import { useAuthStore, useLoginGateStore } from '@personal-system/domain/auth'
import { AppIconButton, BaseDialog } from '@personal-system/ui'
import { computed, watch } from 'vue'
import DesktopAuthEntryCard from './DesktopAuthEntryCard.vue'

const auth = useAuthStore()
const loginGate = useLoginGateStore()

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
    width="520px"
    :close-on-click-modal="true"
    :show-close="false"
    append-to-body
    class="desktop-login-dialog"
  >
    <DesktopAuthEntryCard
      :default-redirect-path="loginGate.redirectPath"
      :framed="false"
    >
      <template #headerActions>
        <AppIconButton label="关闭登录弹窗" @click="visible = false">
          <Close aria-hidden="true" />
        </AppIconButton>
      </template>
    </DesktopAuthEntryCard>
  </BaseDialog>
</template>

<style scoped>
@import '@personal-system/ui/styles/dropdown.css';

:deep(.desktop-login-dialog .el-dialog) {
  border: 1px solid var(--theme-card-border);
  border-radius: 28px;
  overflow: hidden;
  background: var(--theme-card-bg);
  backdrop-filter: blur(14px);
  box-shadow: var(--theme-card-shadow);
}

:deep(.desktop-login-dialog .el-dialog__header) {
  display: none;
}

:deep(.desktop-login-dialog .el-dialog__body) {
  padding: 20px;
}
</style>
