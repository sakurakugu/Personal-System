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
