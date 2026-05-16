<script setup lang="ts">
import ProfileSubpageHeader from '@/modules/个人/components/个人子页面标题.vue'
import { useApiEnvironmentStore } from '@/shared/stores/api-environment'
import { useAuthStore } from '@personal-system/domain/auth'
import { useApiEnvironmentPage } from '@personal-system/domain/api-environment'
import { ApiEnvironmentManager } from '@personal-system/ui'

const auth = useAuthStore()
const apiEnvironmentStore = useApiEnvironmentStore()

const {
  environmentLoading,
  canSwitchEnvironment,
  activeEnvironmentId,
  environments,
  connectivityRefreshing,
  refreshConnectivity,
  handleSelectEnvironment,
  handleRemoveEnvironment,
  handleSubmitEnvironment,
  getEnvironmentStatus,
} = useApiEnvironmentPage({
  store: apiEnvironmentStore,
  logout: () => auth.登出(),
})
</script>

<template>
  <section class="page">
    <ProfileSubpageHeader
      title="接口环境"
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
