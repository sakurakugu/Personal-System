<script setup lang="ts">
import { developerLoginActions } from '@/auth/dev-login'
import { useApiEnvironmentConnectivity } from '@/composables/use-api-environment-connectivity'
import { useApiEnvironmentStore } from '@/stores/api-environment'
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
const editingEnvironmentId = ref<string | null>(null)
const environmentForm = ref({
  name: '',
  baseUrl: '',
})
const registerEnabled = computed(() => settings.registerEnabled)
const canSwitchEnvironment = computed(() => apiEnvironmentStore.canSwitchEnvironment)
const activeEnvironmentId = computed(() => apiEnvironmentStore.activeEnvironmentId)
const activeBaseUrl = computed(() => apiEnvironmentStore.activeBaseUrl)
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

function resetEnvironmentForm() {
  editingEnvironmentId.value = null
  environmentForm.value = {
    name: '',
    baseUrl: '',
  }
}

function openEnvironmentDialog() {
  environmentDialogVisible.value = true
}

function closeEnvironmentDialog() {
  environmentDialogVisible.value = false
  if (editingEnvironmentId.value) {
    resetEnvironmentForm()
  }
}

function handleSelectEnvironment(id: string) {
  if (id === apiEnvironmentStore.activeEnvironmentId) {
    return
  }
  apiEnvironmentStore.setActiveEnvironment(id)
  errorMessage.value = ''
}

function handleEditEnvironment(id: string) {
  const item = apiEnvironmentStore.environments.find((environment) => environment.id === id)
  if (!item) {
    return
  }
  editingEnvironmentId.value = id
  environmentForm.value = {
    name: item.name,
    baseUrl: item.baseUrl,
  }
}

function handleRemoveEnvironment(id: string) {
  apiEnvironmentStore.removeEnvironment(id)
  if (editingEnvironmentId.value === id) {
    resetEnvironmentForm()
  }
}

