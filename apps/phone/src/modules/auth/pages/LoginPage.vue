<script setup lang="ts">
import { developerLoginActions } from '@/modules/auth/lib/dev-login'
import ApiEnvironmentManager from '@/shared/components/ApiEnvironmentManager.vue'
import AppIconButton from '@/shared/components/AppIconButton.vue'
import { useApiEnvironmentConnectivity } from '@/shared/composables/use-api-environment-connectivity'
import { useApiEnvironmentStore } from '@/shared/stores/api-environment'
import { Setting } from '@element-plus/icons-vue'
import { useSettingsStore } from '@personal-system/domain/system'
import {
  AuthEntryPanel,
  useAuthEntry,
} from '@personal-system/modules/auth'
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
      <div class="auth-card__header">
        <AppIconButton
          v-if="canSwitchEnvironment"
          class="auth-settings-button"
          :disabled="loading || environmentLoading"
          label="打开接口环境设置"
          @click="openEnvironmentDialog"
        >
          <Setting aria-hidden="true" />
        </AppIconButton>
      </div>
      <div class="auth-card__title" :class="{ 'auth-card__title--compact-top': canSwitchEnvironment }">
        <h1 class="page-title">Personal System</h1>
      </div>

      <AuthEntryPanel
        v-model:active-tab="activeTab"
        :can-register="showRegisterEntry"
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

.auth-card__header {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr);
  align-items: flex-start;
  gap: 16px;
}

.auth-card__title {
  grid-column: 2;
  text-align: center;
  margin: 20px 0 24px;
}

.auth-card__title--compact-top {
  margin-top: 0;
}

.auth-card__title .page-title {
  margin: 0;
}

.auth-settings-button {
  grid-column: 3;
  justify-self: end;
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
