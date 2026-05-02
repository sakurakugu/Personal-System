<script setup lang="ts">
import AppIconButton from '@/shared/components/AppIconButton.vue'
import ApiEnvironmentManager from '@/shared/components/ApiEnvironmentManager.vue'
import { ArrowLeftBold, ArrowRightBold } from '@element-plus/icons-vue'
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@personal-system/domain/auth'
import { useApiEnvironmentStore } from '@/shared/stores/api-environment'
import { getPhoneRoleProfile } from '@/modules/auth/lib/role'
import { useApiEnvironmentConnectivity } from '@/shared/composables/use-api-environment-connectivity'
import { type AppTabId } from '@/shared/tab-bar'
import { useTabBarStore } from '@/shared/stores/tab-bar'
import { useThemeStore } from '@/shared/stores/theme'

const auth = useAuthStore()
const apiEnvironmentStore = useApiEnvironmentStore()
const tabBar = useTabBarStore()
const theme = useThemeStore()
const router = useRouter()
const loading = ref(false)
const environmentLoading = ref(false)

const canSwitchEnvironment = computed(() => apiEnvironmentStore.canSwitchEnvironment)
const activeEnvironmentId = computed(() => apiEnvironmentStore.activeEnvironmentId)
const activeBaseUrl = computed(() => apiEnvironmentStore.activeBaseUrl)
const roleProfile = computed(() => getPhoneRoleProfile(auth.user?.role))
const environments = computed(() => apiEnvironmentStore.environments)
const tabBarSettingsItems = computed(() => tabBar.settingsItems)
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

function getTabDescription(item: {
  visible: boolean
  required: boolean
  canHide: boolean
}) {
  if (item.required) {
    return '必选标签，不可隐藏'
  }
  if (item.visible && !item.canHide) {
    return `当前显示，至少保留 ${tabBar.minimumVisibleTabCount} 个`
  }
  return item.visible ? '当前显示，可调整顺序' : '当前隐藏，随时可恢复'
}

function handleMoveTab(id: AppTabId, direction: -1 | 1) {
  tabBar.moveTab(id, direction)
}

function handleToggleTab(id: AppTabId, visible: boolean) {
  tabBar.setTabVisible(id, visible)
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
          <div class="theme-slider-wrapper">
            <div class="theme-slider-track" aria-hidden="true" />
            <input
              class="theme-slider"
              type="range"
              min="0"
              max="359"
              :value="theme.hue"
              @input="handleHueChange"
            >
          </div>
        </label>
        <div class="theme-preview-row">
          <span class="theme-preview theme-preview--primary" />
          <span class="theme-preview theme-preview--soft" />
          <span class="theme-preview theme-preview--card" />
          <span class="panel-meta">当前 Hue：{{ theme.hue }}</span>
        </div>
      </section>

      <section class="panel-card stack">
        <div>
          <span class="info-label">底部导航</span>
          <strong class="section-title">至少保留 {{ tabBar.minimumVisibleTabCount }} 个，“我的”必选</strong>
        </div>
        <div class="tabbar-settings-list">
          <article v-for="item in tabBarSettingsItems" :key="item.id" class="tabbar-settings-item">
            <div class="tabbar-settings-main">
              <span class="tabbar-settings-icon">
                <component :is="item.icon" />
              </span>
              <div class="tabbar-settings-text">
                <strong>{{ item.label }}</strong>
                <span class="panel-meta">{{ getTabDescription(item) }}</span>
              </div>
            </div>
            <div class="tabbar-settings-actions">
              <button
                class="chip-button"
                :class="{ 'chip-button--active': item.visible }"
                type="button"
                :disabled="item.visible ? !item.canHide : !item.canShow"
                @click="handleToggleTab(item.id, !item.visible)"
              >
                {{ item.visible ? '显示中' : '已隐藏' }}
              </button>
              <AppIconButton
                label="左移标签"
                size="sm"
                :disabled="!item.canMoveLeft"
                @click="handleMoveTab(item.id, -1)"
              >
                <ArrowLeftBold />
              </AppIconButton>
              <AppIconButton
                label="右移标签"
                size="sm"
                :disabled="!item.canMoveRight"
                @click="handleMoveTab(item.id, 1)"
              >
                <ArrowRightBold />
              </AppIconButton>
            </div>
          </article>
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

.theme-slider-wrapper {
  --slider-edge-gap: 5px;
  --slider-edge-color: oklch(0.8 0.1 0);
  position: relative;
  width: 100%;
  height: 24px;
  border-radius: 4px;
}

.theme-slider-track {
  position: absolute;
  inset: 0;
  border-radius: 4px;
  background:
    linear-gradient(var(--slider-edge-color), var(--slider-edge-color)) left center / var(--slider-edge-gap) 100% no-repeat,
    var(--color-selection-bar) center / calc(100% - (var(--slider-edge-gap) * 2)) 100% no-repeat,
    linear-gradient(var(--slider-edge-color), var(--slider-edge-color)) right center / var(--slider-edge-gap) 100% no-repeat;
  pointer-events: none;
}

.theme-slider {
  position: absolute;
  top: 0;
  right: var(--slider-edge-gap);
  bottom: 0;
  left: var(--slider-edge-gap);
  width: auto;
  height: 100%;
  margin: 0;
  -webkit-appearance: none;
  appearance: none;
  border-radius: 4px;
  background: transparent;
  outline: none;
  cursor: pointer;
}

.theme-slider::-webkit-slider-runnable-track {
  height: 100%;
  background: transparent;
  border: none;
}

.theme-slider::-webkit-slider-thumb {
  width: 8px;
  height: 16px;
  margin-top: 4px;
  -webkit-appearance: none;
  appearance: none;
  border: none;
  border-radius: 2px;
  background: rgba(255, 255, 255, 0.7);
  box-shadow: none;
}

.theme-slider::-webkit-slider-thumb:hover {
  background: rgba(255, 255, 255, 0.85);
}

.theme-slider::-webkit-slider-thumb:active {
  background: rgba(255, 255, 255, 0.6);
}

.theme-slider::-moz-range-track,
.theme-slider::-moz-range-progress {
  height: 100%;
  background: transparent;
  border: none;
}

.theme-slider::-moz-range-thumb {
  width: 8px;
  height: 16px;
  border: none;
  border-radius: 2px;
  background: rgba(255, 255, 255, 0.7);
  box-shadow: none;
}

.theme-slider::-moz-range-thumb:hover {
  background: rgba(255, 255, 255, 0.85);
}

.theme-slider::-moz-range-thumb:active {
  background: rgba(255, 255, 255, 0.6);
}

.dark .theme-slider-wrapper {
  --slider-edge-color: oklch(0.7 0.1 0);
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

.tabbar-settings-list {
  display: grid;
  gap: 12px;
}

.tabbar-settings-item {
  display: grid;
  gap: 12px;
  padding: 14px 16px;
  border: 1px solid var(--theme-card-border);
  border-radius: 18px;
  background: var(--theme-panel-subtle);
}

.tabbar-settings-main {
  display: flex;
  align-items: center;
  gap: 12px;
}

.tabbar-settings-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 42px;
  height: 42px;
  border-radius: 14px;
  color: var(--theme-accent-strong);
  background: var(--theme-panel-soft);
  border: 1px solid var(--theme-card-border);
}

.tabbar-settings-icon :deep(svg) {
  width: 20px;
  height: 20px;
  color: currentColor;
  fill: currentColor;
}

.tabbar-settings-text {
  min-width: 0;
  display: grid;
  gap: 4px;
}

.tabbar-settings-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
</style>
