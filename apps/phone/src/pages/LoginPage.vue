<script setup lang="ts">
import { developerLoginActions } from '@/auth/dev-login'
import { useApiEnvironmentConnectivity } from '@/composables/use-api-environment-connectivity'
import { useApiEnvironmentStore } from '@/stores/api-environment'
import { Setting } from '@element-plus/icons-vue'
import type { AuthUserRole } from '@personal-system/domain/auth'
import { isDeveloperLoginEnabled, useAuthStore } from '@personal-system/domain/auth'
import { useSettingsStore } from '@personal-system/domain/system'
import { computed, reactive, ref } from 'vue'
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
const activeBaseUrl = computed(() => apiEnvironmentStore.activeBaseUrl)
const environments = computed(() => apiEnvironmentStore.environments)
const { refreshing: connectivityRefreshing, refreshConnectivity, getSnapshot } = useApiEnvironmentConnectivity(environments)

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
        <div>
          <p class="eyebrow">手机端</p>
          <h1 class="page-title">登录 Personal System</h1>
          <p class="page-subtitle">手机端已经接入共享公共设置，可按后台配置决定是否开放注册。</p>
        </div>
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

      <div v-if="registerEnabled" class="auth-tabs">
        <button
          class="auth-tab"
          :class="{ 'auth-tab--active': activeTab === 'login' }"
          type="button"
          @click="activeTab = 'login'"
        >
          登录
        </button>
        <button
          class="auth-tab"
          :class="{ 'auth-tab--active': activeTab === 'register' }"
          type="button"
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
    </div>
  </section>
</template>
