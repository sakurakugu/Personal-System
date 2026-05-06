<script setup lang="ts">
import { developerLoginActions } from '@/modules/auth/lib/dev-login'
import ApiEnvironmentManager from '@/shared/components/ApiEnvironmentManager.vue'
import AppIconButton from '@/shared/components/AppIconButton.vue'
import { useApiEnvironmentConnectivity } from '@/shared/composables/use-api-environment-connectivity'
import { useApiEnvironmentStore } from '@/shared/stores/api-environment'
import { Setting } from '@element-plus/icons-vue'
import { useSettingsStore } from '@personal-system/domain/system'
import {
  AuthCredentialsFields,
  AuthDeveloperLoginButtons,
  AuthRegisterFields,
  useAuthEntry,
} from '@personal-system/modules/auth'
import { ElAlert, ElButton, ElForm, ElTabPane, ElTabs } from 'element-plus'
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

      <template v-if="showRegisterEntry">
        <ElTabs v-model="activeTab" class="auth-tabs" stretch>
          <ElTabPane label="登录" name="login">
            <ElForm class="auth-form" label-position="top" @submit.prevent="handleLogin">
              <AuthCredentialsFields :form="loginForm" input-class="auth-input" item-class="auth-form-item" />

              <ElAlert v-if="errorMessage" class="auth-error" :closable="false" type="error" :title="errorMessage" />

              <ElButton class="auth-primary-button" type="primary" native-type="submit" :loading="loading">登录</ElButton>

              <div v-if="isDevMode" class="dev-login-block">
                <p class="field-label">开发快捷登录</p>
                <AuthDeveloperLoginButtons
                  :actions="developerLoginActions"
                  button-class="dev-login-button"
                  :loading="loading"
                  @login="handleDeveloperLogin"
                />
              </div>
            </ElForm>
          </ElTabPane>

          <ElTabPane label="注册" name="register">
            <ElForm class="auth-form" label-position="top" @submit.prevent="handleRegister">
              <AuthRegisterFields :form="registerForm" input-class="auth-input" item-class="auth-form-item" />

              <ElAlert v-if="errorMessage" class="auth-error" :closable="false" type="error" :title="errorMessage" />

              <ElButton class="auth-primary-button" type="primary" native-type="submit" :loading="loading">注册</ElButton>
            </ElForm>
          </ElTabPane>
        </ElTabs>
      </template>

      <ElForm v-else class="auth-form auth-form--standalone" label-position="top" @submit.prevent="handleLogin">
        <AuthCredentialsFields :form="loginForm" input-class="auth-input" item-class="auth-form-item" />

        <ElAlert v-if="errorMessage" class="auth-error" :closable="false" type="error" :title="errorMessage" />

        <ElButton class="auth-primary-button" type="primary" native-type="submit" :loading="loading">登录</ElButton>

        <div v-if="isDevMode" class="dev-login-block">
          <p class="field-label">开发快捷登录</p>
          <AuthDeveloperLoginButtons
            :actions="developerLoginActions"
            button-class="dev-login-button"
            :loading="loading"
            @login="handleDeveloperLogin"
          />
        </div>
      </ElForm>
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

.auth-form {
  display: grid;
  gap: 10px;
  margin-top: 12px;
}

.auth-form--standalone {
  margin-top: 18px;
}

.auth-form :deep(.auth-form-item) {
  margin-bottom: 0;
}

.auth-form :deep(.el-form-item__label) {
  padding-bottom: 5px;
  line-height: 1.3;
  font-size: 0.9rem;
  color: var(--theme-accent-strong);
}

:deep(.auth-input) {
  width: 100%;
}

:deep(.auth-input .el-input__wrapper) {
  padding: 0 16px;
  border-radius: 16px;
  background: var(--theme-input-bg);
  box-shadow: 0 0 0 1px var(--theme-input-border) inset;
}

:deep(.auth-input .el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px var(--theme-input-border-hover) inset;
}

:deep(.auth-input .el-input__wrapper.is-focus) {
  box-shadow:
    0 0 0 1px var(--el-color-primary) inset,
    0 0 0 3px var(--theme-focus-ring);
}

:deep(.auth-input .el-input__inner) {
  height: 48px;
  color: var(--text-primary);
}

:deep(.auth-input .el-input__inner::placeholder) {
  color: var(--text-quaternary);
}

:deep(.auth-input .el-input__suffix-inner) {
  gap: 8px;
}

:deep(.auth-input .el-input__clear),
:deep(.auth-input .el-input__password) {
  color: color-mix(in srgb, var(--theme-accent-strong) 70%, transparent);
}

:deep(.auth-input .el-input__clear:hover),
:deep(.auth-input .el-input__password:hover) {
  color: var(--theme-accent-strong);
}

.auth-error {
  margin: 2px 0;
}

.auth-error :deep(.el-alert) {
  border-radius: 14px;
}

.auth-error :deep(.el-alert__title) {
  line-height: 1.4;
}

.auth-primary-button {
  width: 100%;
  min-height: 48px;
  margin-top: 12px;
  border: 0;
  border-radius: 16px;
  background: var(--theme-accent-gradient);
}

.auth-primary-button:hover,
.auth-primary-button:focus-visible {
  background: var(--theme-accent-gradient-hover);
}

.auth-primary-button.is-loading,
.auth-primary-button.is-disabled {
  opacity: 0.7;
}

.dev-login-block {
  display: grid;
  gap: 10px;
}

.dev-login-block :deep(.dev-login-row) {
  gap: 8px;
}

.dev-login-block :deep(.dev-login-button) {
  min-height: 44px;
  margin: 0;
  padding-left: 10px;
  padding-right: 10px;
  font-size: 0.72rem;
  border-radius: 10px;
  color: var(--theme-accent-strong);
  border-color: var(--theme-card-border);
  background: var(--theme-panel-soft);
  white-space: normal;
  text-align: center;
  line-height: 1.35;
}

.auth-tabs {
  margin-top: 18px;
}

.auth-tabs :deep(.el-tabs__header) {
  margin: 0;
}

.auth-tabs :deep(.el-tabs__nav-wrap) {
  border: 1px solid var(--theme-card-border);
  border-radius: 18px;
  background: var(--theme-panel-subtle);
}

.auth-tabs :deep(.el-tabs__nav-wrap::after) {
  display: none;
}

.auth-tabs :deep(.el-tabs__nav) {
  position: relative;
  width: 100%;
  gap: 4px;
  isolation: isolate;
}

.auth-tabs :deep(.el-tabs__item) {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 44px;
  padding: 0;
  border-radius: 14px;
  color: var(--theme-accent-strong);
  font-size: 0.96rem;
  text-align: center;
}

.auth-tabs :deep(.el-tabs__active-bar) {
  height: 100%;
  bottom: 0;
  border-radius: 14px;
  background: var(--theme-accent-gradient);
  box-shadow: 0 10px 20px color-mix(in srgb, var(--el-color-primary) 26%, transparent);
}

.auth-tabs :deep(.el-tabs__item.is-active) {
  color: #fff;
}

.auth-tabs :deep(.el-tab-pane) {
  padding-top: 14px;
}
</style>
