<script setup lang="ts">
import { 获取手机角色配置 } from '@/modules/认证/lib/role'
import ProfileEntryCard from '@/modules/个人/components/个人入口卡片.vue'
import { 使用API环境存储 } from '@/shared/stores/api-environment'
import { 使用主题存储 } from '@/shared/stores/theme'
import { ArrowRightBold, Brush, ChatDotRound, Collection, Connection, CreditCard, Document, Grid, Monitor, User } from '@element-plus/icons-vue'
import { Icon } from '@iconify/vue'
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
const themeToggleLabel = computed(() => (theme.isDark ? '切换到日间模式' : '切换到夜间模式'))
const themeToggleIcon = computed(() => (
  theme.isDark
    ? 'material-symbols:wb-sunny-outline-rounded'
    : 'material-symbols:dark-mode-outline-rounded'
))

function handleToggleThemeMode() {
  theme.setMode(theme.isDark ? 'light' : 'dark')
}

const managementEntries = [
  {
    title: '文章管理',
    to: '/articles',
    icon: Document,
  },
  {
    title: '账单管理',
    to: '/bills',
    icon: CreditCard,
  },
  {
    title: '动态',
    to: '/moments',
    icon: ChatDotRound,
  },
  {
    title: '收藏收纳',
    to: '/collections',
    icon: Collection,
  },
  {
    title: '登录设备',
    to: '/device-sessions',
    icon: Monitor,
  },
  {
    title: '账户信息',
    to: '/me/account-info',
    icon: User,
  },
] as const
</script>

<template>
  <section class="page profile-page">
    <div class="profile-topbar">
      <RouterLink
        class="profile-topbar__action"
        to="/me/theme"
        :aria-label="`主题设置，当前${theme.modeLabel}`"
        :title="`主题设置（${theme.modeLabel}）`"
      >
        <Brush />
      </RouterLink>
      <button
        class="profile-topbar__action"
        type="button"
        :aria-label="themeToggleLabel"
        :title="themeToggleLabel"
        @click="handleToggleThemeMode"
      >
        <Icon :icon="themeToggleIcon" />
      </button>
    </div>

    <RouterLink class="hero-card hero-card--profile hero-card--link" to="/me/account">
      <div class="section-heading">
        <p class="eyebrow">我的</p>
        <span class="role-badge" :class="roleBadgeClass">{{ roleProfile.badge }}</span>
      </div>
      <div class="hero-card__main">
        <div class="hero-card__content">
          <h1 class="page-title">{{ displayName }}</h1>
          <span class="hero-card__meta">点击查看账号资料</span>
        </div>
        <span class="hero-card__arrow">
          <ArrowRightBold />
        </span>
      </div>
    </RouterLink>

    <div class="profile-scroll">
      <div class="stack">
        <ProfileEntryCard
          title="底部导航"
          to="/me/tab-bar"
          :icon="Grid"
        />

        <ProfileEntryCard
          v-if="canSwitchEnvironment"
          title="接口环境"
          to="/me/api-environment"
          :icon="Connection"
          :value="activeEnvironmentName"
        />
      </div>

      <section class="panel-card profile-section">
        <div class="profile-section__heading">
          <span class="panel-title">共享管理页</span>
        </div>

        <div class="stack">
          <ProfileEntryCard
            v-for="entry in managementEntries"
            :key="entry.to"
            :title="entry.title"
            :to="entry.to"
            :icon="entry.icon"
          />
        </div>
      </section>
    </div>
  </section>
</template>

<style scoped>
.profile-page {
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

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
  flex: 0 0 auto;
}

.hero-card--link {
  color: inherit;
  text-decoration: none;
}

.hero-card__main {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.hero-card__content {
  min-width: 0;
}

.hero-card__meta {
  display: inline-block;
  margin-top: 8px;
  color: var(--text-tertiary);
  font-size: 0.92rem;
}

.hero-card__arrow,
.profile-topbar__action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
}

.hero-card__arrow {
  width: 40px;
  height: 40px;
  border-radius: 14px;
  color: var(--text-tertiary);
  background: var(--theme-panel-soft);
  border: 1px solid var(--theme-card-border);
}

.hero-card__arrow :deep(svg),
.profile-topbar__action :deep(svg) {
  width: 18px;
  height: 18px;
  color: currentColor;
  fill: currentColor;
}

.profile-topbar {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-bottom: 14px;
  flex: 0 0 auto;
}

.profile-topbar__action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 42px;
  height: 42px;
  padding: 0;
  border-radius: 14px;
  color: var(--theme-accent-strong);
  background: var(--theme-panel-soft);
  border: 1px solid var(--theme-card-border);
  text-decoration: none;
  cursor: pointer;
}

.profile-scroll {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overscroll-behavior-y: contain;
  -webkit-overflow-scrolling: touch;
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
