<script setup lang="ts">
import ApiEnvironmentManager from '@/components/ApiEnvironmentManager.vue'
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@personal-system/domain/auth'
import { useApiEnvironmentStore } from '@/stores/api-environment'
import { getPhoneRoleProfile } from '@/auth/role'
import { useApiEnvironmentConnectivity } from '@/composables/use-api-environment-connectivity'
import { useThemeStore } from '@/stores/theme'

const auth = useAuthStore()
const apiEnvironmentStore = useApiEnvironmentStore()
const theme = useThemeStore()
const router = useRouter()
const loading = ref(false)
const environmentLoading = ref(false)

const canSwitchEnvironment = computed(() => apiEnvironmentStore.canSwitchEnvironment)
const activeEnvironmentId = computed(() => apiEnvironmentStore.activeEnvironmentId)
const activeBaseUrl = computed(() => apiEnvironmentStore.activeBaseUrl)
const roleProfile = computed(() => getPhoneRoleProfile(auth.user?.role))
const environments = computed(() => apiEnvironmentStore.environments)
const themeModes = [
  { value: 'system', label: '跟随系统' },
  { value: 'light', label: '浅色' },
  { value: 'dark', label: '深色' },
] as const
const { refreshing: connectivityRefreshing, refreshConnectivity, getSnapshot } = useApiEnvironmentConnectivity(environments)

async function reloadAfterEnvironmentChange() {
  try {
    await auth.logout()
  } catch {
    // 后端不可达时也要允许本地退出并刷新
  }
  window.location.reload()
}

async function handleSelectEnvironment(id: string) {
  if (id === apiEnvironmentStore.activeEnvironmentId) {
    return
  }
  environmentLoading.value = true
  try {
    apiEnvironmentStore.setActiveEnvironment(id)
    await reloadAfterEnvironmentChange()
  } finally {
    environmentLoading.value = false
  }
}

async function handleRemoveEnvironment(id: string) {
  const removedActive = apiEnvironmentStore.activeEnvironmentId === id
  apiEnvironmentStore.removeEnvironment(id)
  if (removedActive) {
    environmentLoading.value = true
    try {
      await reloadAfterEnvironmentChange()
    } finally {
      environmentLoading.value = false
    }
  }
}

async function handleSubmitEnvironment(payload: { editingId: string | null; name: string; baseUrl: string }) {
  environmentLoading.value = true
  try {
    const currentActiveId = apiEnvironmentStore.activeEnvironmentId
    const currentActiveBaseUrl = activeBaseUrl.value

    if (payload.editingId) {
      const targetId = payload.editingId
      apiEnvironmentStore.updateEnvironment(targetId, payload.name, payload.baseUrl)
      if (targetId === currentActiveId && payload.baseUrl !== currentActiveBaseUrl) {
        await reloadAfterEnvironmentChange()
      }
      return
    }

    apiEnvironmentStore.addEnvironment(payload.name, payload.baseUrl)
    await reloadAfterEnvironmentChange()
  } finally {
    environmentLoading.value = false
  }
}

function getEnvironmentStatus(id: string) {
  return getSnapshot(id).status
}

function handleThemeModeChange(mode: 'light' | 'dark' | 'system') {
  theme.setMode(mode)
}

function handleHueChange(event: globalThis.Event) {
  const target = event.target
  if (!(target instanceof globalThis.HTMLInputElement)) {
    return
  }
  theme.setHue(Number(target.value))
}

async function handleLogout() {
  loading.value = true
  try {
    try {
      await auth.logout()
    } catch {
      // 后端不可达时也要允许本地退出并返回登录页
    }
    await router.replace('/login')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="page">
    <header class="page-header">
      <div>
        <p class="eyebrow">我的</p>
        <h1 class="page-title">账号信息</h1>
      </div>
    </header>

    <div class="stack">
      <section class="panel-card">
        <div class="info-row">
          <span class="info-label">用户名</span>
          <strong>{{ auth.user?.username || '-' }}</strong>
        </div>
        <div class="info-row">
          <span class="info-label">昵称</span>
          <strong>{{ auth.user?.nickname || '未设置' }}</strong>
        </div>
        <div class="info-row">
          <span class="info-label">邮箱</span>
          <strong>{{ auth.user?.email || '-' }}</strong>
        </div>
        <div class="info-row">
          <span class="info-label">角色</span>
          <strong>{{ roleProfile.label }}</strong>
        </div>
      </section>

      <section class="panel-card stack">
        <div>
          <span class="info-label">角色说明</span>
          <strong class="section-title">{{ roleProfile.summary }}</strong>
        </div>
        <div class="capability-list">
          <article v-for="item in roleProfile.capabilities" :key="item.title" class="capability-card">
            <strong>{{ item.title }}</strong>
            <p>{{ item.description }}</p>
          </article>
        </div>
        <p v-if="roleProfile.managementNotice" class="panel-meta panel-note">
          {{ roleProfile.managementNotice }}
        </p>
      </section>

      <section class="panel-card stack">
        <div>
          <span class="info-label">主题设置</span>
          <strong class="section-title">{{ theme.modeLabel }}</strong>
        </div>
        <div class="theme-mode-list">
          <button
            v-for="item in themeModes"
            :key="item.value"
            class="chip-button"
            :class="{ 'chip-button--active': theme.mode === item.value }"
            type="button"
            @click="handleThemeModeChange(item.value)"
          >
            {{ item.label }}
          </button>
        </div>
        <label class="theme-slider-field">
          <span class="info-label">主题主色</span>
          <input
            class="theme-slider"
            type="range"
            min="0"
            max="359"
            :value="theme.hue"
            @input="handleHueChange"
          >
        </label>
        <div class="theme-preview-row">
          <span class="theme-preview theme-preview--primary" />
          <span class="theme-preview theme-preview--soft" />
          <span class="theme-preview theme-preview--card" />
          <span class="panel-meta">当前 Hue：{{ theme.hue }}</span>
        </div>
      </section>

      <section v-if="canSwitchEnvironment" class="panel-card stack">
        <ApiEnvironmentManager
          :environments="environments"
          :active-environment-id="activeEnvironmentId"
          :loading="environmentLoading"
          :refreshing="connectivityRefreshing"
          create-action-text="新增并切换"
          update-action-text="保存修改"
          :get-status="getEnvironmentStatus"
          :on-refresh="refreshConnectivity"
          :on-select="handleSelectEnvironment"
          :on-submit="handleSubmitEnvironment"
          :on-remove="handleRemoveEnvironment"
        />
      </section>

      <button class="primary-button primary-button--danger" type="button" :disabled="loading" @click="handleLogout">
        {{ loading ? '退出中…' : '退出登录' }}
      </button>
    </div>
  </section>
</template>

<style scoped>
.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.info-row + .info-row {
  margin-top: 16px;
}

.info-label {
  color: var(--text-tertiary);
}

.theme-mode-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.theme-slider-field {
  display: grid;
  gap: 10px;
}

.theme-slider {
  width: 100%;
  margin: 0;
  accent-color: var(--el-color-primary);
}

.theme-preview-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.theme-preview {
  width: 22px;
  height: 22px;
  border-radius: 999px;
  border: 1px solid var(--theme-card-border);
}

.theme-preview--primary {
  background: var(--el-color-primary);
}

.theme-preview--soft {
  background: var(--theme-accent-soft);
}

.theme-preview--card {
  background: var(--theme-card-bg);
}
</style>
