<script setup lang="ts">
import { Monitor, User } from '@element-plus/icons-vue'
import { ElButton, ElCard, ElIcon, ElTag } from 'element-plus'
import { computed } from 'vue'
import { useAuthStore } from '@personal-system/domain/auth'
import { useDesktopRouteTabs } from '../../../shared/composables/useDesktopRouteTabs'

const auth = useAuthStore()
const { openDesktopRoute } = useDesktopRouteTabs()

const displayName = computed(() => auth.user?.nickname || auth.user?.username || '未登录')
const roleLabel = computed(() => {
  if (auth.user?.role === 'super_admin') {
    return '超级管理员'
  }
  if (auth.user?.role === 'admin') {
    return '管理员'
  }
  return '普通用户'
})
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h1>桌面端概览</h1>
      <p>当前骨架已接入设备令牌登录，可继续扩展待办、账单和小工具联动。</p>
    </div>

    <div class="card-grid">
      <ElCard class="overview-card">
        <template #header>
          <div class="card-title">
            <ElIcon><User /></ElIcon>
            <span>当前账户</span>
          </div>
        </template>
        <div class="info-grid">
          <div>
            <strong>{{ displayName }}</strong>
            <p>@{{ auth.user?.username }}</p>
          </div>
          <ElTag type="primary" effect="plain">{{ roleLabel }}</ElTag>
        </div>
      </ElCard>

      <ElCard class="overview-card">
        <template #header>
          <div class="card-title">
            <ElIcon><Monitor /></ElIcon>
            <span>设备会话</span>
          </div>
        </template>
        <p class="card-description">这里可以直接检查当前桌面端是否已经进入原生设备会话体系。</p>
        <ElButton type="primary" @click="openDesktopRoute('/device-sessions')">
          查看登录设备
        </ElButton>
      </ElCard>
    </div>
  </div>
</template>

<style scoped>
.page-container {
  display: grid;
  gap: 20px;
  padding: 28px;
}

.page-header h1 {
  margin: 0 0 8px;
}

.page-header p {
  margin: 0;
  color: var(--desktop-text-muted);
}

.card-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.overview-card {
  border-radius: 20px;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.info-grid {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.info-grid p,
.card-description {
  margin: 8px 0 0;
  color: var(--desktop-text-muted);
}

@media (max-width: 960px) {
  .card-grid {
    grid-template-columns: 1fr;
  }
}
</style>
