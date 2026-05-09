<script setup lang="ts">
import { computed } from 'vue'
import { ElAlert, ElButton, ElForm, ElTabPane, ElTabs } from 'element-plus'
import type { AuthUserRole } from '@personal-system/domain/auth'
import { AppIconButton } from '@personal-system/ui'
import type { DeveloperLoginAction } from '../dev-login'
import AuthCredentialsFields from './AuthCredentialsFields.vue'
import AuthDeveloperLoginButtons from './AuthDeveloperLoginButtons.vue'
import AuthRegisterFields from './AuthRegisterFields.vue'

interface LoginFormModel {
  username: string
  password: string
}

interface RegisterFormModel {
  confirmPassword: string
  email: string
  nickname: string
  password: string
  username: string
}

interface Props {
  activeTab: 'login' | 'register'
  canRegister: boolean
  developerLoginActions: DeveloperLoginAction[]
  errorMessage: string
  isDevMode: boolean
  loading: boolean
  actionButtonDisabled?: boolean
  actionButtonLabel?: string
  loginButtonText?: string
  loginForm: LoginFormModel
  registerButtonText?: string
  registerForm: RegisterFormModel
}

const props = withDefaults(defineProps<Props>(), {
  loginButtonText: '登录',
  registerButtonText: '注册',
})

const emit = defineEmits<{
  'update:activeTab': [value: 'login' | 'register']
  actionButtonClick: []
  developerLogin: [role: AuthUserRole]
  login: []
  register: []
}>()

const activeTabModel = computed({
  get: () => props.activeTab,
  set: (value: 'login' | 'register') => emit('update:activeTab', value),
})
</script>

<template>
  <div class="auth-entry-panel">
    <div v-if="actionButtonLabel || $slots.headerActions" class="auth-entry-panel__header">
      <AppIconButton
        v-if="actionButtonLabel"
        class="auth-entry-panel__action-button"
        :disabled="actionButtonDisabled"
        :label="actionButtonLabel"
        @click="emit('actionButtonClick')"
      >
        <slot name="action-icon" />
      </AppIconButton>
      <slot name="headerActions" />
    </div>

    <div v-if="$slots.title" class="auth-entry-panel__title">
      <slot name="title" />
    </div>

    <ElTabs v-if="canRegister" v-model="activeTabModel" class="auth-tabs" stretch>
      <ElTabPane label="登录" name="login">
        <ElForm class="auth-form" label-position="top" @submit.prevent="emit('login')">
          <AuthCredentialsFields :form="loginForm" input-class="auth-input" item-class="auth-form-item" />

          <ElAlert v-if="errorMessage" class="auth-error" :closable="false" type="error" :title="errorMessage" />

          <ElButton class="auth-primary-button" type="primary" native-type="submit" :loading="loading">
            {{ loginButtonText }}
          </ElButton>

          <div v-if="isDevMode" class="dev-login-block">
            <p class="field-label">开发快捷登录</p>
            <AuthDeveloperLoginButtons
              :actions="developerLoginActions"
              button-class="dev-login-button"
              :loading="loading"
              @login="emit('developerLogin', $event)"
            />
          </div>
        </ElForm>
      </ElTabPane>

      <ElTabPane label="注册" name="register">
        <ElForm class="auth-form" label-position="top" @submit.prevent="emit('register')">
          <AuthRegisterFields :form="registerForm" input-class="auth-input" item-class="auth-form-item" />

          <ElAlert v-if="errorMessage" class="auth-error" :closable="false" type="error" :title="errorMessage" />

          <ElButton class="auth-primary-button" type="primary" native-type="submit" :loading="loading">
            {{ registerButtonText }}
          </ElButton>
        </ElForm>
      </ElTabPane>
    </ElTabs>

    <ElForm v-else class="auth-form auth-form--standalone" label-position="top" @submit.prevent="emit('login')">
      <AuthCredentialsFields :form="loginForm" input-class="auth-input" item-class="auth-form-item" />

      <ElAlert v-if="errorMessage" class="auth-error" :closable="false" type="error" :title="errorMessage" />

      <ElButton class="auth-primary-button" type="primary" native-type="submit" :loading="loading">
        {{ loginButtonText }}
      </ElButton>

      <div v-if="isDevMode" class="dev-login-block">
        <p class="field-label">开发快捷登录</p>
        <AuthDeveloperLoginButtons
          :actions="developerLoginActions"
          button-class="dev-login-button"
          :loading="loading"
          @login="emit('developerLogin', $event)"
        />
      </div>
    </ElForm>
  </div>
</template>

<style scoped>
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
