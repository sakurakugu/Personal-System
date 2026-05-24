<script setup lang="ts">
import { 使用API环境存储 } from '@/shared/stores/api-environment'
import { 使用认证存储 } from '@personal-system/domain/auth'
import { 使用API环境页面 } from '@personal-system/domain/api-environment'
import { ApiEnvironmentManager, PageSectionShell } from '@personal-system/ui'

const auth = 使用认证存储()
const apiEnvironmentStore = 使用API环境存储()

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
} = 使用API环境页面({
  store: apiEnvironmentStore,
  logout: () => auth.登出(),
})
</script>

<template>
  <section class="page">
    <PageSectionShell
      title="接口环境"
      to="/me/settings"
      :show-back="true"
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
      <strong class="section-title">当前构建未开启接口环境切换</strong>
    </section>
  </section>
</template>
