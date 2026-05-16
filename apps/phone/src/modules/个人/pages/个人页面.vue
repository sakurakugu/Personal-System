<script setup lang="ts">
import { 获取手机角色配置 } from '@/modules/认证/lib/role'
import ProfileEntryCard from '@/modules/个人/components/个人入口卡片.vue'
import { 使用API环境存储 } from '@/shared/stores/api-environment'
import { 使用主题存储 } from '@/shared/stores/theme'
import { Brush, ChatDotRound, Collection, Connection, CreditCard, Document, Grid, Monitor, User } from '@element-plus/icons-vue'
import { 使用认证存储 } from '@personal-system/domain/auth'
import { 获取个人资料显示名称 } from '@personal-system/module-profile'
import { computed } from 'vue'

const auth = 使用认证存储()
const apiEnvironmentStore = 使用API环境存储()
const theme = 使用主题存储()

const canSwitchEnvironment = computed(() => apiEnvironmentStore.canSwitchEnvironment)
const roleProfile = computed(() => 获取手机角色配置(auth.user?.role))
const displayName = computed(() => 获取个人资料显示名称(auth.user))
const activeEnvironmentName = computed(() => apiEnvironmentStore.activeEnvironment?.name || '未选择')
const roleBadgeClass = computed(() => `role-badge--${auth.user?.role || 'user'}`)

const managementEntries = [
  {
    title: '文章管理',
    description: '写文章、回收站恢复和本地备份都沿用共享页面',
    to: '/articles',
    icon: Document,
  },
  {
    title: '账单管理',
    description: '账户、分类、流水和固定账单统一在这里维护',
    to: '/bills',
    icon: CreditCard,
  },
  {
    title: '动态',
    description: '草稿自动保存、图片管理和回收站都可直接使用',
    to: '/moments',
    icon: ChatDotRound,
  },
  {
    title: '收藏收纳',
    description: '支持筛选、批量整理，以及转文章、转动态、转待办',
    to: '/collections',
    icon: Collection,
  },
  {
    title: '登录设备',
    description: '查看原生设备会话，并单独或批量吊销',
    to: '/device-sessions',
    icon: Monitor,
  },
  {
    title: '账户信息',
    description: '进入完整资料页，修改头像、密码和安全信息',
    to: '/me/account-info',
    icon: User,
  },
] as const
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

      <section class="panel-card profile-section">
        <div class="profile-section__heading">
          <span class="panel-title">共享管理页</span>
          <strong class="section-title">已复用窄屏适配后的后台页面</strong>
        </div>

        <div class="stack">
          <ProfileEntryCard
            v-for="entry in managementEntries"
            :key="entry.to"
            :title="entry.title"
            :description="entry.description"
            :to="entry.to"
            :icon="entry.icon"
          />
        </div>
      </section>
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

.profile-section {
  display: grid;
  gap: 16px;
}

.profile-section__heading {
  display: grid;
  gap: 6px;
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
