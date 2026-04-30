<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@personal-system/domain/auth'
import { useApiEnvironmentStore } from '@/stores/api-environment'
import { getPhoneRoleProfile } from '@/auth/role'
import { useApiEnvironmentConnectivity } from '@/composables/use-api-environment-connectivity'

const auth = useAuthStore()
const apiEnvironmentStore = useApiEnvironmentStore()
const router = useRouter()
const loading = ref(false)
const environmentLoading = ref(false)
const editingId = ref<string | null>(null)
const form = ref({
  name: '',
  baseUrl: '',
})

const canSwitchEnvironment = computed(() => apiEnvironmentStore.canSwitchEnvironment)
const activeBaseUrl = computed(() => apiEnvironmentStore.activeBaseUrl)
const roleProfile = computed(() => getPhoneRoleProfile(auth.user?.role))
const environments = computed(() => apiEnvironmentStore.environments)
const { refreshing: connectivityRefreshing, refreshConnectivity, getSnapshot } = useApiEnvironmentConnectivity(environments)

function resetForm() {
  editingId.value = null
  form.value = {
    name: '',
    baseUrl: '',
  }
}

function normalizeBaseUrl(value: string) {
  return value.trim().replace(/\/+$/, '')
}

async function reloadAfterEnvironmentChange() {
  await auth.logout()
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

function handleEditEnvironment(id: string) {
  const item = apiEnvironmentStore.environments.find((environment) => environment.id === id)
  if (!item) {
    return
  }
  editingId.value = id
  form.value = {
    name: item.name,
    baseUrl: item.baseUrl,
  }
}

async function handleRemoveEnvironment(id: string) {
  const removedActive = apiEnvironmentStore.activeEnvironmentId === id
  apiEnvironmentStore.removeEnvironment(id)
  if (editingId.value === id) {
    resetForm()
  }
  if (removedActive) {
    environmentLoading.value = true
    try {
      await reloadAfterEnvironmentChange()
    } finally {
      environmentLoading.value = false
    }
  }
}

async function handleSubmitEnvironment() {
  const name = form.value.name.trim()
  const baseUrl = normalizeBaseUrl(form.value.baseUrl)

  if (!name) {
    return
  }
  if (!/^https?:\/\//.test(baseUrl)) {
    return
  }

  environmentLoading.value = true
  try {
    const currentActiveId = apiEnvironmentStore.activeEnvironmentId
    const currentActiveBaseUrl = apiEnvironmentStore.activeBaseUrl

    if (editingId.value) {
      const targetId = editingId.value
      apiEnvironmentStore.updateEnvironment(targetId, name, baseUrl)
      resetForm()
      if (targetId === currentActiveId && baseUrl !== currentActiveBaseUrl) {
        await reloadAfterEnvironmentChange()
      }
      return
    }

    apiEnvironmentStore.addEnvironment(name, baseUrl)
    resetForm()
    await reloadAfterEnvironmentChange()
  } finally {
    environmentLoading.value = false
  }
}

async function handleLogout() {
  loading.value = true
  try {
    await auth.logout()
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

      <section v-if="canSwitchEnvironment" class="panel-card stack">
        <div class="section-heading">
          <div>
            <span class="info-label">接口环境</span>
            <strong class="section-title">当前 {{ activeBaseUrl }}</strong>
          </div>
          <button class="chip-button" type="button" :disabled="environmentLoading || connectivityRefreshing" @click="refreshConnectivity">
            {{ connectivityRefreshing ? '检测中' : '重新检测' }}
          </button>
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
            :disabled="environmentLoading"
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
              <button class="chip-button" type="button" :disabled="environmentLoading" @click="handleEditEnvironment(item.id)">
                编辑
              </button>
              <button
                v-if="item.id.startsWith('custom-')"
                class="chip-button chip-button--danger"
                type="button"
                :disabled="environmentLoading"
                @click="handleRemoveEnvironment(item.id)"
              >
                删除
              </button>
            </div>
          </button>
        </div>

        <div class="stack env-form">
          <label class="field">
            <span class="field-label">{{ editingId ? '修改环境名称' : '新增环境名称' }}</span>
            <input v-model="form.name" class="field-input" placeholder="例如：办公室服务端">
          </label>
          <label class="field">
            <span class="field-label">接口基址</span>
            <input v-model="form.baseUrl" class="field-input" placeholder="http://192.168.1.23:8000/api/v1">
          </label>
          <div class="button-row">
            <button class="primary-button" type="button" :disabled="environmentLoading" @click="handleSubmitEnvironment">
              {{ editingId ? '保存修改' : '新增并切换' }}
            </button>
            <button v-if="editingId" class="ghost-button" type="button" :disabled="environmentLoading" @click="resetForm">
              取消
            </button>
          </div>
        </div>
      </section>

      <button class="primary-button primary-button--danger" type="button" :disabled="loading" @click="handleLogout">
        {{ loading ? '退出中…' : '退出登录' }}
      </button>
    </div>
  </section>
</template>
