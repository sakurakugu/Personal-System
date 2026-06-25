<script setup lang="ts">
import ProfileEntryCard from '@/modules/个人/components/个人入口卡片.vue'
import { 获取手机角色配置 } from '@/modules/认证/lib/role'
import { 使用标签栏存储 } from '@/shared/stores/tab-bar'
import { 使用主题存储 } from '@/shared/stores/theme'
import { APP_TAB_DEFINITION_MAP, type AppTabId } from '@/shared/tab-bar'
import { ArrowRightBold, Iphone, Setting } from '@element-plus/icons-vue'
import { Icon } from '@iconify/vue'
import { 获取API错误消息 } from '@personal-system/api'
import { 使用登录门禁存储, 使用认证存储 } from '@personal-system/domain/auth'
import { 获取待办列表 } from '@personal-system/domain/todos'
import { 获取我的文章列表 } from '@personal-system/module-articles'
import { 获取我的动态 } from '@personal-system/module-moments'
import { 获取个人资料显示名称 } from '@personal-system/module-profile'
import { UniversalAvatar } from '@personal-system/ui'
import { ElMessage } from 'element-plus'
import { computed, onMounted, ref } from 'vue'

const auth = 使用认证存储()
const loginGate = 使用登录门禁存储()
const tabBar = 使用标签栏存储()
const theme = 使用主题存储()

const isAuthenticated = computed(() => auth.isAuthenticated)
const roleProfile = computed(() => 获取手机角色配置(auth.user?.role))
const displayName = computed(() => (
  auth.user
    ? 获取个人资料显示名称(auth.user)
    : '游客'
))
const profileBio = computed(() => (
  auth.user?.bio?.trim()
  || (isAuthenticated.value ? '暂无简介' : '登录后查看你的个人资料与统计')
))
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

function handleOpenLogin() {
  loginGate.open({ redirectPath: '/me' })
}

async function loadProfileStats() {
  if (!auth.isAuthenticated) {
    profileStats.value = {
      articleCount: 0,
      momentCount: 0,
      todoCount: 0,
    }
    return
  }

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

const 共享管理标签页ID列表: AppTabId[] = ['memos', 'todos', 'moments', 'articles', 'materials', 'bills']
const 共享管理标题映射: Record<AppTabId, string> = {
  home: '首页',
  memos: '备忘录',
  todos: '待办',
  moments: '动态',
  articles: '文章管理',
  materials: '资料库',
  bills: '账单管理',
  profile: '我的',
}

const managementEntries = computed(() => {
  return 共享管理标签页ID列表
    .filter((tabId) => !tabBar.visibleTabIds.includes(tabId))
    .map((tabId) => {
      const tab = APP_TAB_DEFINITION_MAP.get(tabId)
      if (!tab) {
        return null
      }

      return {
        title: 共享管理标题映射[tabId],
        to: tab.to,
        icon: tab.icon,
      }
    })
    .filter((item) => item !== null)
})
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

    <RouterLink
      v-if="isAuthenticated"
      class="hero-card hero-card--profile hero-card--link"
      to="/me/account"
    >
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

    <section v-else class="hero-card hero-card--profile hero-card--guest">
      <UniversalAvatar
        class="hero-card__avatar"
        :src="''"
        :text="displayName"
        alt="游客头像"
        :size="52"
      />

      <div class="hero-card__content">
        <div class="hero-card__heading">
          <h1 class="page-title">{{ displayName }}</h1>
          <span class="role-badge" :class="roleBadgeClass">{{ roleProfile.badge }}</span>
        </div>
        <p class="hero-card__meta">{{ profileBio }}</p>
      </div>

      <button class="hero-card__login-button" type="button" @click="handleOpenLogin">
        登录
      </button>
    </section>

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
          <span class="panel-title">三端共享页</span>
        </div>

        <div v-if="managementEntries.length > 0" class="panel-card panel-list">
          <ProfileEntryCard
            v-for="entry in managementEntries"
            :key="entry.to"
            :title="entry.title"
            :to="entry.to"
            :icon="entry.icon"
          />
        </div>

        <div v-else class="profile-section__empty">
          三端共享页都已经在底部栏显示了
        </div>
      </section>

      <section class="profile-section">
        <div class="profile-section__heading">
          <span class="panel-title">本地专用页</span>
        </div>

        <div class="panel-card panel-list">
          <ProfileEntryCard
            title="手机使用"
            to="/me/phone-usage"
            :icon="Iphone"
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

.hero-card--guest {
  grid-template-columns: auto minmax(0, 1fr) auto;
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
.hero-card__login-button,
.profile-topbar__action,
.profile-login-entry__icon,
.profile-login-entry__arrow {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
}

.hero-card__arrow {
  color: var(--text-tertiary);
}

.hero-card__arrow :deep(svg),
.profile-topbar__action :deep(svg),
.profile-login-entry__icon :deep(svg),
.profile-login-entry__arrow :deep(svg) {
  width: 18px;
  height: 18px;
  color: currentColor;
  fill: currentColor;
}

.hero-card__login-button {
  min-width: 64px;
  height: 36px;
  padding: 0 16px;
  border: 1px solid transparent;
  border-radius: 12px;
  background: var(--theme-accent-soft);
  color: var(--theme-accent-strong);
  font-weight: 600;
  cursor: pointer;
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

.profile-section + .profile-section {
  margin-top: 16px;
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

.profile-section__empty {
  padding: 14px 16px;
  border-radius: 18px;
  color: var(--text-tertiary);
  background: var(--theme-panel-soft);
  border: 1px solid var(--theme-card-border);
}

.role-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 44px;
  min-height: 24px;
  padding: 0 10px;
  border-radius: 10px;
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

</style>
