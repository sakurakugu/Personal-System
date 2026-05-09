<script setup lang="ts">
import { useApiEnvironmentStore } from '@/shared/stores/api-environment'
import { developerLoginActions } from '@/modules/auth/lib/dev-login'
import { Setting } from '@element-plus/icons-vue'
import { useApiEnvironmentConnectivity } from '@personal-system/domain/api-environment'
import { useSettingsStore } from '@personal-system/domain/system'
import { AuthEntryPanel, useAuthEntry } from '@personal-system/module-auth'
import { ApiEnvironmentManager } from '@personal-system/ui'
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const props = withDefaults(defineProps<{
  defaultRedirectPath?: string
  framed?: boolean
  actionButtonLabel?: string
  actionButtonType?: 'environment' | 'close'
  hideActionButton?: boolean
  onActionButtonClick?: () => void
}>(), {
  defaultRedirectPath: '/',
  framed: true,
  actionButtonLabel: undefined,
  actionButtonType: 'environment',
  hideActionButton: false,
  onActionButtonClick: undefined,
})

const route = useRoute()
const router = useRouter()
const settings = useSettingsStore()
const apiEnvironmentStore = useApiEnvironmentStore()
const environmentLoading = ref(false)
const environmentDialogVisible = ref(false)
const registerEnabled = computed(() => settings.registerEnabled)
const canSwitchEnvironment = computed(() => apiEnvironmentStore.canSwitchEnvironment)
const activeEnvironmentId = computed(() => apiEnvironmentStore.activeEnvironmentId)
const environments = computed(() => apiEnvironmentStore.environments)
const { refreshing: connectivityRefreshing, refreshConnectivity, getSnapshot } = useApiEnvironmentConnectivity(environments)
const activeEnvironmentReachable = computed(() => getSnapshot(activeEnvironmentId.value).status === 'reachable')
const showRegisterEntry = computed(() => registerEnabled.value && activeEnvironmentReachable.value)
const {
  activeTab,
  errorMessage,
  isDevMode,
  loading,
  loginForm,
  registerForm,
  clearError,
  handleDeveloperLogin,
  handleLogin,
  handleRegister,
} = useAuthEntry({
  redirectHandler: {
    getRedirectPath: () => typeof route.query.redirect === 'string' ? route.query.redirect : props.defaultRedirectPath,
    navigate: async (path) => router.replace(path),
  },
  registerOptions: {
    isReachable: activeEnvironmentReachable,
    isRegisterEnabled: registerEnabled,
  },
})

function normalizeBaseUrl(value: string) {
  return value.trim().replace(/\/+$/, '')
}

function openEnvironmentDialog() {
  environmentDialogVisible.value = true
}

function closeEnvironmentDialog() {
  environmentDialogVisible.value = false
}

function handleSelectEnvironment(id: string) {
  if (id === apiEnvironmentStore.activeEnvironmentId) {
    return
  }
  apiEnvironmentStore.setActiveEnvironment(id)
  clearError()
}

function handleRemoveEnvironment(id: string) {
  apiEnvironmentStore.removeEnvironment(id)
}

function handleSubmitEnvironment(payload: { editingId: string | null; name: string; baseUrl: string }) {
  environmentLoading.value = true
  try {
    if (payload.editingId) {
      apiEnvironmentStore.updateEnvironment(payload.editingId, payload.name, normalizeBaseUrl(payload.baseUrl))
      return
    }

    apiEnvironmentStore.addEnvironment(payload.name, normalizeBaseUrl(payload.baseUrl))
  } finally {
    environmentLoading.value = false
  }
}

function getEnvironmentStatus(id: string) {
  return getSnapshot(id).status
}

function handleActionButtonClick() {
  if (props.onActionButtonClick) {
    props.onActionButtonClick()
    return
  }

  openEnvironmentDialog()
}
</script>

<template>
  <div :class="{ 'auth-card': props.framed }">
    <AuthEntryPanel
      v-model:active-tab="activeTab"
      :action-button-disabled="loading || environmentLoading"
      :action-button-label="props.hideActionButton ? undefined : (props.actionButtonLabel ?? (canSwitchEnvironment ? '打开接口环境设置' : undefined))"
      :can-register="showRegisterEntry"
      :developer-login-actions="developerLoginActions"
      :error-message="errorMessage"
      :is-dev-mode="isDevMode"
      :loading="loading"
      :login-form="loginForm"
      :register-form="registerForm"
      @action-button-click="handleActionButtonClick"
      @developer-login="handleDeveloperLogin"
      @login="handleLogin"
      @register="handleRegister"
    >
      <template #action-icon>
        <slot name="action-icon">
          <Setting v-if="props.actionButtonType === 'environment'" aria-hidden="true" />
        </slot>
      </template>
      <template v-if="$slots.headerActions" #headerActions>
        <slot name="headerActions" />
      </template>
      <template #title>
        <h1 class="page-title">Personal System</h1>
      </template>
    </AuthEntryPanel>
  </div>

  <Teleport to="body">
    <div v-if="canSwitchEnvironment && environmentDialogVisible" class="auth-settings-overlay" @click.self="closeEnvironmentDialog">
      <section class="auth-settings-panel" role="dialog" aria-modal="true" aria-label="接口环境设置">
        <ApiEnvironmentManager
          :environments="environments"
          :active-environment-id="activeEnvironmentId"
          :loading="loading || environmentLoading"
          :refreshing="connectivityRefreshing"
          :show-close-button="true"
          create-action-text="新增环境"
          update-action-text="保存地址"
          :get-status="getEnvironmentStatus"
          :on-refresh="refreshConnectivity"
          :on-close="closeEnvironmentDialog"
          :on-select="handleSelectEnvironment"
          :on-submit="handleSubmitEnvironment"
          :on-remove="handleRemoveEnvironment"
        />
      </section>
    </div>
  </Teleport>
</template>

<style scoped>
.auth-card {
  width: min(100%, 460px);
  padding: 20px;
  border: 1px solid var(--theme-card-border);
  border-radius: 24px;
  background: var(--theme-card-bg);
  backdrop-filter: blur(14px);
  box-shadow: var(--theme-card-shadow);
}

.auth-settings-overlay {
  position: fixed;
  inset: 0;
  z-index: 20;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px 12px;
  background: var(--theme-overlay);
  backdrop-filter: blur(10px);
  overflow-y: auto;
}

.auth-settings-panel {
  width: min(100%, 520px);
  max-height: min(80vh, 720px);
  overflow: auto;
  padding: 20px;
  border: 1px solid var(--theme-card-border);
  border-radius: 28px;
  background: var(--theme-card-bg-strong);
  box-shadow: var(--theme-card-shadow);
}
</style>
