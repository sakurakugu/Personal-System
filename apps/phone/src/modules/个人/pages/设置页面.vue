<script setup lang="ts">
import ProfileEntryCard from '@/modules/个人/components/个人入口卡片.vue'
import { 使用API环境存储 } from '@/shared/stores/api-environment'
import { Brush, Connection, Grid, Monitor } from '@element-plus/icons-vue'
import { 使用认证存储 } from '@personal-system/domain/auth'
import { PageSectionShell } from '@personal-system/ui'
import { computed } from 'vue'

const auth = 使用认证存储()
const apiEnvironmentStore = 使用API环境存储()
const isAuthenticated = computed(() => auth.isAuthenticated)
const canSwitchEnvironment = computed(() => apiEnvironmentStore.canSwitchEnvironment)
const activeEnvironmentName = computed(() => apiEnvironmentStore.activeEnvironment?.name || '未选择')
</script>

<template>
  <section class="page">
    <PageSectionShell
      title="设置"
      to="/me"
      :show-back="true"
    />

    <div class="settings-groups">
      <div v-if="isAuthenticated" class="panel-card panel-list">
        <ProfileEntryCard
          title="登录设备"
          to="/device-sessions"
          :icon="Monitor"
        />
      </div>

      <div class="panel-card panel-list">
        <ProfileEntryCard
          title="主题设置"
          to="/me/theme"
          :icon="Brush"
        />

        <ProfileEntryCard
          title="底部导航"
          to="/me/tab-bar"
          :icon="Grid"
        />
      </div>

      <div v-if="canSwitchEnvironment" class="panel-card panel-list">
        <ProfileEntryCard
          title="接口环境"
          to="/me/api-environment"
          :icon="Connection"
          :value="activeEnvironmentName"
        />
      </div>
    </div>
  </section>
</template>

<style scoped>
.settings-groups {
  display: grid;
  gap: 14px;
}
</style>