function handleSubmitEnvironment() {
  const name = environmentForm.value.name.trim()
  const baseUrl = normalizeBaseUrl(environmentForm.value.baseUrl)

  if (!name) {
    return
  }
  if (!/^https?:\/\//.test(baseUrl)) {
    return
  }

  environmentLoading.value = true
  try {
    if (editingEnvironmentId.value) {
      apiEnvironmentStore.updateEnvironment(editingEnvironmentId.value, name, baseUrl)
      resetEnvironmentForm()
      return
    }

    apiEnvironmentStore.addEnvironment(name, baseUrl)
    resetEnvironmentForm()
  } finally {
    environmentLoading.value = false
  }
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
        <button
          v-if="canSwitchEnvironment"
          class="icon-button auth-settings-button"
          type="button"
          :disabled="loading || environmentLoading"
          aria-label="打开接口环境设置"
          @click="openEnvironmentDialog"
        >
          <Setting aria-hidden="true" />
        </button>
      </div>
      <div class="auth-card__title" :class="{ 'auth-card__title--compact-top': canSwitchEnvironment }">
        <h1 class="page-title">Personal System</h1>
      </div>

      <div v-if="canSwitchEnvironment && environmentDialogVisible" class="auth-settings-overlay" @click.self="closeEnvironmentDialog">
        <section class="auth-settings-panel stack" role="dialog" aria-modal="true" aria-label="接口环境设置">
          <div class="section-heading">
            <div>
              <span class="field-label">接口环境</span>
              <strong class="section-title">当前 {{ activeBaseUrl }}</strong>
            </div>
            <div class="auth-settings-actions">
              <button class="chip-button" type="button" :disabled="loading || environmentLoading || connectivityRefreshing" @click="refreshConnectivity">
                {{ connectivityRefreshing ? '检测中' : '重新检测' }}
              </button>
              <button class="chip-button" type="button" :disabled="loading || environmentLoading" @click="closeEnvironmentDialog">
                关闭
              </button>
            </div>
          </div>

          <div class="stack">
            <button
              v-for="item in environments"
              :key="item.id"
              class="env-card"
              :class="{
                'env-card--active': item.id === apiEnvironmentStore.activeEnvironmentId,
                'env-card--reachable': getSnapshot(item.id).status === 'reachable',
                'env-card--unreachable': getSnapshot(item.id).status === 'unreachable',
              }"
              type="button"
              :disabled="loading || environmentLoading"
              @click="handleSelectEnvironment(item.id)"
            >
              <div class="env-card__content">
                <strong>{{ item.name }}</strong>
                <span class="env-card__url">{{ item.baseUrl }}</span>
                <span class="env-card__status" :class="`env-card__status--${getSnapshot(item.id).status}`">
                  <span class="env-card__status-dot" />
                  {{ getSnapshot(item.id).message }}
                </span>
              </div>
              <div class="env-card__actions" @click.stop>
                <button class="chip-button" type="button" :disabled="loading || environmentLoading" @click="handleEditEnvironment(item.id)">
                  编辑
                </button>
                <button
                  v-if="item.id.startsWith('custom-')"
                  class="chip-button chip-button--danger"
                  type="button"
                  :disabled="loading || environmentLoading"
                  @click="handleRemoveEnvironment(item.id)"
                >
                  删除
                </button>
              </div>
            </button>
          </div>

          <div class="stack env-form">
            <label class="field">
              <span class="field-label">{{ editingEnvironmentId ? '修改环境名称' : '新增环境名称' }}</span>
              <input v-model="environmentForm.name" class="field-input" placeholder="例如：办公室服务端">
            </label>
            <label class="field">
              <span class="field-label">接口基址</span>
              <input v-model="environmentForm.baseUrl" class="field-input" placeholder="http://192.168.1.23:8000/api/v1">
            </label>
            <div class="button-row">
              <button class="ghost-button" type="button" :disabled="loading || environmentLoading" @click="handleSubmitEnvironment">
                {{ editingEnvironmentId ? '保存地址' : '新增环境' }}
              </button>
              <button
                v-if="editingEnvironmentId"
                class="ghost-button"
                type="button"
                :disabled="loading || environmentLoading"
                @click="resetEnvironmentForm"
              >
                取消
              </button>
            </div>
          </div>
        </section>
      </div>

      <template v-if="showRegisterEntry">
        <div class="auth-tabs" role="tablist" aria-label="登录注册切换">
          <button
            class="auth-tab"
            :class="{ 'auth-tab--active': activeTab === 'login' }"
            type="button"
            role="tab"
            :aria-selected="activeTab === 'login'"
            @click="activeTab = 'login'"
          >
            登录
          </button>
          <button
            class="auth-tab"
            :class="{ 'auth-tab--active': activeTab === 'register' }"
            type="button"
            role="tab"
            :aria-selected="activeTab === 'register'"
            @click="activeTab = 'register'"
          >
            注册
          </button>
        </div>

        <form v-if="activeTab === 'login'" class="auth-form" @submit.prevent="handleSubmit">
          <label class="field">
            <span class="field-label">用户名</span>
            <input v-model="loginForm.username" class="field-input" autocomplete="username" placeholder="请输入用户名">
          </label>

          <label class="field">
            <span class="field-label">密码</span>
            <input v-model="loginForm.password" class="field-input" type="password" autocomplete="current-password" placeholder="请输入密码">
          </label>

          <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>

          <button class="primary-button" type="submit" :disabled="loading">
            {{ loading ? '登录中…' : '登录' }}
          </button>

          <div v-if="isDevMode" class="dev-login-block">
            <p class="field-label">开发快捷登录</p>
            <div class="dev-login-row">
              <button
                v-for="action in developerLoginActions"
                :key="action.role"
                class="ghost-button dev-login-button"
                type="button"
                :disabled="loading"
                @click="handleDeveloperLogin(action.role)"
              >
                {{ action.label }}
              </button>
            </div>
          </div>
        </form>

        <form v-else class="auth-form" @submit.prevent="handleRegister">
          <label class="field">
            <span class="field-label">用户名</span>
            <input v-model="registerForm.username" class="field-input" autocomplete="username" placeholder="至少 2 个字符">
          </label>

          <label class="field">
            <span class="field-label">昵称</span>
            <input v-model="registerForm.nickname" class="field-input" placeholder="用于展示，可选">
          </label>

          <label class="field">
            <span class="field-label">邮箱</span>
            <input v-model="registerForm.email" class="field-input" autocomplete="email" placeholder="your@email.com">
          </label>

          <label class="field">
            <span class="field-label">密码</span>
            <input v-model="registerForm.password" class="field-input" type="password" autocomplete="new-password" placeholder="至少 6 位">
          </label>

          <label class="field">
            <span class="field-label">确认密码</span>
            <input v-model="registerForm.confirmPassword" class="field-input" type="password" autocomplete="new-password" placeholder="再次输入密码">
          </label>

          <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>

          <button class="primary-button" type="submit" :disabled="loading">
            {{ loading ? '注册中…' : '注册' }}
          </button>
        </form>
      </template>

      <form v-else class="auth-form" @submit.prevent="handleSubmit">
        <label class="field">
          <span class="field-label">用户名</span>
          <input v-model="loginForm.username" class="field-input" autocomplete="username" placeholder="请输入用户名">
        </label>

        <label class="field">
          <span class="field-label">密码</span>
          <input v-model="loginForm.password" class="field-input" type="password" autocomplete="current-password" placeholder="请输入密码">
        </label>

        <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>

        <button class="primary-button" type="submit" :disabled="loading">
          {{ loading ? '登录中…' : '登录' }}
        </button>

        <div v-if="isDevMode" class="dev-login-block">
          <p class="field-label">开发快捷登录</p>
          <div class="dev-login-row">
            <button
              v-for="action in developerLoginActions"
              :key="action.role"
              class="ghost-button dev-login-button"
              type="button"
              :disabled="loading"
              @click="handleDeveloperLogin(action.role)"
            >
              {{ action.label }}
            </button>
          </div>
        </div>
      </form>
    </div>
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
  border: 1px solid rgba(202, 138, 4, 0.12);
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.84);
  backdrop-filter: blur(14px);
  box-shadow: 0 20px 40px rgba(120, 53, 15, 0.08);
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
  margin-top: 0px;
}

