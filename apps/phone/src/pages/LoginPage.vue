<script setup lang="ts">
import { developerLoginActions } from '@/auth/dev-login'
import AppIconButton from '@/components/AppIconButton.vue'
import ApiEnvironmentManager from '@/components/ApiEnvironmentManager.vue'
import { useApiEnvironmentConnectivity } from '@/composables/use-api-environment-connectivity'
import { useApiEnvironmentStore } from '@/stores/api-environment'
import { ElAlert, ElButton, ElForm, ElFormItem, ElInput, ElTabPane, ElTabs } from 'element-plus'
import { Setting } from '@element-plus/icons-vue'
import type { AuthUserRole } from '@personal-system/domain/auth'
import { isDeveloperLoginEnabled, useAuthStore } from '@personal-system/domain/auth'
import { useSettingsStore } from '@personal-system/domain/system'
import { computed, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const auth = useAuthStore()
const settings = useSettingsStore()
const apiEnvironmentStore = useApiEnvironmentStore()
const route = useRoute()
const router = useRouter()
const isDevMode = isDeveloperLoginEnabled()

const activeTab = ref<'login' | 'register'>('login')
const loginForm = reactive({
  username: '',
  password: '',
})
const registerForm = reactive({
  username: '',
  nickname: '',
  email: '',
  password: '',
  confirmPassword: '',
})
const errorMessage = ref('')
const loading = ref(false)
const environmentLoading = ref(false)
const environmentDialogVisible = ref(false)
const registerEnabled = computed(() => settings.registerEnabled)
const canSwitchEnvironment = computed(() => apiEnvironmentStore.canSwitchEnvironment)
const activeEnvironmentId = computed(() => apiEnvironmentStore.activeEnvironmentId)
const environments = computed(() => apiEnvironmentStore.environments)
const { refreshing: connectivityRefreshing, refreshConnectivity, getSnapshot } = useApiEnvironmentConnectivity(environments)
const activeEnvironmentReachable = computed(() => getSnapshot(activeEnvironmentId.value).status === 'reachable')
const showRegisterEntry = computed(() => registerEnabled.value && activeEnvironmentReachable.value)

watch(
  showRegisterEntry,
  (enabled) => {
    if (!enabled && activeTab.value !== 'login') {
      activeTab.value = 'login'
    }
  },
  { immediate: true },
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
  if (id === apiEnvironmentStore.activeEnvironmentId) {
    return
  }
  apiEnvironmentStore.setActiveEnvironment(id)
  errorMessage.value = ''
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

async function handleSubmit() {
  errorMessage.value = ''
  loading.value = true

  try {
    await auth.login(loginForm.username, loginForm.password)
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/'
    await router.replace(redirect)
  } catch (error: any) {
    errorMessage.value = error?.response?.data?.detail || '登录失败，请检查用户名和密码'
  } finally {
    loading.value = false
  }
}

async function handleDeveloperLogin(role: AuthUserRole) {
  errorMessage.value = ''
  loading.value = true

  try {
    await auth.developerLogin(role)
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/'
    await router.replace(redirect)
  } catch (error: any) {
    errorMessage.value = error?.response?.data?.detail || '开发者登录失败'
  } finally {
    loading.value = false
  }
}

async function handleRegister() {
  if (!activeEnvironmentReachable.value) {
    errorMessage.value = '未连接服务器'
    return
  }
  if (!registerEnabled.value) {
    errorMessage.value = '当前未开放注册'
    return
  }
  if (registerForm.password !== registerForm.confirmPassword) {
    errorMessage.value = '两次输入的密码不一致'
    return
  }

  errorMessage.value = ''
  loading.value = true

  try {
    await auth.register(
      registerForm.username,
      registerForm.email,
      registerForm.password,
      registerForm.nickname.trim() || undefined,
    )
    activeTab.value = 'login'
    loginForm.username = registerForm.username
    registerForm.username = ''
    registerForm.nickname = ''
    registerForm.email = ''
    registerForm.password = ''
    registerForm.confirmPassword = ''
  } catch (error: any) {
    errorMessage.value = error?.response?.data?.detail || '注册失败，请检查输入内容'
  } finally {
    loading.value = false
  }
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
            <ElForm class="auth-form" label-position="top" @submit.prevent="handleSubmit">
              <ElFormItem label="用户名" class="auth-form-item">
                <ElInput
                  v-model="loginForm.username"
                  class="auth-input"
                  autocomplete="username"
                  placeholder="请输入用户名"
                  clearable
                />
              </ElFormItem>

              <ElFormItem label="密码" class="auth-form-item">
                <ElInput
                  v-model="loginForm.password"
                  class="auth-input"
                  type="password"
                  autocomplete="current-password"
                  placeholder="请输入密码"
                  show-password
                />
              </ElFormItem>

              <ElAlert v-if="errorMessage" class="auth-error" :closable="false" type="error" :title="errorMessage" />

              <ElButton class="auth-primary-button" type="primary" native-type="submit" :loading="loading">登录</ElButton>

              <div v-if="isDevMode" class="dev-login-block">
                <p class="field-label">开发快捷登录</p>
                <div class="dev-login-row">
                  <ElButton
                    v-for="action in developerLoginActions"
                    :key="action.role"
                    class="dev-login-button"
                    plain
                    :loading="loading"
                    @click="handleDeveloperLogin(action.role)"
                  >
                    {{ action.label }}
                  </ElButton>
                </div>
              </div>
            </ElForm>
          </ElTabPane>

          <ElTabPane label="注册" name="register">
            <ElForm class="auth-form" label-position="top" @submit.prevent="handleRegister">
              <ElFormItem label="用户名" class="auth-form-item">
                <ElInput
                  v-model="registerForm.username"
                  class="auth-input"
                  autocomplete="username"
                  placeholder="至少 2 个字符"
                  clearable
                />
              </ElFormItem>

              <ElFormItem label="昵称" class="auth-form-item">
                <ElInput v-model="registerForm.nickname" class="auth-input" placeholder="用于展示，可选" clearable />
              </ElFormItem>

              <ElFormItem label="邮箱" class="auth-form-item">
                <ElInput
                  v-model="registerForm.email"
                  class="auth-input"
                  autocomplete="email"
                  placeholder="your@email.com"
                  clearable
                />
              </ElFormItem>

              <ElFormItem label="密码" class="auth-form-item">
                <ElInput
                  v-model="registerForm.password"
                  class="auth-input"
                  type="password"
                  autocomplete="new-password"
                  placeholder="至少 6 位"
                  show-password
                />
              </ElFormItem>

              <ElFormItem label="确认密码" class="auth-form-item">
                <ElInput
                  v-model="registerForm.confirmPassword"
                  class="auth-input"
                  type="password"
                  autocomplete="new-password"
                  placeholder="再次输入密码"
                  show-password
                />
              </ElFormItem>

              <ElAlert v-if="errorMessage" class="auth-error" :closable="false" type="error" :title="errorMessage" />

              <ElButton class="auth-primary-button" type="primary" native-type="submit" :loading="loading">注册</ElButton>
            </ElForm>
          </ElTabPane>
        </ElTabs>
      </template>

      <ElForm v-else class="auth-form auth-form--standalone" label-position="top" @submit.prevent="handleSubmit">
        <ElFormItem label="用户名" class="auth-form-item">
          <ElInput
            v-model="loginForm.username"
            class="auth-input"
            autocomplete="username"
            placeholder="请输入用户名"
            clearable
          />
        </ElFormItem>

        <ElFormItem label="密码" class="auth-form-item">
          <ElInput
            v-model="loginForm.password"
            class="auth-input"
            type="password"
            autocomplete="current-password"
            placeholder="请输入密码"
            show-password
          />
        </ElFormItem>

        <ElAlert v-if="errorMessage" class="auth-error" :closable="false" type="error" :title="errorMessage" />

        <ElButton class="auth-primary-button" type="primary" native-type="submit" :loading="loading">登录</ElButton>

        <div v-if="isDevMode" class="dev-login-block">
          <p class="field-label">开发快捷登录</p>
          <div class="dev-login-row">
            <ElButton
              v-for="action in developerLoginActions"
              :key="action.role"
              class="dev-login-button"
              plain
              :loading="loading"
              @click="handleDeveloperLogin(action.role)"
            >
              {{ action.label }}
            </ElButton>
          </div>
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
  gap: 14px;
  margin-top: 12px;
}

.auth-form--standalone {
  margin-top: 18px;
}

.auth-form-item {
  margin-bottom: 0;
}

.auth-form :deep(.el-form-item__label) {
  padding-bottom: 8px;
  line-height: 1.3;
  font-size: 0.9rem;
  color: var(--theme-accent-strong);
}

.auth-input {
  width: 100%;
}

.auth-input :deep(.el-input__wrapper) {
  padding: 0 16px;
  border-radius: 16px;
  background: var(--theme-input-bg);
  box-shadow: 0 0 0 1px var(--theme-input-border) inset;
}

.auth-input :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px var(--theme-input-border-hover) inset;
}

.auth-input :deep(.el-input__wrapper.is-focus) {
  box-shadow:
    0 0 0 1px var(--el-color-primary) inset,
    0 0 0 3px var(--theme-focus-ring);
}

.auth-input :deep(.el-input__inner) {
  height: 48px;
  color: var(--text-primary);
}

.auth-input :deep(.el-input__inner::placeholder) {
  color: var(--text-quaternary);
}

.auth-input :deep(.el-input__suffix-inner) {
  gap: 8px;
}

.auth-input :deep(.el-input__clear),
.auth-input :deep(.el-input__password) {
  color: color-mix(in srgb, var(--theme-accent-strong) 70%, transparent);
}

.auth-input :deep(.el-input__clear:hover),
.auth-input :deep(.el-input__password:hover) {
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
  margin-top: 2px;
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

.dev-login-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.dev-login-button {
  min-height: 44px;
  margin: 0;
  padding-left: 10px;
  padding-right: 10px;
  font-size: 0.88rem;
  border-radius: 14px;
  color: var(--theme-accent-strong);
  border-color: var(--theme-card-border);
  background: var(--theme-panel-soft);
}

.auth-tabs {
  margin-top: 18px;
}

.auth-tabs :deep(.el-tabs__header) {
  margin: 0;
}

.auth-tabs :deep(.el-tabs__nav-wrap) {
  padding: 4px;
  border: 1px solid var(--theme-card-border);
  border-radius: 18px;
  background: var(--theme-panel-subtle);
}

.auth-tabs :deep(.el-tabs__nav-wrap::after) {
  display: none;
}

.auth-tabs :deep(.el-tabs__nav) {
  width: 100%;
  gap: 4px;
}

.auth-tabs :deep(.el-tabs__item) {
  height: 44px;
  border-radius: 14px;
  color: var(--theme-accent-strong);
  font-size: 0.96rem;
}

.auth-tabs :deep(.el-tabs__active-bar) {
  display: none;
}

.auth-tabs :deep(.el-tabs__item.is-active) {
  color: #fff;
  background: var(--theme-accent-gradient);
  box-shadow: 0 10px 20px color-mix(in srgb, var(--el-color-primary) 26%, transparent);
}

.auth-tabs :deep(.el-tab-pane) {
  padding-top: 14px;
}
</style>
