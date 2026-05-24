<script setup lang="ts">
import ProfileEntryCard from '@/modules/个人/components/个人入口卡片.vue'
import { 获取手机角色配置 } from '@/modules/认证/lib/role'
import { 使用主题存储 } from '@/shared/stores/theme'
import { ArrowRightBold, ChatDotRound, Collection, CreditCard, Document, Setting } from '@element-plus/icons-vue'
import { Icon } from '@iconify/vue'
import { 获取API错误消息 } from '@personal-system/api'
import { 使用认证存储 } from '@personal-system/domain/auth'
import { 获取待办列表 } from '@personal-system/domain/todos'
import { 获取我的文章列表 } from '@personal-system/module-articles'
import { 获取我的动态 } from '@personal-system/module-moments'
import { 获取个人资料显示名称 } from '@personal-system/module-profile'
import { UniversalAvatar } from '@personal-system/ui'
import { ElMessage } from 'element-plus'
import { computed, onMounted, ref } from 'vue'

const auth = 使用认证存储()
const theme = 使用主题存储()

const roleProfile = computed(() => 获取手机角色配置(auth.user?.role))
const displayName = computed(() => 获取个人资料显示名称(auth.user))
const profileBio = computed(() => auth.user?.bio?.trim() || '暂无简介')
const roleBadgeClass = computed(() => `role-badge--${auth.user?.role || 'user'}`)
const themeToggleLabel = computed(() => (theme.isDark ? '切换到日间模式' : '切换到夜间模式'))
const themeToggleIcon = computed(() => (
  theme.isDark
    ? 'material-symbols:wb-sunny-outline-rounded'
    : 'material-symbols:dark-mode-outline-rounded'
))
const profileStatsLoading = ref(false)
const profileStats = ref({
  articleCount: 0,
  momentCount: 0,
  todoCount: 0,
})
const profileStatItems = computed(() => [
  { label: '文章', value: profileStats.value.articleCount },
  { label: '动态', value: profileStats.value.momentCount },
  { label: '待办', value: profileStats.value.todoCount },
])

function handleToggleThemeMode() {
  theme.setMode(theme.isDark ? 'light' : 'dark')
}

async function loadProfileStats() {
  profileStatsLoading.value = true
  console.info('[PhoneProfilePage] 开始加载个人统计')
  try {
    const [articleResponse, momentResponse, todos] = await Promise.all([
      获取我的文章列表(1, 1, false),
      获取我的动态(1, 1, false),
      获取待办列表(),
    ])
    profileStats.value = {
      articleCount: articleResponse.total,
      momentCount: momentResponse.total,
      todoCount: todos.length,
    }
    console.info('[PhoneProfilePage] 个人统计加载完成', profileStats.value)
  } catch (error) {
    console.error('[PhoneProfilePage] 个人统计加载失败', error)
    console.warn('[PhoneProfilePage] 个人统计加载失败，保留默认值')
    ElMessage.error(获取API错误消息(error, '加载个人统计失败'))
  } finally {
    profileStatsLoading.value = false
  }
}

onMounted(() => {
  void loadProfileStats()
})

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
] as const
</script>

<template>
  <section class="page profile-page">
    <div class="profile-topbar">
      <button
        class="profile-topbar__action"
        type="button"
        :aria-label="themeToggleLabel"
        :title="themeToggleLabel"
        @click="handleToggleThemeMode"
      >
        <Icon :icon="themeToggleIcon" />
      </button>
      <RouterLink
        class="profile-topbar__action"
        to="/me/settings"
        aria-label="打开设置"
        title="设置"
      >
        <Setting />
      </RouterLink>
    </div>

    <RouterLink class="hero-card hero-card--profile hero-card--link" to="/me/account">
      <UniversalAvatar
        class="hero-card__avatar"
        :src="auth.user?.avatar_url || ''"
        :text="displayName"
        alt="用户头像"
        :size="52"
      />

      <div class="hero-card__content">
        <div class="hero-card__heading">
          <h1 class="page-title">{{ displayName }}</h1>
          <span class="role-badge" :class="roleBadgeClass">{{ roleProfile.badge }}</span>
        </div>
        <p class="hero-card__meta">{{ profileBio }}</p>
      </div>

      <span class="hero-card__arrow">
        <ArrowRightBold />
      </span>
    </RouterLink>

    <section class="profile-stats" :class="{ 'is-loading': profileStatsLoading }" aria-label="个人统计">
      <div
        v-for="item in profileStatItems"
        :key="item.label"
        class="profile-stats__item"
      >
        <strong class="profile-stats__value">{{ item.value }}</strong>
        <span class="profile-stats__label">{{ item.label }}</span>
      </div>
    </section>

    <div class="profile-scroll">
      <section class="profile-section">
        <div class="profile-section__heading">
          <span class="panel-title">共享管理页</span>
        </div>

        <div class="panel-card panel-list">
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
  padding-top: 14px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.hero-card {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 14px;
  padding: 10px 0;
}

.hero-card--profile {
  margin-bottom: 8px;
  flex: 0 0 auto;
}

.hero-card--link {
  color: inherit;
  text-decoration: none;
}

.hero-card__avatar {
  flex: 0 0 auto;
}

.hero-card__content {
  min-width: 0;
}

.hero-card__heading {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  flex-wrap: nowrap;
}

.hero-card__heading .page-title {
  margin: 0;
  min-width: 0;
  font-size: 1.2rem;
  line-height: 1.25;
}

.hero-card__meta {
  margin: 4px 0 0;
  color: var(--text-tertiary);
  font-size: 0.92rem;
  line-height: 1.45;
  word-break: break-word;
}

.hero-card__arrow,
.profile-topbar__action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
}

.hero-card__arrow {
  color: var(--text-tertiary);
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
  margin-bottom: 0px;
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
  padding-top: 8px;
  overflow-y: auto;
  overscroll-behavior-y: contain;
  -webkit-overflow-scrolling: touch;
}

.profile-section {
  display: grid;
  gap: 16px;
}

.profile-stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin-bottom: 8px;
  flex: 0 0 auto;
}

.profile-stats.is-loading {
  opacity: 0.72;
}

.profile-stats__item {
  display: grid;
  justify-items: center;
  gap: 4px;
  min-width: 0;
  padding: 6px 0;
}

.profile-stats__item + .profile-stats__item {
  border-left: 1px solid var(--theme-card-border);
}

.profile-stats__value {
  font-size: 1rem;
  line-height: 1.1;
  color: var(--text-primary);
}

.profile-stats__label {
  color: var(--text-tertiary);
  font-size: 0.78rem;
  line-height: 1;
}

.profile-section__heading {
  display: grid;
  gap: 6px;
}
.role-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 44px;
  min-height: 24px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 0.74rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  white-space: nowrap;
  flex: 0 0 auto;
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
