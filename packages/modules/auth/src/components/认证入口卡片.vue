<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ElAlert, ElButton, ElForm, ElTabPane, ElTabs } from 'element-plus'
import { Setting } from '@element-plus/icons-vue'
import { 使用API环境连接性 } from '@personal-system/domain/api-environment'
import { 使用设置存储 } from '@personal-system/domain/system'
import { ApiEnvironmentManager, AppIconButton } from '@personal-system/ui'
import type { Ref } from 'vue'
import type { DeveloperLoginAction } from '../dev-login'
import type { AuthEntryMessages, AuthEntryRedirectHandler } from '../使用认证入口'
import { 使用认证入口 } from '../使用认证入口'
import AuthCredentialsFields from './认证凭证字段.vue'
import AuthDeveloperLoginButtons from './认证开发者登录按钮.vue'
import AuthRegisterFields from './认证注册字段.vue'
import { useRoute, useRouter } from 'vue-router'

interface ApiEnvironmentItem {
  id: string
  name: string
  baseUrl: string
}

interface ApiEnvironmentStoreLike {
  canSwitchEnvironment: boolean
  activeEnvironmentId: string
  environments: ApiEnvironmentItem[]
  设置活动环境: (id: string) => void
  添加环境: (name: string, baseUrl: string) => void
  更新环境: (id: string, name: string, baseUrl: string) => void
  移除环境: (id: string) => void
}
interface Props {
  actionButtonLabel?: string
  actionButtonDisabled?: boolean
  actionButtonType?: 'environment' | 'close'
  activeTabResetKey?: boolean | number | string
  defaultRedirectPath?: string
  developerLoginActions: DeveloperLoginAction[]
  framed?: boolean
  hideActionButton?: boolean
  initialTab?: 'login' | 'register'
  loginButtonText?: string
  messages?: AuthEntryMessages
  onActionButtonClick?: () => void
  redirectHandler?: AuthEntryRedirectHandler
  registerButtonText?: string
  registerEnabled?: boolean
  settingsPanelClass?: string
  使用API环境存储?: () => ApiEnvironmentStoreLike
}

const props = withDefaults(defineProps<Props>(), {
  actionButtonLabel: undefined,
  actionButtonDisabled: false,
  actionButtonType: 'environment',
  activeTabResetKey: undefined,
  defaultRedirectPath: '/',
  framed: true,
  hideActionButton: false,
  initialTab: undefined,
  loginButtonText: '登录',
  messages: undefined,
  onActionButtonClick: undefined,
  redirectHandler: undefined,
  registerButtonText: '注册',
  registerEnabled: undefined,
  settingsPanelClass: '',
  使用API环境存储: undefined,
})

const route = useRoute()
const router = useRouter()
const settings = 使用设置存储()
const apiEnvironmentStore = props.使用API环境存储?.()
const environmentLoading = ref(false)
const environmentDialogVisible = ref(false)
const registerEnabled = computed(() => props.registerEnabled ?? settings.registerEnabled)
const canSwitchEnvironment = computed(() => apiEnvironmentStore?.canSwitchEnvironment ?? false)
const activeEnvironmentId = computed(() => apiEnvironmentStore?.activeEnvironmentId ?? '')
const environments = computed(() => apiEnvironmentStore?.environments ?? [])
const { refreshing: connectivityRefreshing, refreshConnectivity: 刷新连接性, getSnapshot: 获取快照 } = 使用API环境连接性(environments)
const activeEnvironmentReachable = computed(() => {
  if (!apiEnvironmentStore || !activeEnvironmentId.value) {
    return true
  }
  return 获取快照(activeEnvironmentId.value).status === 'reachable'
})
const showRegisterEntry = computed(() => registerEnabled.value && activeEnvironmentReachable.value)
const {
  activeTab,
  errorMessage,
  isDevMode,
  loading,
  loginForm,
  registerForm,
  clearError,
  handleLogin,
  handleRegister,
  handleDeveloperLogin,
} = 使用认证入口({
  messages: props.messages,
  redirectHandler: props.redirectHandler ?? {
    getRedirectPath: () => typeof route.query.redirect === 'string' ? route.query.redirect : props.defaultRedirectPath,
    navigate: async (path) => router.replace(path),
  },
  registerOptions: {
    isReachable: activeEnvironmentReachable as Ref<boolean>,
    isRegisterEnabled: registerEnabled as Ref<boolean>,
  },
})

watch(
  () => props.initialTab,
  (value) => {
    if (value) {
      activeTab.value = value
    }
  },
  { immediate: true },
)

watch(
  () => props.activeTabResetKey,
  () => {
    if (props.initialTab) {
      activeTab.value = props.initialTab
    }
  },
)

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
  if (!apiEnvironmentStore || id === apiEnvironmentStore.activeEnvironmentId) {
    return
  }
  apiEnvironmentStore.设置活动环境(id)
  clearError()
}

