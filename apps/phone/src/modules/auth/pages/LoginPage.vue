<script setup lang="ts">
import { developerLoginActions } from '@/modules/auth/lib/dev-login'
import { useApiEnvironmentStore } from '@/shared/stores/api-environment'
import { Setting } from '@element-plus/icons-vue'
import { useSettingsStore } from '@personal-system/domain/system'
import { useApiEnvironmentConnectivity } from '@personal-system/domain/api-environment'
import {
  AuthEntryPanel,
  useAuthEntry,
} from '@personal-system/module-auth'
import { ApiEnvironmentManager } from '@personal-system/ui'
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const settings = useSettingsStore()
const apiEnvironmentStore = useApiEnvironmentStore()
const route = useRoute()
const router = useRouter()
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
    getRedirectPath: () => typeof route.query.redirect === 'string' ? route.query.redirect : '/',
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
</script>

<template>
  <section class="page auth-page">
    <div class="auth-card">
      <AuthEntryPanel
        v-model:active-tab="activeTab"
        :action-button-disabled="loading || environmentLoading"
        :action-button-label="canSwitchEnvironment ? '打开接口环境设置' : undefined"
        :can-register="showRegisterEntry"
        :developer-login-actions="developerLoginActions"
        :error-message="errorMessage"
        :is-dev-mode="isDevMode"
        :loading="loading"
        :login-form="loginForm"
        :register-form="registerForm"
        @action-button-click="openEnvironmentDialog"
        @developer-login="handleDeveloperLogin"
        @login="handleLogin"
        @register="handleRegister"
      >
        <template #action-icon>
          <Setting aria-hidden="true" />
        </template>
        <template #title>
          <h1 class="page-title">Personal System</h1>
        </template>
      </AuthEntryPanel>
    </div>

    <Teleport to="body">
      <div v-if="canSwitchEnvironment && environmentDialogVisible" class="auth-settings-overlay" @click.self="closeEnvironmentDialog">
        <section class="auth-settings-panel stack" role="dialog" aria-modal="true" aria-label="接口环境设置">
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
  </section>
</template>

<style scoped>
.auth-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  min-height: 100dvh;
  padding-top: 24px;
  padding-bottom: 24px;
}

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
  border: 1px solid var(--theme-card-border);
  border-radius: 28px;
  padding: 20px;
  background: var(--theme-card-bg-strong);
  box-shadow: var(--theme-card-shadow);
}

</style>
