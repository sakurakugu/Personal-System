<script setup lang="ts">
import { useApiEnvironmentStore } from '@/shared/stores/api-environment'
import { Connection } from '@element-plus/icons-vue'
import { useAuthStore } from '@personal-system/domain/auth'
import { useApiEnvironmentPage } from '@personal-system/domain/api-environment'
import { ApiEnvironmentManager, SettingsPageShell, SettingsSectionCard } from '@personal-system/ui'

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
  logout: () => auth.logout(),
})
</script>

<template>
  <SettingsPageShell title="接口环境" :icon="Connection">
    <SettingsSectionCard v-if="canSwitchEnvironment" header="环境管理">
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
    </SettingsSectionCard>

    <SettingsSectionCard v-else header="当前状态">
      <div class="settings-api-environment__disabled">
        <strong>当前构建未开启接口环境切换</strong>
        <p>如果后续需要开放多环境能力，再从这里继续扩展即可。</p>
      </div>
    </SettingsSectionCard>
  </SettingsPageShell>
</template>

<style scoped>
.settings-api-environment__disabled {
  display: grid;
  gap: 8px;
  color: var(--text-primary);
}

.settings-api-environment__disabled p {
  margin: 0;
  color: var(--text-tertiary);
}
</style>