function handleRemoveEnvironment(id: string) {
  if (!apiEnvironmentStore) {
    return
  }
  apiEnvironmentStore.移除环境(id)
}

function handleSubmitEnvironment(payload: { editingId: string | null; name: string; baseUrl: string }) {
  if (!apiEnvironmentStore) {
    return
  }
  environmentLoading.value = true
  try {
    if (payload.editingId) {
      apiEnvironmentStore.更新环境(payload.editingId, payload.name, normalizeBaseUrl(payload.baseUrl))
      return
    }

    apiEnvironmentStore.添加环境(payload.name, normalizeBaseUrl(payload.baseUrl))
  } finally {
    environmentLoading.value = false
  }
}

function getEnvironmentStatus(id: string) {
  return 获取快照(id).status
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
    <div class="auth-entry-panel">
      <div
        v-if="props.hideActionButton !== true
          ? (props.actionButtonLabel ?? (canSwitchEnvironment ? '打开接口环境设置' : undefined)) || $slots.headerActions
          : $slots.headerActions"
        class="auth-entry-panel__header"
      >
        <AppIconButton
          v-if="!props.hideActionButton && (props.actionButtonLabel ?? (canSwitchEnvironment ? '打开接口环境设置' : undefined))"
          class="auth-entry-panel__action-button"
          :disabled="props.actionButtonDisabled || loading || environmentLoading"
          :label="props.actionButtonLabel ?? (canSwitchEnvironment ? '打开接口环境设置' : '')"
          @click="handleActionButtonClick"
        >
          <slot name="action-icon">
            <Setting v-if="props.actionButtonType === 'environment'" aria-hidden="true" />
          </slot>
        </AppIconButton>
        <slot name="headerActions" />
      </div>

      <div class="auth-entry-panel__title">
        <slot name="title">
          <h1 class="page-title">Personal System</h1>
        </slot>
      </div>

      <ElTabs v-if="showRegisterEntry" v-model="activeTab" class="auth-tabs" stretch>
        <ElTabPane label="登录" name="login">
          <ElForm class="auth-form" label-position="top" @submit.prevent="handleLogin">
            <AuthCredentialsFields :form="loginForm" input-class="auth-input" item-class="auth-form-item" />

            <ElAlert v-if="errorMessage" class="auth-error" :closable="false" type="error" :title="errorMessage" />

            <ElButton class="auth-primary-button" type="primary" native-type="submit" :loading="loading">
              {{ props.loginButtonText }}
            </ElButton>

            <div v-if="isDevMode" class="dev-login-block">
              <p class="field-label">开发快捷登录</p>
              <AuthDeveloperLoginButtons
                :actions="props.developerLoginActions"
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

            <ElButton class="auth-primary-button" type="primary" native-type="submit" :loading="loading">
              {{ props.registerButtonText }}
            </ElButton>
          </ElForm>
        </ElTabPane>
      </ElTabs>

      <ElForm v-else class="auth-form auth-form--standalone" label-position="top" @submit.prevent="handleLogin">
        <AuthCredentialsFields :form="loginForm" input-class="auth-input" item-class="auth-form-item" />

        <ElAlert v-if="errorMessage" class="auth-error" :closable="false" type="error" :title="errorMessage" />

        <ElButton class="auth-primary-button" type="primary" native-type="submit" :loading="loading">
          {{ props.loginButtonText }}
        </ElButton>

        <div v-if="isDevMode" class="dev-login-block">
          <p class="field-label">开发快捷登录</p>
          <AuthDeveloperLoginButtons
            :actions="props.developerLoginActions"
            button-class="dev-login-button"
            :loading="loading"
            @login="handleDeveloperLogin"
          />
        </div>
      </ElForm>
    </div>
  </div>

  <Teleport to="body">
    <div v-if="apiEnvironmentStore && canSwitchEnvironment && environmentDialogVisible" class="auth-settings-overlay" @click.self="closeEnvironmentDialog">
      <section :class="['auth-settings-panel', props.settingsPanelClass]" role="dialog" aria-modal="true" aria-label="接口环境设置">
        <ApiEnvironmentManager
          :environments="environments"
          :active-environment-id="activeEnvironmentId"
          :loading="loading || environmentLoading"
          :refreshing="connectivityRefreshing"
          :show-close-button="true"
          create-action-text="新增环境"
          update-action-text="保存地址"
          :get-status="getEnvironmentStatus"
          :on-refresh="刷新连接性"
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

.auth-entry-panel {
  display: grid;
}

.auth-entry-panel__header {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.auth-entry-panel__action-button {
  margin-bottom: 0;
}

.auth-entry-panel__title {
  margin: 0 0 24px;
  text-align: center;
}

.auth-entry-panel__title :deep(.page-title) {
  margin: 0;
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
