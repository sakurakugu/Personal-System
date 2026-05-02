<script setup lang="ts">
import { computed } from 'vue'
import { useAuthStore } from '@personal-system/domain/auth'
import { useTodoStore } from '@personal-system/domain/todos'
import { getPhoneRoleProfile } from '@/auth/role'

const auth = useAuthStore()
const todoStore = useTodoStore()

const pendingTodoCount = computed(() => todoStore.todos.filter((todo) => todo.status === 'todo').length)
const displayName = computed(() => auth.user?.nickname || auth.user?.username || '你好')
const roleProfile = computed(() => getPhoneRoleProfile(auth.user?.role))
const accountStatus = computed(() => (auth.user?.is_active === false ? '已停用' : '正常'))
const roleBadgeClass = computed(() => `role-badge--${auth.user?.role || 'user'}`)
</script>

<template>
  <section class="page">
    <header class="hero-card hero-card--role">
      <div class="section-heading">
        <p class="eyebrow">首页</p>
        <span class="role-badge" :class="roleBadgeClass">{{ roleProfile.badge }}</span>
      </div>
      <h1 class="page-title">{{ displayName }}</h1>
      <p class="page-subtitle">{{ roleProfile.summary }}</p>
    </header>

    <div class="overview-grid">
      <article class="panel-card stat-card">
        <span class="panel-title">当前身份</span>
        <strong class="panel-value panel-value--compact">{{ roleProfile.label }}</strong>
        <span class="panel-meta">已按角色切换手机端视角</span>
      </article>

      <article class="panel-card stat-card">
        <span class="panel-title">待办</span>
        <strong class="panel-value">{{ pendingTodoCount }}</strong>
        <span class="panel-meta">当前未完成数量</span>
      </article>

      <article class="panel-card stat-card">
        <span class="panel-title">账户状态</span>
        <strong class="panel-value panel-value--compact">{{ accountStatus }}</strong>
        <span class="panel-meta">登录后以当前账号权限生效</span>
      </article>
    </div>

    <section class="panel-card stack">
      <div>
        <span class="panel-title">当前角色能力</span>
        <strong class="section-title">手机端已识别 {{ roleProfile.label }}</strong>
      </div>
      <div class="capability-list">
        <article v-for="item in roleProfile.capabilities" :key="item.title" class="capability-card">
          <strong>{{ item.title }}</strong>
          <p>{{ item.description }}</p>
        </article>
      </div>
      <p v-if="roleProfile.managementNotice" class="panel-meta panel-note">
        {{ roleProfile.managementNotice }}
      </p>
    </section>

    <div class="stack">
      <RouterLink class="panel-card panel-link" to="/todos">
        <span class="panel-title">待办</span>
        <strong class="panel-value">{{ pendingTodoCount }}</strong>
        <span class="panel-meta">当前未完成数量</span>
      </RouterLink>

      <RouterLink class="panel-card panel-link" to="/me">
        <span class="panel-title">账号</span>
        <strong class="panel-value panel-value--compact">{{ roleProfile.label }}</strong>
        <span class="panel-meta">查看个人资料、接口环境与退出登录</span>
      </RouterLink>
    </div>
  </section>
</template>

<style scoped>
.hero-card {
  padding: 20px;
  border: 1px solid rgba(202, 138, 4, 0.12);
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.84);
  backdrop-filter: blur(14px);
  box-shadow: 0 20px 40px rgba(120, 53, 15, 0.08);
}

.hero-card--role {
  display: grid;
  gap: 10px;
}

.page-subtitle {
  margin: 12px 0 0;
  color: #6b7280;
}

.panel-link {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.overview-grid {
  display: grid;
  gap: 14px;
}

.stat-card {
  display: grid;
  gap: 8px;
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
  color: #92400e;
  background: rgba(245, 158, 11, 0.12);
}

.role-badge--admin {
  color: #166534;
  background: rgba(34, 197, 94, 0.14);
}

.role-badge--super_admin {
  color: #991b1b;
  background: rgba(239, 68, 68, 0.14);
}

.panel-title {
  display: block;
  color: #92400e;
  font-size: 0.95rem;
}

.panel-value {
  display: block;
  font-size: 2rem;
  line-height: 1;
}

.panel-value--compact {
  font-size: 1.35rem;
  line-height: 1.3;
}

@media (min-width: 768px) {
  .overview-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}
</style>
