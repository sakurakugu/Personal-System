<script setup lang="ts">
import { computed } from 'vue'
import { 使用认证存储 } from '@personal-system/domain/auth'
import { 获取手机角色配置 } from '@/modules/认证/lib/role'

const auth = 使用认证存储()

const displayName = computed(() => auth.user?.nickname || auth.user?.username || '你好')
const roleProfile = computed(() => 获取手机角色配置(auth.user?.role))
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

.hero-card--role {
  display: grid;
  gap: 10px;
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
