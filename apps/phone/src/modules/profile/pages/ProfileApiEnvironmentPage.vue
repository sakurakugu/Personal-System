<script setup lang="ts">
import ProfileSubpageHeader from '@/modules/profile/components/ProfileSubpageHeader.vue'
import ApiEnvironmentManager from '@/shared/components/ApiEnvironmentManager.vue'
import { useApiEnvironmentConnectivity } from '@/shared/composables/use-api-environment-connectivity'
import { useApiEnvironmentStore } from '@/shared/stores/api-environment'
import { useAuthStore } from '@personal-system/domain/auth'
import { computed, ref } from 'vue'

const auth = useAuthStore()
const apiEnvironmentStore = useApiEnvironmentStore()
const environmentLoading = ref(false)

const canSwitchEnvironment = computed(() => apiEnvironmentStore.canSwitchEnvironment)
const activeEnvironmentId = computed(() => apiEnvironmentStore.activeEnvironmentId)
const activeBaseUrl = computed(() => apiEnvironmentStore.activeBaseUrl)
const environments = computed(() => apiEnvironmentStore.environments)
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
</script>

<template>
  <section class="page">
    <ProfileSubpageHeader
      eyebrow="接口"
      title="接口环境"
      description="环境切换和连通性检测已经单独分层，避免继续把它和账号、主题、导航混成一页。"
    />

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

    <section v-else class="panel-card stack">
      <div>
        <span class="info-label">当前状态</span>
        <strong class="section-title">当前构建未开启接口环境切换</strong>
      </div>
      <p class="panel-meta">如果后续需要开放多环境能力，再从这里继续扩展即可。</p>
    </section>
  </section>
</template>

<style scoped>
.info-label {
  color: var(--text-tertiary);
}
</style>
