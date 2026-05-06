<script setup lang="ts">
import { getPhoneRoleProfile } from '@/modules/auth/lib/role'
import ProfileEntryCard from '@/modules/profile/components/ProfileEntryCard.vue'
import { useApiEnvironmentStore } from '@/shared/stores/api-environment'
import { useThemeStore } from '@/shared/stores/theme'
import { Brush, Connection, Grid, User } from '@element-plus/icons-vue'
import { useAuthStore } from '@personal-system/domain/auth'
import { getProfileDisplayName } from '@personal-system/modules/profile'
import { computed } from 'vue'

const auth = useAuthStore()
const apiEnvironmentStore = useApiEnvironmentStore()
const theme = useThemeStore()

const canSwitchEnvironment = computed(() => apiEnvironmentStore.canSwitchEnvironment)
const roleProfile = computed(() => getPhoneRoleProfile(auth.user?.role))
const displayName = computed(() => getProfileDisplayName(auth.user))
const activeEnvironmentName = computed(() => apiEnvironmentStore.activeEnvironment?.name || '未选择')
const roleBadgeClass = computed(() => `role-badge--${auth.user?.role || 'user'}`)
</script>

<template>
  <section class="page">
    <header class="hero-card hero-card--profile">
      <div class="section-heading">
        <p class="eyebrow">我的</p>
        <span class="role-badge" :class="roleBadgeClass">{{ roleProfile.badge }}</span>
      </div>
      <h1 class="page-title">{{ displayName }}</h1>
      <p class="page-subtitle">{{ roleProfile.summary }}</p>
    </header>

    <div class="stack">
      <div class="stack">
        <ProfileEntryCard
          title="账号资料"
          description="查看用户名、昵称、邮箱、角色说明，并从这里退出登录"
          to="/me/account"
          :icon="User"
          :value="roleProfile.label"
        />

        <ProfileEntryCard
          title="主题设置"
          description="调整浅色、深色、跟随系统，以及当前主题主色"
          to="/me/theme"
          :icon="Brush"
          :value="theme.modeLabel"
        />

        <ProfileEntryCard
          title="底部导航"
          description="控制标签显示与顺序，避免所有入口都挤在一个页面里"
          to="/me/tab-bar"
          :icon="Grid"
        />

        <ProfileEntryCard
          v-if="canSwitchEnvironment"
          title="接口环境"
          description="管理本地开发、线上环境和自定义接口地址"
          to="/me/api-environment"
          :icon="Connection"
          :value="activeEnvironmentName"
        />
      </div>
    </div>
  </section>
</template>

<style scoped>
.hero-card {
  padding: 20px;
  border: 1px solid var(--theme-card-border);
  border-radius: 24px;
  background: var(--theme-card-bg);
  backdrop-filter: blur(14px);
  box-shadow: var(--theme-card-shadow);
}

.hero-card--profile {
  display: grid;
  gap: 10px;
  margin-bottom: 14px;
}

.page-subtitle {
  margin: 12px 0 0;
  color: var(--text-tertiary);
}

.role-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 52px;
  min-height: 32px;
  padding: 0 12px;
  border-radius: 999px;
  font-size: 0.82rem;
  font-weight: 700;
  letter-spacing: 0.06em;
}

.role-badge--user {
  color: var(--theme-accent-strong);
  background: var(--theme-accent-soft);
}

.role-badge--admin {
  color: var(--theme-success-strong);
  background: var(--theme-success-soft);
}

.role-badge--super_admin {
  color: var(--theme-danger-strong);
  background: var(--theme-danger-soft);
}

</style>