.auth-card__title .page-title {
  margin: 0;
}

.auth-card__header .icon-button {
  grid-column: 3;
  justify-self: end;
}

.auth-settings-button,
.icon-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
  width: 42px;
  height: 42px;
  border: 1px solid rgba(180, 83, 9, 0.14);
  border-radius: 14px;
  color: #92400e;
  background: rgba(255, 247, 237, 0.92);
  cursor: pointer;
}

.icon-button:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.icon-button svg {
  width: 20px;
  height: 20px;
  fill: currentColor;
}

.auth-settings-overlay {
  position: fixed;
  inset: 0;
  z-index: 20;
  display: flex;
  align-items: flex-end;
  padding: 20px 12px;
  background: rgba(17, 24, 39, 0.4);
  backdrop-filter: blur(10px);
}

.auth-settings-panel {
  width: min(100%, 520px);
  max-height: min(80vh, 720px);
  margin: 0 auto;
  overflow: auto;
  border: 1px solid rgba(202, 138, 4, 0.12);
  border-radius: 28px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 24px 48px rgba(17, 24, 39, 0.18);
}

.auth-settings-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
}

.auth-form {
  display: grid;
  gap: 14px;
  margin-top: 18px;
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
  padding-left: 10px;
  padding-right: 10px;
  font-size: 0.88rem;
}

.auth-tabs {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0;
  margin-top: 18px;
  padding: 4px;
  border: 1px solid rgba(180, 83, 9, 0.12);
  border-radius: 18px;
  background: rgba(255, 247, 237, 0.82);
}

.auth-tab {
  min-height: 44px;
  border: 0;
  border-radius: 14px;
  color: #92400e;
  background: transparent;
  cursor: pointer;
  transition: background-color 0.18s ease, color 0.18s ease, box-shadow 0.18s ease;
}

.auth-tab--active {
  color: #fff;
  background: linear-gradient(135deg, #d97706 0%, #b45309 100%);
  box-shadow: 0 10px 20px rgba(180, 83, 9, 0.18);
}

@media (min-width: 720px) {
  .auth-settings-overlay {
    align-items: center;
  }
}
</style>
